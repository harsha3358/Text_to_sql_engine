from flask import Flask, render_template, request, jsonify
import sqlite3
import re
import difflib

app = Flask(__name__)

# ---------------------------
# CONFIGURATION (Schema Maps)
# ---------------------------

TABLES = {
    "employee": "Employees",
    "employees": "Employees",
    "department": "Departments",
    "departments": "Departments"
}

COLUMNS = {
    "name": "name",
    "salary": "salary",
    "id": "id",
    "department": "department_id"
}

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def preprocess(text):
    return text.lower().strip()

def fuzzy_match(word, possibilities, cutoff=0.7):
    match = difflib.get_close_matches(word, possibilities, n=1, cutoff=cutoff)
    return match[0] if match else None

def detect_table(text):
    words = text.split()
    for word in words:
        match = fuzzy_match(word, TABLES.keys())
        if match:
            return TABLES[match]
    return None

def detect_column(text):
    words = text.split()
    for word in words:
        match = fuzzy_match(word, COLUMNS.keys())
        if match:
            return COLUMNS[match]
    return None

# ---------------------------
# SQL GENERATOR
# ---------------------------

def generate_sql(text):
    text = preprocess(text)
    table = detect_table(text)

    if not table:
        return None

    # COUNT support
    if "count" in text:
        sql = f"SELECT COUNT(*) FROM {table}"
    else:
        sql = f"SELECT * FROM {table}"

    where_added = False

    # GREATER THAN
    if "greater than" in text:
        match = re.search(r'greater than (\d+)', text)
        column = detect_column(text)
        if match and column:
            value = match.group(1)
            sql += f" WHERE {column} > {value}"
            where_added = True

    # LESS THAN
    elif "less than" in text:
        match = re.search(r'less than (\d+)', text)
        column = detect_column(text)
        if match and column:
            value = match.group(1)
            sql += f" WHERE {column} < {value}"
            where_added = True

    # EQUAL TO
    elif "equal to" in text:
        match = re.search(r'equal to (\d+)', text)
        column = detect_column(text)
        if match and column:
            value = match.group(1)
            sql += f" WHERE {column} = {value}"
            where_added = True

    # ORDER BY
    if "sort by" in text or "order by" in text:
        column = detect_column(text)
        if column:
            sql += f" ORDER BY {column}"

    # HIGHEST / LOWEST
    if "highest" in text:
        column = detect_column(text)
        if column:
            sql += f" ORDER BY {column} DESC LIMIT 1"

    if "lowest" in text:
        column = detect_column(text)
        if column:
            sql += f" ORDER BY {column} ASC LIMIT 1"

    sql += ";"
    return sql

# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    user_input = request.json.get("query")

    sql = generate_sql(user_input)

    if not sql:
        return jsonify({"error": "Could not understand query."})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return jsonify({
            "sql": sql,
            "columns": columns,
            "rows": rows
        })

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        conn.close()

# ---------------------------
# RUN APP
# ---------------------------

if __name__ == "__main__":
    app.run(debug=False)
