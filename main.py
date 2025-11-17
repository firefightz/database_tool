import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import getpass
from dateutil import parser

# Load environment variables from .env
load_dotenv()

TABLES = {
    "bundle": ["group_name", "group_address", "active", "created", "deactivated"],
    "book": ["name", "update_frequency"]
}

UPDATE_FREQUENCY_OPTIONS = ["daily", "weekly", "monthly", "yearly"]

def parse_date_input(date_str):
    """Convert user input into a date string compatible with Postgres (YYYY-MM-DD)."""
    if not date_str.strip():
        return None
    try:
        dt = parser.parse(date_str)
        return dt.date().isoformat()
    except (ValueError, OverflowError):
        print("Invalid date format. Please try again.")
        return None

def get_connection():
    """Prompt for password and return a DB connection."""
    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT", 5432))
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    
    password = getpass.getpass("Enter DB password: ")
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    return conn

def select_table():
    """Prompt user to select a table until a valid choice is made."""
    table_list = list(TABLES.keys())
    while True:
        print("\nSelect table:")
        for i, table in enumerate(table_list, start=1):
            print(f"{i}. {table}")
        choice = input("Enter number: ")
        try:
            return table_list[int(choice)-1]
        except (ValueError, IndexError):
            print("Invalid choice.")

def crud_menu():
    """Display CRUD menu and return choice."""
    print("\nChoose action:")
    print("1. Create")
    print("2. Read/Lookup")
    print("3. Update")
    print("4. Delete")
    print("5. Exit")
    return input("Enter number: ")

def confirm_action(prompt):
    return input(f"{prompt} (y/n): ").lower() == "y"

def get_key_values(table):
    """Prompt for key fields. For bundle, require both group_name and group_address."""
    key_fields = {
        "bundle": ["group_name", "group_address"],
        "book": ["name"]
    }
    values = {}
    for key in key_fields[table]:
        while True:
            val = input(f"{key}: ")
            if val:
                values[key] = val
                break
            print(f"{key} is required.")
    return values

def create_record(conn, table):
    fields = TABLES[table]
    data = {}
    for f in fields:
        if table == "book" and f == "update_frequency":
            while True:
                val = input(f"{f} ({'/'.join(UPDATE_FREQUENCY_OPTIONS)}): ").lower()
                if val in UPDATE_FREQUENCY_OPTIONS:
                    data[f] = val
                    break
                print("Invalid option.")
        elif table == "bundle" and f in ["created", "deactivated"]:
            while True:
                val = input(f"{f} (leave blank if none): ")
                parsed = parse_date_input(val)
                if parsed is not None or val.strip() == "":
                    data[f] = parsed
                    break
        else:
            data[f] = input(f"{f}: ")
    if confirm_action("Create this record?"):
        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join(fields)
        values = tuple(data[f] for f in fields)
        query = sql.SQL(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
        with conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()
        print("Record created.")

def read_records(conn, table):
    key_values = get_key_values(table)
    filters = [f"{k} = %s" for k in key_values.keys()]
    values = tuple(key_values.values())
    query = f"SELECT * FROM {table} WHERE " + " AND ".join(filters)
    with conn.cursor() as cur:
        cur.execute(query, values)
        rows = cur.fetchall()
        if rows:
            for r in rows:
                print(dict(zip(TABLES[table], r)))
        else:
            print("No records found.")

def update_record(conn, table):
    key_values = get_key_values(table)
    fields = TABLES[table]
    update_fields = {}
    print("Enter new values (leave blank to skip):")
    for f in fields:
        if f not in key_values:
            val = input(f"{f}: ")
            if val:
                if table == "book" and f == "update_frequency":
                    if val.lower() not in UPDATE_FREQUENCY_OPTIONS:
                        print(f"Skipping invalid {f} value.")
                        continue
                    update_fields[f] = val.lower()
                elif table == "bundle" and f in ["created", "deactivated"]:
                    parsed = parse_date_input(val)
                    if parsed:
                        update_fields[f] = parsed
                else:
                    update_fields[f] = val
    if not update_fields:
        print("No fields to update.")
        return
    if confirm_action("Update this record?"):
        set_clause = ", ".join(f"{k} = %s" for k in update_fields.keys())
        filters = " AND ".join(f"{k} = %s" for k in key_values.keys())
        query = f"UPDATE {table} SET {set_clause} WHERE {filters}"
        with conn.cursor() as cur:
            cur.execute(query, tuple(update_fields.values()) + tuple(key_values.values()))
            conn.commit()
        print("Record updated.")

def delete_record(conn, table):
    key_values = get_key_values(table)
    if confirm_action("Delete this record?"):
        filters = " AND ".join(f"{k} = %s" for k in key_values.keys())
        query = f"DELETE FROM {table} WHERE {filters}"
        with conn.cursor() as cur:
            cur.execute(query, tuple(key_values.values()))
            conn.commit()
        print("Record deleted.")

def main():
    conn = None
    try:
        conn = get_connection()
        while True:
            table = select_table()
            action = crud_menu()
            if action == "1":
                create_record(conn, table)
            elif action == "2":
                read_records(conn, table)
            elif action == "3":
                update_record(conn, table)
            elif action == "4":
                delete_record(conn, table)
            elif action == "5":
                print("Exiting...")
                break
            else:
                print("Invalid choice.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
