# Text-to-SQL Engine

A web application that converts simple English questions into SQL queries and runs them against a sample employee database.

## Why it matters

Business users often know the question they want answered but not the SQL needed to retrieve it. This project demonstrates a rule-based bridge between plain language and structured data.

## What it supports

- Employee and department queries
- Greater-than, less-than, between, and equality filters
- Sorting, grouping, and simple nested queries
- Fuzzy matching for small spelling mistakes
- Displaying both generated SQL and returned rows

## Technology

Python, Flask, SQLite, regular expressions, HTML, CSS, and JavaScript.

## Run

```bash
python create_db.py
python app.py
```

This is a learning prototype and should only execute approved read-only queries in a production environment.
