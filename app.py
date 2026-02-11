from flask import Flask, render_template, request, jsonify
import sqlite3
import re
import difflib

app = Flask(__name__)

# ---------------------------
# SCHEMA CONFIG
# ---------------------------

TABLES = {
    "employee": "Employees",
    "employees": "Employees",
    "department": "Departments",
    "departments": "Departments"
}

COLUMNS = {
    "id": "id",
    "name": "name",
    "salary": "salary",
    "department": "department_id",
    "department_id": "department_id"
}

# ---------------------------
# HELPERS
# ---------------------------

def preprocess(text):
    return text.lower().strip()

def fuzzy_match(word, possibilities, cutoff=0.7):
    match = difflib.get_close_matches(word, possibilities, n=1, cutoff=cutoff)
    return match[0] if match else None

def detect_table(text):
    words = text.split()
    detected = []
    for word in words:
        match = fuzzy_match(word, TABLES.keys())
        if match:
            detected.append(TABLES[match])
    return list(set(detected))

def detect_column(word):
    match = fuzzy_match(word, COLUMNS.keys())
    if match:
        return COLUMNS[match]
    return None

# ---------------------------
# SQL GENERATOR
# ---------------------------

def generate_sql(text):
    text = preprocess(text)
    tables = detect_table(text)

    if not tables:
        return None

    sql = f"SELECT * FROM {tables[0]}"
    and_conditions = []
    or_conditions = []

    # ---------------------------
    # BETWEEN
    # ---------------------------
    for match in re.finditer(r'(\w+) between (\d+) and (\d+)', text):
        column = detect_column(match.group(1))
        if column:
            and_conditions.append(f"{column} BETWEEN {match.group(2)} AND {match.group(3)}")

    # ---------------------------
    # GREATER / LESS
    # ---------------------------
    for match in re.finditer(r'(\w+)?\s*greater than (\d+)', text):
        column = detect_column(match.group(1) or "salary") or "salary"
        and_conditions.append(f"{column} > {match.group(2)}")

    for match in re.finditer(r'(\w+)?\s*less than (\d+)', text):
        column = detect_column(match.group(1) or "salary") or "salary"
        and_conditions.append(f"{column} < {match.group(2)}")

    # ---------------------------
    # STRING EQUAL
    # ---------------------------
    for match in re.finditer(r'(\w+) equal to (\w+)', text):
        column = detect_column(match.group(1))
        if column:
            and_conditions.append(f"{column} = '{match.group(2)}'")

    # ---------------------------
    # LIKE SUPPORT
    # ---------------------------
    for match in re.finditer(r'(\w+) like (\w+)', text):
        column = detect_column(match.group(1))
        if column:
            and_conditions.append(f"{column} LIKE '%{match.group(2)}%'")

    # ---------------------------
    # DIRECT EQUAL (column value)
    # ---------------------------
    for match in re.finditer(r'(\w+)\s+(\d+)', text):
        column = detect_column(match.group(1))
        if column:
            and_conditions.append(f"{column} = {match.group(2)}")

    # ---------------------------
    # OR SUPPORT
    # ---------------------------
    if " or " in text:
        parts = text.split(" or ")
        for part in parts:
            match = re.search(r'(\w+)\s+(\d+)', part)
            if match:
                column = detect_column(match.group(1))
                if column:
                    or_conditions.append(f"{column} = {match.group(2)}")

    # ---------------------------
    # APPLY WHERE
    # ---------------------------
    where_clause = ""

    if and_conditions:
        where_clause += " AND ".join(and_conditions)

    if or_conditions:
        if where_clause:
            where_clause = f"({where_clause}) OR " + " OR ".join(or_conditions)
        else:
            where_clause = " OR ".join(or_conditions)

    if where_clause:
        sql += " WHERE " + where_clause

    # ---------------------------
    # GROUP BY
    # ---------------------------
    if "per" in text:
        for word in text.split():
            column = detect_column(word)
            if column:
                sql = f"SELECT {column}, COUNT(*) FROM {tables[0]} GROUP BY {column}"
                break

    # ---------------------------
    # NESTED QUERY (Simple Example)
    # ---------------------------
    if "in department" in text:
        match = re.search(r'in department (\d+)', text)
        if match:
            sql = f"""SELECT * FROM Employees 
                      WHERE department_id IN 
                      (SELECT id FROM Departments WHERE id = {match.group(1)})"""

    # ---------------------------
    # ORDER BY
    # ---------------------------
    if "sort by" in text or "order by" in text:
        for word in text.split():
            column = detect_column(word)
            if column:
                sql += f" ORDER BY {column}"
                break

    if "highest" in text:
        sql += " ORDER BY salary DESC LIMIT 1"

    if "lowest" in text:
        sql += " ORDER BY salary ASC LIMIT 1"

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

if __name__ == "__main__":
    app.run(debug=True)
