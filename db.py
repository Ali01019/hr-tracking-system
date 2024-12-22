import pg8000
import pg8000.legacy
def connect_db():
    conn = pg8000.connect(
        host='localhost',
        database="hr_tracking_system",
        password="_Ali252_",    
        user="postgres",
        port=5432
    )
    cur = conn.cursor()
    return cur,conn
def create_tables():
    cur, conn = connect_db()

    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS office (
        id serial PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        latitude int NOT NULL,
        longtitutde int NOT NULL
    );
    CREATE TABLE IF NOT EXISTS employee (
        id serial PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        role VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        office_id int NOT NULL,
        CONSTRAINT office_id FOREIGN KEY (office_id) REFERENCES office(id)
    );
    CREATE TABLE IF NOT EXISTS check_in_out (
        id serial PRIMARY KEY,
        check_in_date TIMESTAMP,
        check_out_date TIMESTAMP,
        office_check_in_id int,
        office_check_out_id int,
        employee_id int NOT NULL,
        CONSTRAINT fk_office_check_in FOREIGN KEY (office_check_in_id) REFERENCES office(id) ON DELETE SET NULL,
        CONSTRAINT fk_office_check_out FOREIGN KEY (office_check_out_id) REFERENCES office(id) ON DELETE SET NULL,
        CONSTRAINT fk_employee FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE
    );
    """)
    conn.commit()

    # Check if the office table is empty before inserting
    cur.execute("SELECT COUNT(*) FROM office;")
    office_count = cur.fetchone()[0]
    if office_count == 0:
        cur.execute("""
        INSERT INTO office (name, latitude, longtitutde)
        VALUES
            ('Main Office', 40, 70),
            ('New Office', 90, 100);
        """)
        conn.commit()

    # Check if the employee table is empty before inserting
    cur.execute("SELECT COUNT(*) FROM employee;")
    employee_count = cur.fetchone()[0]
    if employee_count == 0:
        cur.execute("""
        INSERT INTO employee (name, role, email, office_id)
        VALUES
            ('Ali Elghoul', 'admin', 'ali.elghoul@example.com', 1);
        """)
        conn.commit()

    close_connection(cur, conn)


def query (query:str):
    cur,conn = connect_db()
    cur.execute(query)
    conn.commit()
    close_connection(cur,conn)

def close_connection(cur:pg8000.legacy.Cursor, conn: pg8000.legacy.Connection):
    cur.close()
    conn.close()

def get_employee_by_id(employee_id):
    cur, conn = connect_db()
    cur.execute("SELECT * FROM employee WHERE id = %s", (employee_id,))
    employee = cur.fetchone()
    close_connection(cur, conn)
    if employee:
        return {
            "id": employee[0],
            "name": employee[1],
            "role": employee[2],
            "email": employee[3],
            "office_id": employee[4]
        }
    return None

def create_employee(name, role, email, office_id):
    cur, conn = connect_db()
    cur.execute("""
        INSERT INTO employee (name, role, email, office_id)
        VALUES (%s, %s, %s, %s)
    """, (name, role, email, office_id))
    conn.commit()
    close_connection(cur, conn)
def check_in(employee_id, office_id,check_in_date):
    cur, conn = connect_db()
    cur.execute("""
        INSERT INTO check_in_out (employee_id, office_id,check_in_date)
        VALUES (%s, %s,%s)
    """, (employee_id, office_id,check_in_date))
    conn.commit()
    close_connection(cur, conn)

def check_out(employee_id):
    cur, conn = connect_db()

    # Update the check-out date to the current timestamp
    cur.execute("""
        UPDATE check_in_out 
        SET check_out_date = CURRENT_TIMESTAMP
        WHERE employee_id = %s AND check_out_date IS NULL
    """, (employee_id,))
    conn.commit()
    close_connection(cur, conn)

def get_attendance(employee_id):
    cur, conn = connect_db()
    cur.execute("""
        SELECT * FROM check_in_out 
        WHERE employee_id = %s
    """, (employee_id,))
    attendance = cur.fetchall()
    close_connection(cur, conn)
    attendance_data = []
    for record in attendance:
        attendance_data.append({
            "check_in_id": record[0],
            "employee_id": record[1],
            "office_id": record[2],
            "check_in_date": record[3],
            "check_out_date": record[4]
        })
    return attendance_data


# create_tables()
# insert_query = """
# INSERT INTO office (name,latitude,longtitutde) VALUES
#  ('Main Office',40,70),
#  ('New Office',90,100);
# """
# insert_values(insert_query)
