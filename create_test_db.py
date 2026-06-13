import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "test_database.db")

# Remove old file if exists
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# --- Tables ---

cursor.execute("""
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT,
    budget REAL DEFAULT 0.0
)
""")

cursor.execute("""
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    department_id INTEGER,
    hire_date TEXT,
    salary REAL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
""")

cursor.execute("""
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT DEFAULT 'active'
)
""")

cursor.execute("""
CREATE TABLE project_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    role TEXT,
    assigned_date TEXT DEFAULT (date('now')),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
""")

# --- Indexes ---

cursor.execute("CREATE INDEX idx_employees_dept ON employees(department_id)")
cursor.execute("CREATE INDEX idx_employees_email ON employees(email)")
cursor.execute("CREATE INDEX idx_assignments_employee ON project_assignments(employee_id)")

# --- Views ---

cursor.execute("""
CREATE VIEW employee_details AS
SELECT e.id, e.first_name, e.last_name, e.email,
       d.name AS department, e.hire_date, e.salary, e.is_active
FROM employees e
LEFT JOIN departments d ON e.department_id = d.id
""")

# --- Insert data ---

departments = [
    ("Engineering", "Building A", 500000.00),
    ("Marketing", "Building B", 200000.00),
    ("Finance", "Building C", 150000.00),
    ("Human Resources", "Building A", 120000.00),
    ("Sales", "Building B", 300000.00),
]
cursor.executemany("INSERT INTO departments (name, location, budget) VALUES (?, ?, ?)", departments)

employees = [
    ("Alice", "Johnson", "alice.johnson@company.com", 1, "2020-03-15", 95000.00, 1),
    ("Bob", "Smith", "bob.smith@company.com", 1, "2019-07-22", 105000.00, 1),
    ("Carol", "Williams", "carol.williams@company.com", 2, "2021-01-10", 72000.00, 1),
    ("David", "Brown", "david.brown@company.com", 3, "2018-11-05", 88000.00, 1),
    ("Eve", "Davis", "eve.davis@company.com", 1, "2022-06-01", 92000.00, 1),
    ("Frank", "Miller", "frank.miller@company.com", 4, "2020-09-18", 68000.00, 1),
    ("Grace", "Wilson", "grace.wilson@company.com", 5, "2021-04-25", 75000.00, 1),
    ("Henry", "Moore", "henry.moore@company.com", 2, "2019-02-14", 70000.00, 0),
    ("Ivy", "Taylor", "ivy.taylor@company.com", 3, "2023-01-09", 82000.00, 1),
    ("Jack", "Anderson", "jack.anderson@company.com", 5, "2022-08-30", 78000.00, 1),
    ("Karen", "Thomas", "karen.thomas@company.com", 1, "2017-05-20", 115000.00, 1),
    ("Leo", "Jackson", "leo.jackson@company.com", 4, "2021-11-12", 65000.00, 1),
    ("Mia", "White", "mia.white@company.com", 2, "2023-03-01", 71000.00, 1),
    ("Nathan", "Harris", "nathan.harris@company.com", 1, "2020-10-07", 98000.00, 1),
    ("Olivia", "Martin", "olivia.martin@company.com", 5, "2019-12-15", 80000.00, 0),
]
cursor.executemany(
    "INSERT INTO employees (first_name, last_name, email, department_id, hire_date, salary, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
    employees,
)

projects = [
    ("Website Redesign", "Complete overhaul of company website", "2024-01-15", "2024-06-30", "completed"),
    ("Mobile App", "Develop iOS and Android app", "2024-03-01", None, "active"),
    ("Data Migration", "Migrate legacy data to new system", "2024-06-01", "2024-09-15", "completed"),
    ("AI Chatbot", "Build customer support chatbot", "2024-08-01", None, "active"),
    ("Security Audit", "Full security review of all systems", "2025-01-10", "2025-03-31", "planning"),
]
cursor.executemany(
    "INSERT INTO projects (name, description, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
    projects,
)

assignments = [
    (1, 1, "Lead Developer", "2024-01-15"),
    (2, 1, "Backend Developer", "2024-01-20"),
    (5, 2, "Full Stack Developer", "2024-03-01"),
    (11, 2, "Tech Lead", "2024-03-01"),
    (14, 2, "Backend Developer", "2024-03-15"),
    (3, 1, "UI/UX Designer", "2024-02-01"),
    (4, 3, "Project Manager", "2024-06-01"),
    (9, 3, "Data Analyst", "2024-06-15"),
    (1, 4, "Lead Developer", "2024-08-01"),
    (7, 4, "Marketing Lead", "2024-08-15"),
    (10, 4, "Sales Advisor", "2024-09-01"),
    (6, 5, "HR Coordinator", "2025-01-10"),
    (12, 5, "Compliance Officer", "2025-01-15"),
]
cursor.executemany(
    "INSERT INTO project_assignments (employee_id, project_id, role, assigned_date) VALUES (?, ?, ?, ?)",
    assignments,
)

# --- Trigger ---

cursor.execute("""
CREATE TRIGGER update_project_status
AFTER UPDATE OF end_date ON projects
WHEN NEW.end_date IS NOT NULL AND OLD.end_date IS NULL
BEGIN
    UPDATE projects SET status = 'completed' WHERE id = NEW.id;
END
""")

conn.commit()
conn.close()

print(f"Test database created: {DB_PATH}")
print(f"  Tables: departments, employees, projects, project_assignments")
print(f"  Views: employee_details")
print(f"  Indexes: idx_employees_dept, idx_employees_email, idx_assignments_employee")
print(f"  Triggers: update_project_status")
print(f"  Data: 5 departments, 15 employees, 5 projects, 13 assignments")
