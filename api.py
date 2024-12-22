from flask import Flask, request, jsonify
import datetime
import db
from db import *
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, create_access_token

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "pass"
jwt = JWTManager(app)
@app.route('/login', methods=['POST'])
def login():
    auth_data = request.get_json()

    email = auth_data.get('email')
    role = auth_data.get('role')

    # Check if email and role exist in the database
    cur, conn = db.connect_db()
    cur.execute("SELECT * FROM employee WHERE email = %s AND role = %s", (email, role))
    user = cur.fetchone()

    db.close_connection(cur, conn)

    if user:
        # Create a JWT token without an expiration time
        token = create_access_token(identity={"email": email, "role": role})
        return jsonify({"token": token})

    return jsonify({"message": "Invalid credentials"}), 401
@app.route("/")
def home ():
    return "Home"

@app.route("/employee/<employee_id>")
def get_employee(employee_id):
    employee_data = db.get_employee_by_id(employee_id)
    if employee_data:
        return jsonify(employee_data), 200
    return jsonify({"message": "Employee not found"}), 404
@app.route("/add-employee", methods=['POST'])
def create_employee():
    try:
        # Parse JSON payload
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Invalid JSON payload"}), 400

        # Connect to the database
        cur, conn = db.connect_db()

        # Check if data is for a single employee or multiple
        if isinstance(data, list):  # Multiple employees
            for employee in data:
                name = employee.get('name')
                role = employee.get('role')
                email = employee.get('email')
                office_id = employee.get('office_id')

                if not (name and role and email and isinstance(office_id, int)):
                    db.close_connection(cur, conn)
                    return jsonify({"msg": "Invalid or missing fields in one of the employees"}), 400

                cur.execute(
                    "INSERT INTO employee (name, role, email, office_id) VALUES (%s, %s, %s, %s)",
                    (name, role, email, office_id)
                )
        else:  # Single employee
            name = data.get('name')
            role = data.get('role')
            email = data.get('email')
            office_id = data.get('office_id')

            if not (name and role and email and isinstance(office_id, int)):
                db.close_connection(cur, conn)
                return jsonify({"msg": "Invalid or missing fields"}), 400

            cur.execute(
                "INSERT INTO employee (name, role, email, office_id) VALUES (%s, %s, %s, %s)",
                (name, role, email, office_id)
            )

        # Commit changes
        conn.commit()
        db.close_connection(cur, conn)

        return jsonify({"msg": "Employee(s) added successfully"}), 201
    except Exception as e:
        return jsonify({"msg": f"Server error: {str(e)}"}), 500

@app.route("/checkin", methods=['POST'])
def checkin():
    # Parse the JSON payload
    checkin_data = request.get_json()

    # If the input is a list, iterate over the list; if it's a single entry, wrap it in a list
    if isinstance(checkin_data, dict):
        checkin_data = [checkin_data]

    # Ensure each item has employee_id and office_check_in_id
    for item in checkin_data:
        employee_id = item.get("employee_id")
        office_check_in_id = item.get("office_check_in_id")
        check_in_date = item.get("check_in_date")
        if not employee_id or not office_check_in_id:
            return jsonify({"message": "Employee ID and Office Check-In ID are required"}), 400

        try:
            # Open database connection
            cur, conn = db.connect_db()

            # Insert check-in record
            cur.execute(
                """
                INSERT INTO check_in_out (employee_id, office_check_in_id,check_in_date) 
                VALUES (%s, %s,%s)
                """, 
                (employee_id, office_check_in_id,check_in_date)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()  # Roll back in case of an error
            db.close_connection(cur, conn)
            return jsonify({"message": "Error during check-in", "error": str(e)}), 500
        finally:
            db.close_connection(cur, conn)

    return jsonify({"message": "Check-in(s) successful"}), 201
        
@app.route("/checkout", methods=['POST'])
def checkout():
    checkout_data = request.get_json()

    # If the input is a list, iterate over the list; if it's a single entry, wrap it in a list
    if isinstance(checkout_data, dict):
        checkout_data = [checkout_data]

    for item in checkout_data:
        employee_id = item.get("employee_id")
        office_check_out_id = item.get("office_check_out_id")
        check_out_date = item.get("check_out_date")  # Get the check-out date from the request

        if not employee_id or not office_check_out_id or not check_out_date:
            return jsonify({"message": "Employee ID, Office Check-Out ID, and Check-Out Date are required"}), 400

        try:
            # Open database connection
            cur, conn = db.connect_db()

            # Find the latest check-in for the employee where check-out is not set
            cur.execute("""
                SELECT id 
                FROM check_in_out 
                WHERE employee_id = %s AND check_out_date IS NULL
                ORDER BY check_in_date DESC 
                LIMIT 1
            """, (employee_id,))
            check_in_out_record = cur.fetchone()

            if not check_in_out_record:
                db.close_connection(cur, conn)
                return jsonify({"message": f"No active check-in record found for employee {employee_id}"}), 404

            check_in_out_id = check_in_out_record[0]

            # Use the check_out_date passed in the request
            cur.execute("""
                UPDATE check_in_out
                SET check_out_date = %s, office_check_out_id = %s
                WHERE id = %s
            """, (check_out_date, office_check_out_id, check_in_out_id))
            conn.commit()
        except Exception as e:
            conn.rollback()  # Roll back in case of an error
            db.close_connection(cur, conn)
            return jsonify({"message": "Error during check-out", "error": str(e)}), 500
        finally:
            db.close_connection(cur, conn)

    return jsonify({"message": "Check-out(s) successful"}), 200

@app.route("/attendance", methods=["GET"])
def attendance():
    employee_id = request.args.get("employee_id")  # Get employee_id from query parameters
    
    if not employee_id:
        return jsonify({"message": "Employee ID is required"}), 400

    attendance_data = get_attendance(employee_id)
    return jsonify(attendance_data), 200

@app.route("/update-employee-role/<int:employee_id>", methods=['PUT'])
def update_employee_role(employee_id):
    try:
        # Parse the JSON payload
        data = request.get_json()

        # Extract and validate the new role
        new_role = data.get('role')
        if not new_role:
            return jsonify({"message": "Role is required"}), 400

        # Open database connection
        cur, conn = db.connect_db()

        # Check if the employee exists in the database
        cur.execute("SELECT * FROM employee WHERE id = %s", (employee_id,))
        employee = cur.fetchone()
        
        if not employee:
            db.close_connection(cur, conn)
            return jsonify({"message": "Employee not found"}), 404

        # Update the employee's role
        cur.execute("""
            UPDATE employee 
            SET role = %s 
            WHERE id = %s
        """, (new_role, employee_id))
        conn.commit()

        # Close the database connection
        db.close_connection(cur, conn)

        return jsonify({"message": f"Employee role updated to {new_role} successfully"}), 200

    except Exception as e:
        return jsonify({"message": f"Error during update: {str(e)}"}), 500

@app.route("/get-data", methods=['GET'])
def get_data():
    # Get the table name from the query parameters
    table_name = request.args.get('table')
    
    if not table_name:
        return jsonify({"message": "Table parameter is required"}), 400
    
    # Validate that the table name is one of the allowed tables
    if table_name not in ['employee', 'office', 'check_in_out']:
        return jsonify({"message": "Invalid table name"}), 400
    
    try:
        # Open database connection
        cur, conn = db.connect_db()

        # Dynamically fetch data based on the table name
        cur.execute(f"SELECT * FROM {table_name}")
        data = cur.fetchall()

        # If no data found, return a 404 message
        if not data:
            db.close_connection(cur, conn)
            return jsonify({"message": f"No data found in {table_name} table"}), 404
        
        # Prepare the column names for JSON response
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in data]

        # Close database connection
        db.close_connection(cur, conn)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"message": f"Error during fetching data: {str(e)}"}), 500

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)