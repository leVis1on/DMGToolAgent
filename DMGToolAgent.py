import sqlite3
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
def connect_to_db(db_name):
    return sqlite3.connect(db_name)

def create_table(connection):
    with connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            );
        ''')

def insert_value(connection, value):
    with connection:
        connection.execute('''
            INSERT INTO records (value) VALUES (?);
        ''', (value,))

def delete_value(connection, record_id):
    with connection:
        connection.execute('''
            DELETE FROM records WHERE id = ?;
        ''', (record_id,))

def get_all_values(connection):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM records;')
    return cursor.fetchall()
class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Database App")

        self.conn = connect_to_db('example.db')
        create_table(self.conn)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Создание таблицы
        self.tree = ttk.Treeview(self.root, columns=('ID', 'Value'), show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Value', text='Value')
        self.tree.pack(side=TOP, fill=BOTH, expand=True)

        # Кнопки
        frame = Frame(self.root)
        frame.pack(side=BOTTOM, fill=X)

        self.entry_value = Entry(frame)
        self.entry_value.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)

        add_button = Button(frame, text="Add", command=self.add_record)
        add_button.pack(side=LEFT, padx=5, pady=5)

        delete_button = Button(frame, text="Delete", command=self.delete_record)
        delete_button.pack(side=LEFT, padx=5, pady=5)

        self.tree.bind('<Double-1>', self.edit_record)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        records = get_all_values(self.conn)
        for record in records:
            self.tree.insert('', END, values=record)

    def add_record(self):
        value = self.entry_value.get()
        if value:
            insert_value(self.conn, value)
            self.entry_value.delete(0, END)
            self.load_data()
        else:
            messagebox.showwarning("Input Error", "Please enter a value")

    def delete_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            record_id = self.tree.item(selected_item)['values'][0]
            delete_value(self.conn, record_id)
            self.load_data()
        else:
            messagebox.showwarning("Selection Error", "Please select a record to delete")

    def edit_record(self, event):
        selected_item = self.tree.selection()[0]
        old_value = self.tree.item(selected_item)['values'][1]
        new_value = self.entry_value.get()
        if new_value:
            self.conn.execute('''
                UPDATE records SET value = ? WHERE id = ?;
            ''', (new_value, self.tree.item(selected_item)['values'][0]))
            self.conn.commit()
            self.load_data()
            self.entry_value.delete(0, END)
        else:
            self.entry_value.insert(0, old_value)

def main():
    root = Tk()
    app = DatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
