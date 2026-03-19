import sqlite3

def setup_database():
    print("Initializing local SQLite database...")
    
    # This will create a file named 'company_data.db' in our folder
    conn = sqlite3.connect('company_data.db')
    cursor = conn.cursor()

    # Create a table for Employee Leave Balances
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_balances (
            employee_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            leave_days_remaining INTEGER NOT NULL
        )
    ''')

    # Clear out any old data if we run this script multiple times
    cursor.execute('DELETE FROM employee_balances')

    # Insert some dummy data
    dummy_data =[
        (101, 'Alice Smith', 'Engineering', 15),
        (102, 'Bob Jones', 'Marketing', 5),
        (103, 'Charlie Brown', 'HR', 22),
        (104, 'Diana Prince', 'Engineering', 30)
    ]

    cursor.executemany('''
        INSERT INTO employee_balances (employee_id, name, department, leave_days_remaining)
        VALUES (?, ?, ?, ?)
    ''', dummy_data)

    # Save (commit) the changes and close the connection
    conn.commit()
    conn.close()
    
    print("Database setup complete! 'company_data.db' has been created and populated.")

if __name__ == "__main__":
    setup_database()