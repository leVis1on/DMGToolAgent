import sqlite3
from tkinter import *
from tkinter import ttk
from tkinter import messagebox

# Database functions
def connect_to_db(db_name):
    return sqlite3.connect(db_name)

def create_table(connection):
    with connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY,
                T TEXT, Name TEXT, L REAL, R REAL, Type TEXT, Description TEXT, 
                LCut REAL, Cuts INTEGER, ROffset REAL, LOffset REAL, PType TEXT
            );
        ''')

def insert_value(connection, values):
    with connection:
        connection.execute('''
            INSERT INTO tools (T, Name, L, R, Type, Description, LCut, Cuts, ROffset, LOffset, PType) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', values)

def delete_value(connection, record_id):
    with connection:
        connection.execute('''
            DELETE FROM tools WHERE id = ?;
        ''', (record_id,))

def update_value(connection, values):
    with connection:
        connection.execute('''
            UPDATE tools SET T=?, Name=?, L=?, R=?, Type=?, Description=?, 
            LCut=?, Cuts=?, ROffset=?, LOffset=?, PType=? WHERE id=?;
        ''', values)

def get_all_values(connection):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM tools;')
    return cursor.fetchall()

# GUI class
class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DMG Tool Agent")

        # Set window icon
        self.root.iconphoto(False, PhotoImage(file='icon.png'))

        self.conn = connect_to_db('tools.db')
        create_table(self.conn)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Create frame for treeview and scrollbars
        frame = Frame(self.root)
        frame.pack(side=TOP, fill=BOTH, expand=True)

        # Create treeview
        columns = ('ID', 'T', 'Name', 'L', 'R', 'Type', 'Description', 
                   'LCut', 'Cuts', 'ROffset', 'LOffset', 'PType')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, False))
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

        # Add scrollbars
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        hsb.place(relwidth=1, anchor="sw", x=0, rely=1)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vsb.place(relheight=1, anchor="ne", y=0, relx=1)
        self.tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        
        # Buttons
        controls = Frame(self.root)
        controls.pack(side=BOTTOM, fill=X)

        self.entry_value = Entry(controls)
        self.entry_value.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)

        add_button = Button(controls, text="Добавить", command=self.add_record)
        add_button.pack(side=LEFT, padx=5, pady=5)

        delete_button = Button(controls, text="Удалить", command=self.delete_record)
        delete_button.pack(side=LEFT, padx=5, pady=5)

        search_button = Button(controls, text="Поиск", command=self.search_record)
        search_button.pack(side=LEFT, padx=5, pady=5)

        self.tree.bind('<Double-1>', self.edit_record)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        records = get_all_values(self.conn)
        for record in records:
            self.tree.insert('', END, values=record)

    def add_record(self):
        values = self.entry_value.get().split(',')
        if len(values) <= 11:
            values = values + [''] * (11 - len(values))
            insert_value(self.conn, values)
            self.entry_value.delete(0, END)
            self.load_data()
        else:
            messagebox.showwarning("Ошибка ввода", "Введите не более 11 значений, разделенных запятыми")

    def delete_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            record_id = self.tree.item(selected_item)['values'][0]
            delete_value(self.conn, record_id)
            self.load_data()
        else:
            messagebox.showwarning("Ошибка выбора", "Выберите строку для удаления")

    def edit_record(self, event):
        selected_item = self.tree.selection()[0]
        values = self.tree.item(selected_item)['values']
        self.entry_value.delete(0, END)
        self.entry_value.insert(0, ','.join(map(str, values[1:])))
        
        top = Toplevel(self.root)
        top.title("Редактировать запись")

        # Set window icon
        top.iconphoto(False, PhotoImage(file='icon.png'))
        
        # Centering the window
        self.root.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        width = 220
        height = 390
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        top.geometry(f"{width}x{height}+{x}+{y}")

        fields = ['T', 'Name', 'L', 'R', 'Type', 'Description', 'LCut', 'Cuts', 'ROffset', 'LOffset', 'PType']
        entries = {}

        for idx, field in enumerate(fields):
            Label(top, text=field).grid(row=idx, column=0, padx=5, pady=5, sticky=W)
            entry = Entry(top)
            entry.grid(row=idx, column=1, padx=5, pady=5, sticky=EW)
            entry.insert(0, str(values[idx + 1]))
            entries[field] = entry

        def save_and_update():
            new_values = [entry.get() for entry in entries.values()]
            if len(new_values) <= 11:
                new_values = new_values + [''] * (11 - len(new_values))
                update_value(self.conn, new_values + [values[0]])
                self.load_data()
                # Find and select the updated record by ID
                for child in self.tree.get_children():
                    if self.tree.item(child)['values'][0] == values[0]:
                        self.tree.selection_set(child)
                        self.tree.see(child)
                        break
                top.destroy()
            else:
                messagebox.showwarning("Ошибка ввода", "Введите не более 11 значений, разделенных запятыми")

        Button(top, text="Сохранить", command=save_and_update).grid(row=len(fields), columnspan=2, pady=10)

    def search_record(self):
        search_value = self.entry_value.get()
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            if search_value in map(str, values):
                self.tree.selection_set(child)
                self.tree.see(child)
                break

    def sort_by_column(self, col, descending):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Convert data to appropriate type (number or string) for sorting
        try:
            data = [(float(val), child) if val.replace('.', '', 1).isdigit() else (val, child) for val, child in data]
        except ValueError:
            data = [(val, child) for val, child in data]

        data.sort(reverse=descending)
        
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        for column in self.tree["columns"]:
            if column == col:
                if descending:
                    self.tree.heading(column, text=f"{col} ↑")
                else:
                    self.tree.heading(column, text=f"{col} ↓")
            else:
                self.tree.heading(column, text=column)
        
        self.tree.heading(col, command=lambda _col=col: self.sort_by_column(_col, not descending))

def main():
    root = Tk()
    
    # Centering and resizing the window
    root.update_idletasks()
    width = root.winfo_screenwidth() // 2
    height = root.winfo_screenheight() // 2
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    app = DatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
