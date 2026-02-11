import sqlite3
import random

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Drop table if exists (so it resets every time)
cursor.execute("DROP TABLE IF EXISTS Employees")

# Create Employees table
cursor.execute("""
CREATE TABLE Employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    salary INTEGER,
    department_id INTEGER
)
""")

# Sample names list
names = [
    "Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace",
    "Hannah", "Ishaan", "Jack", "Kiran", "Liam", "Maya", "Nikhil",
    "Olivia", "Priya", "Rahul", "Sophia", "Tanvi", "Vikram"
]

employees = []

for i in range(1, 101):  # 100 rows
    name = random.choice(names) + str(i)
    salary = random.randint(25000, 120000)
    department_id = random.randint(1, 5)
    employees.append((i, name, salary, department_id))

cursor.executemany(
    "INSERT INTO Employees (id, name, salary, department_id) VALUES (?, ?, ?, ?)",
    employees
)

conn.commit()
conn.close()

print("Database created successfully with 100 employees!")
