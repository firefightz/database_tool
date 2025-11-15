# file: cli_crud_app_rich_full_bundle.py

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from thefuzz import fuzz

load_dotenv()  # Load DB credentials from .env file

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

console = Console()

def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def display_row(row, columns):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Column")
    table.add_column("Value")
    for col, val in zip(columns, row):
        table.add_row(str(col), str(val))
    console.print(table)

def select_row_by_key(cursor, table, key_column, key_term):
    cursor.execute(f"SELECT * FROM {table} WHERE {key_column} ILIKE %s", (f"%{key_term}%",))
    results = cursor.fetchall()
    if not results:
        console.print("[red]No matching records found.[/red]")
        return None
    console.print(f"[bold green]{len(results)} results found:[/bold green]")
    for idx, row in enumerate(results, 1):
        console.print(f"\n[cyan]Result {idx}:[/cyan]")
        display_row(row, [desc[0] for desc in cursor.description])
    selection = Prompt.ask("Select which record to use (enter number)", choices=[str(i+1) for i in range(len(results))])
    return results[int(selection)-1]

# ----------------- CRUD FUNCTIONS -----------------

def add_bundle(cursor):
    bundle_name = Prompt.ask("Enter bundle name")
    bundle_type = Prompt.ask("Enter bundle type")
    created = datetime.now()
    cursor.execute("""
        INSERT INTO bundle(bundle_name, type, created, active)
        VALUES (%s, %s, %s, %s) RETURNING *
    """, (bundle_name, bundle_type, created, True))
    row = cursor.fetchone()
    console.print("[bold green]Bundle added:[/bold green]")
    display_row(row, [desc[0] for desc in cursor.description])

def add_thing(cursor):
    thing_url = Prompt.ask("Enter thing URL")
    cursor.execute("""
        INSERT INTO things(thing_url)
        VALUES (%s) RETURNING *
    """, (thing_url,))
    row = cursor.fetchone()
    console.print("[bold green]Thing added:[/bold green]")
    display_row(row, [desc[0] for desc in cursor.description])

def update_bundle(cursor):
    key_term = Prompt.ask("Enter key term to search for a bundle")
    row = select_row_by_key(cursor, "bundle", "bundle_name", key_term)
    if not row:
        return
    columns = [desc[0] for desc in cursor.description]
    console.print("[bold cyan]Current bundle info:[/bold cyan]")
    display_row(row, columns)

    updates = {}
    if Confirm.ask("Do you want to update the active status?"):
        current = row[columns.index("active")]
        console.print(f"Current active status: [yellow]{current}[/yellow]")
        new_active = Confirm.ask("Set active to True?")
        updates["active"] = new_active

    if Confirm.ask("Do you want to remove deactivated date?"):
        updates["deactivated"] = None

    if updates:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [row[columns.index("bundle_name")]]
        cursor.execute(f"UPDATE bundle SET {set_clause} WHERE bundle_name = %s RETURNING *", values)
        updated_row = cursor.fetchone()
        console.print("[bold green]Bundle updated:[/bold green]")
        display_row(updated_row, columns)

def update_thing(cursor):
    key_term = Prompt.ask("Enter key term to search for a thing")
    row = select_row_by_key(cursor, "things", "thing_url", key_term)
    if not row:
        return
    columns = [desc[0] for desc in cursor.description]
    console.print("[bold cyan]Current thing info:[/bold cyan]")
    display_row(row, columns)

    if Confirm.ask("Do you want to update the thing URL?"):
        new_url = Prompt.ask("Enter new URL")
        cursor.execute("UPDATE things SET thing_url = %s WHERE thing_url = %s RETURNING *", (new_url, row[columns.index("thing_url")]))
        updated_row = cursor.fetchone()
        console.print("[bold green]Thing updated:[/bold green]")
        display_row(updated_row, columns)

def delete_bundle(cursor):
    key_term = Prompt.ask("Enter key term to search for a bundle to delete")
    row = select_row_by_key(cursor, "bundle", "bundle_name", key_term)
    if not row:
        return
    columns = [desc[0] for desc in cursor.description]
    console.print("[bold red]Selected bundle for deletion:[/bold red]")
    display_row(row, columns)
    if Confirm.ask("Are you sure you want to delete this bundle?"):
        cursor.execute("DELETE FROM bundle WHERE bundle_name = %s", (row[columns.index("bundle_name")],))
        console.print("[bold green]Bundle deleted.[/bold green]")

def delete_thing(cursor):
    key_term = Prompt.ask("Enter key term to search for a thing to delete")
    row = select_row_by_key(cursor, "things", "thing_url", key_term)
    if not row:
        return
    columns = [desc[0] for desc in cursor.description]
    console.print("[bold red]Selected thing for deletion:[/bold red]")
    display_row(row, columns)
    if Confirm.ask("Are you sure you want to delete this thing?"):
        cursor.execute("DELETE FROM things WHERE thing_url = %s", (row[columns.index("thing_url")],))
        console.print("[bold green]Thing deleted.[/bold green]")

# ----------------- FUZZY + PAGINATED LOOKUP -----------------

def lookup_paginated(cursor, table, key_column):
    key_term = Prompt.ask(f"Enter search term for {table}")
    
    # Fetch all rows
    cursor.execute(f"SELECT * FROM {table}")
    all_rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    # Fuzzy matching
    results = []
    for row in all_rows:
        score = fuzz.partial_ratio(key_term.lower(), str(row[columns.index(key_column)]).lower())
        if score >= 60:  # threshold
            results.append((score, row))
    
    if not results:
        console.print("[red]No matching records found.[/red]")
        return
    
    results.sort(reverse=True, key=lambda x: x[0])
    rows_only = [row for score, row in results]
    
    # Pagination
    page_size = 5
    total_pages = (len(rows_only) + page_size - 1) // page_size
    current_page = 0
    
    while True:
        console.print(f"\n[bold green]Page {current_page+1} of {total_pages}[/bold green]")
        start = current_page * page_size
        end = start + page_size
        for idx, row in enumerate(rows_only[start:end], start=1):
            console.print(f"\n[cyan]Result {start + idx}:[/cyan]")
            display_row(row, columns)
            console.print("-"*40)
        
        if total_pages == 1:
            break
        
        console.print("[bold yellow]n[/bold yellow]=next, [bold yellow]p[/bold yellow]=previous, [bold yellow]q[/bold yellow]=quit")
        action = Prompt.ask("Choose action", choices=["n", "p", "q"])
        if action == "n" and current_page < total_pages - 1:
            current_page += 1
        elif action == "p" and current_page > 0:
            current_page -= 1
        elif action == "q":
            break

def lookup(cursor):
    table_choice = Prompt.ask("Lookup in table", choices=["bundle", "things"])
    table = table_choice
    key_column = "bundle_name" if table == "bundle" else "thing_url"
    lookup_paginated(cursor, table, key_column)

# ----------------- MAIN MENU -----------------

def main():
    with connect() as conn:
        with conn.cursor() as cursor:
            while True:
                console.print("\n[bold blue]Main Menu[/bold blue]")
                choice = Prompt.ask("Select an option", choices=[
                    "Add Bundle", "Add Thing",
                    "Update Bundle", "Update Thing",
                    "Delete Bundle", "Delete Thing",
                    "Lookup", "Exit"
                ])
                if choice == "Add Bundle":
                    add_bundle(cursor)
                elif choice == "Add Thing":
                    add_thing(cursor)
                elif choice == "Update Bundle":
                    update_bundle(cursor)
                elif choice == "Update Thing":
                    update_thing(cursor)
                elif choice == "Delete Bundle":
                    delete_bundle(cursor)
                elif choice == "Delete Thing":
                    delete_thing(cursor)
                elif choice == "Lookup":
                    lookup(cursor)
                elif choice == "Exit":
                    console.print("[bold magenta]Exiting...[/bold magenta]")
                    break
                conn.commit()

if __name__ == "__main__":
    main()
