import os
import json
import psycopg2
from psycopg2 import sql

# DB credentials from environment variables
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

# Whitelist tables and columns to avoid injection
TABLES = {
    "bundle": ["group_name", "group_address", "active", "created", "deactivated"],
    "book": ["name", "update_frequency"]
}

# Unique keys for tables
UNIQUE_KEYS = {
    "bundle": ["group_name", "group_address"],
    "book": ["name"]
}


def build_insert_query(table, values):
    columns = values.keys()
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(', ').join(map(sql.Identifier, columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )
    return query, tuple(values.values())


def build_update_query(table, values, filters):
    set_clause = sql.SQL(', ').join(
        sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()]) for k in values.keys()
    )
    where_clause = sql.SQL(' AND ').join(
        sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()]) for k in filters.keys()
    )
    query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
        sql.Identifier(table),
        set_clause,
        where_clause
    )
    return query, tuple(values.values()) + tuple(filters.values())


def build_delete_query(table, filters):
    where_clause = sql.SQL(' AND ').join(
        sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()]) for k in filters.keys()
    )
    query = sql.SQL("DELETE FROM {} WHERE {}").format(
        sql.Identifier(table),
        where_clause
    )
    return query, tuple(filters.values())


def build_select_query(table, filters):
    if filters:
        where_clause = sql.SQL(' AND ').join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder()]) for k in filters.keys()
        )
        query = sql.SQL("SELECT * FROM {} WHERE {}").format(
            sql.Identifier(table),
            where_clause
        )
        params = tuple(filters.values())
    else:
        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
        params = ()
    return query, params


def build_lookup_query(table, term, column=None):
    if column and column not in TABLES[table]:
        raise ValueError(f"Column {column} not allowed in table {table}.")
    if not column:
        column = TABLES[table][0]
    query = sql.SQL("SELECT * FROM {} WHERE {} ILIKE %s").format(
        sql.Identifier(table),
        sql.Identifier(column)
    )
    return query, (f"%{term}%",)


def validate_unique_key(table, filters):
    """Ensure unique key columns are present in filters."""
    required_keys = UNIQUE_KEYS.get(table, [])
    missing_keys = [k for k in required_keys if k not in filters]
    if missing_keys:
        raise ValueError(f"Missing required unique key(s) for {table}: {missing_keys}")


def lambda_handler(event, context):
    """
    Expects JSON payload like:
    {
        "action": "SELECT"|"INSERT"|"UPDATE"|"DELETE"|"LOOKUP",
        "table": "bundle"|"book",
        "filters": {...},
        "values": {...},
        "term": "search term",
        "column": "column_name"
    }
    """

    action = event.get("action", "").upper()
    table = event.get("table")

    if table not in TABLES:
        return {"statusCode": 400, "body": json.dumps(f"Table {table} not allowed.")}

    filters = event.get("filters", {})
    values = event.get("values", {})
    term = event.get("term", "")
    column = event.get("column")

    # Validate columns for all actions
    if action in ["INSERT", "UPDATE", "DELETE", "SELECT", "LOOKUP"]:
        for col in list(filters.keys()) + list(values.keys()):
            if col not in TABLES[table]:
                return {"statusCode": 400, "body": json.dumps(f"Column {col} not allowed in table {table}.")}

    # Enforce unique key for UPDATE, DELETE, LOOKUP
    if action in ["UPDATE", "DELETE", "LOOKUP"]:
        try:
            validate_unique_key(table, filters)
        except ValueError as e:
            return {"statusCode": 400, "body": json.dumps(str(e))}

    conn = None
    cur = None

    try:
        if action == "INSERT":
            query, params = build_insert_query(table, values)
        elif action == "UPDATE":
            query, params = build_update_query(table, values, filters)
        elif action == "DELETE":
            query, params = build_delete_query(table, filters)
        elif action == "SELECT":
            query, params = build_select_query(table, filters)
        elif action == "LOOKUP":
            query, params = build_lookup_query(table, term, column)
        else:
            return {"statusCode": 400, "body": json.dumps("Invalid action.")}

        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()

        cur.execute(query, params)

        if action in ["SELECT", "LOOKUP"]:
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            result = {"rowcount": cur.rowcount}

        return {"statusCode": 200, "body": json.dumps({"action": action, "result": result})}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(str(e))}

    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass
