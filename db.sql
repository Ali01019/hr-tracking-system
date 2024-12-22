CREATE TABLE office (
id serial PRIMARY KEY,
name VARCHAR(100) NOT NULL,
latitude int NOT NULL,
longtitutde int NOT NULL
);
CREATE TABLE employee(
id serial PRIMARY KEY,
name VARCHAR(100) NOT NULL,
role VARCHAR(100) NOT NULL,
email VARCHAR(100) UNIQUE not null,
office_id int NOT NULL,
CONSTRAINT office_id FOREIGN KEY (office_id) REFERENCES office(id)
);
CREATE TABLE check_in_out (
id serial PRIMARY KEY,
--check_in_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
check_in_date TIMESTAMP,
check_out_date TIMESTAMP,
office_id int NOT NULL,
employee_id int NOT NULL,
CONSTRAINT fk_office FOREIGN KEY (office_id) REFERENCES office(id),
CONSTRAINT fk_employee FOREIGN KEY (employee_id) REFERENCES employee(id)
);
DROP TABLE check_in_out;
DROP TABLE employee;
DROP TABLE office;
SELECT * FROM office;
SELECT * FROM employee;
SELECT * FROM check_in_out;