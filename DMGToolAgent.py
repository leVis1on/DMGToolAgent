import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, 
    QPushButton, QLineEdit, QLabel, QComboBox, QFormLayout, 
    QHeaderView, QFileDialog, QMessageBox, QDialog, QHBoxLayout,
    QAbstractItemView, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QVariant
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
import sqlite3

class NumericSortProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_data = left.data(Qt.DisplayRole)
        right_data = right.data(Qt.DisplayRole)
        
        # Пытаемся преобразовать в числа
        try:
            left_num = float(left_data)
            right_num = float(right_data)
            return left_num < right_num
        except (ValueError, TypeError):
            # Если не получается, сортируем как строки
            return left_data < right_data

class DatabaseSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор базы данных")
        self.setFixedSize(400, 200)
        self.setWindowIcon(QIcon('icon.png'))
        
        layout = QVBoxLayout()
        
        label = QLabel("Выберите действие:")
        label.setStyleSheet("font-size: 14px;")
        layout.addWidget(label)
        
        self.btn_open = QPushButton("Открыть существующую базу")
        self.btn_open.setFixedHeight(40)
        self.btn_open.clicked.connect(self.open_existing_db)
        layout.addWidget(self.btn_open)
        
        self.btn_create = QPushButton("Создать новую базу")
        self.btn_create.setFixedHeight(40)
        self.btn_create.clicked.connect(self.create_new_db)
        layout.addWidget(self.btn_create)
        
        self.setLayout(layout)
    
    def open_existing_db(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл базы данных", 
            "", "SQLite Database (*.db);;All files (*)"
        )
        if filepath:
            self.db_file = filepath
            self.accept()
    
    def create_new_db(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Создать новую базу данных", 
            "", "SQLite Database (*.db);;All files (*)"
        )
        if filepath:
            if not filepath.endswith('.db'):
                filepath += '.db'
            
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY,
                    T INTEGER, Name TEXT, L REAL, R REAL, Type TEXT, Description TEXT, 
                    LCut REAL, Cuts INTEGER, ROffset REAL, LOffset REAL, PType INTEGER
                );
            ''')
            conn.commit()
            conn.close()
            
            self.db_file = filepath
            self.accept()

class EditDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать запись")
        self.setFixedSize(300, 450)
        self.setWindowIcon(QIcon('icon.png'))
        
        self.fields = ['T', 'Name', 'L', 'R', 'Type', 'Description', 
                      'LCut', 'Cuts', 'ROffset', 'LOffset', 'PType']
        self.entries = {}
        
        layout = QFormLayout()
        
        for idx, field in enumerate(self.fields):
            label = QLabel(field)
            entry = QLineEdit()
            entry.setText(str(data[idx+1] if idx+1 < len(data) else ''))
            self.entries[field] = entry
            layout.addRow(label, entry)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)
    
    def get_data(self):
        return [self.entries[field].text() for field in self.fields]

class DatabaseApp(QMainWindow):
    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file
        self.setWindowTitle(f"DMG Tool Agent - {os.path.basename(db_file)}")
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowIcon(QIcon('icon.png'))
        
        self.conn = sqlite3.connect(db_file)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(self.edit_record)
        
        self.model = QStandardItemModel()
        self.proxy_model = NumericSortProxyModel()  # Используем нашу модель для сортировки
        self.proxy_model.setSourceModel(self.model)
        self.table.setModel(self.proxy_model)
        
        headers = ['ID', 'T', 'Name', 'L', 'R', 'Type', 'Description', 
                   'LCut', 'Cuts', 'ROffset', 'LOffset', 'PType']
        self.model.setHorizontalHeaderLabels(headers)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.search_record)
        control_layout.addWidget(self.search_input)
        
        self.btn_add = QPushButton("Добавить")
        self.btn_add.clicked.connect(self.add_record)
        control_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("Редактировать")
        self.btn_edit.clicked.connect(self.edit_record)
        control_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.clicked.connect(self.delete_record)
        control_layout.addWidget(self.btn_delete)
        
        control_panel.setLayout(control_layout)
        
        layout.addWidget(self.table)
        layout.addWidget(control_panel)
        central_widget.setLayout(layout)
    
    def load_data(self):
        self.model.removeRows(0, self.model.rowCount())
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tools;')
        records = cursor.fetchall()
        
        for record in records:
            row = []
            for col, item in enumerate(record):
                cell = QStandardItem()
                # Устанавливаем правильный тип данных для числовых столбцов
                if col in [0, 1, 8, 11]:  # Целочисленные столбцы (ID, T, Cuts, PType)
                    cell.setData(int(item) if item is not None else 0, Qt.DisplayRole)
                elif col in [3, 4, 7, 9, 10]:  # Вещественные столбцы (L, R, LCut, ROffset, LOffset)
                    cell.setData(float(item) if item is not None else 0.0, Qt.DisplayRole)
                else:  # Текстовые столбцы
                    cell.setData(str(item) if item is not None else '', Qt.DisplayRole)
                row.append(cell)
            self.model.appendRow(row)
    
    def add_record(self):
        dialog = EditDialog(['']*12, self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO tools (T, Name, L, R, Type, Description, LCut, Cuts, ROffset, LOffset, PType) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            ''', values)
            self.conn.commit()
            self.load_data()
    
    def edit_record(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        
        index = self.proxy_model.mapToSource(selected[0])
        row = index.row()
        record_id = int(self.model.item(row, 0).data(Qt.DisplayRole))
        
        data = []
        for col in range(self.model.columnCount()):
            data.append(self.model.item(row, col).data(Qt.DisplayRole))
        
        dialog = EditDialog(data, self)
        if dialog.exec_() == QDialog.Accepted:
            new_values = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE tools SET T=?, Name=?, L=?, R=?, Type=?, Description=?, 
                LCut=?, Cuts=?, ROffset=?, LOffset=?, PType=? WHERE id=?;
            ''', new_values + [record_id])
            self.conn.commit()
            self.load_data()
    
    def delete_record(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        
        index = self.proxy_model.mapToSource(selected[0])
        row = index.row()
        record_id = int(self.model.item(row, 0).data(Qt.DisplayRole))
        
        reply = QMessageBox.question(
            self, 'Подтверждение', 
            'Вы уверены, что хотите удалить эту запись?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM tools WHERE id=?;', (record_id,))
            self.conn.commit()
            self.load_data()
    
    def search_record(self, text):
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterFixedString(text)
    
    def closeEvent(self, event):
        self.conn.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    selector = DatabaseSelector()
    if selector.exec_() == QDialog.Accepted:
        main_window = DatabaseApp(selector.db_file)
        main_window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()