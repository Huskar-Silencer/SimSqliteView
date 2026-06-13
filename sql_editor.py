from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QSplitter, QAbstractItemView,
    QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence

from database import DatabaseManager
from table_browser import CellValueDetailsDialog


class SqlEditor(QWidget):
    """Widget for writing and executing SQL queries."""

    status_message = Signal(str)

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Vertical)

        # --- SQL input area ---
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)

        input_header = QHBoxLayout()
        input_header.addWidget(QLabel("SQL Query"))
        input_header.addStretch()

        self._run_btn = QPushButton("Execute (Ctrl+Enter)")
        self._run_btn.setObjectName("primaryBtn")
        self._run_btn.setStyleSheet("")
        self._run_btn.clicked.connect(self._execute_sql)
        input_header.addWidget(self._run_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear)
        input_header.addWidget(self._clear_btn)

        input_layout.addLayout(input_header)

        self._sql_input = QTextEdit()
        self._sql_input.setFont(QFont("Consolas", 11))
        self._sql_input.setPlaceholderText("Enter SQL query here...\n\nExample:\n  SELECT * FROM table_name;\n  SELECT name, type FROM sqlite_master;")
        self._sql_input.setMinimumHeight(100)
        self._sql_input.setMaximumHeight(300)
        input_layout.addWidget(self._sql_input)

        splitter.addWidget(input_widget)

        # --- Results area ---
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)

        self._result_label = QLabel("Results")
        self._result_label.setObjectName("sectionLabel")
        self._result_label.setStyleSheet("")
        result_layout.addWidget(self._result_label)

        self._result_table = QTableWidget()
        self._result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._result_table.setAlternatingRowColors(True)
        self._result_table.verticalHeader().setVisible(False)
        self._result_table.horizontalHeader().setStretchLastSection(True)
        self._result_table.cellDoubleClicked.connect(self._on_result_cell_double_clicked)
        result_layout.addWidget(self._result_table, 1)

        self._info_label = QLabel("")
        self._info_label.setObjectName("infoLabel")
        self._info_label.setStyleSheet("")
        result_layout.addWidget(self._info_label)

        splitter.addWidget(result_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        # Ctrl+Enter shortcut to execute
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._execute_sql)

    def _execute_sql(self):
        sql = self._sql_input.toPlainText().strip()
        if not sql:
            self.status_message.emit("No SQL to execute.")
            return
        if not self._db.is_connected:
            self.status_message.emit("No database connected.")
            return

        try:
            # Check if it's a multi-statement script
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            if len(statements) > 1:
                rows, columns, rowcount = self._db.execute_script(sql)
            else:
                rows, columns = self._db.execute_query(sql)
                rowcount = len(rows)

            self._display_results(rows, columns, rowcount)
            self.status_message.emit(f"Query executed successfully. {rowcount} row(s) returned.")

        except Exception as e:
            self._result_table.setRowCount(0)
            self._result_table.setColumnCount(0)
            self._result_label.setText("Results — Error")
            self._info_label.setText(f"Error: {e}")
            self._info_label.setStyleSheet("")
            self._info_label.setObjectName("errorLabel")
            self.status_message.emit(f"SQL Error: {e}")

    def _display_results(self, rows: list, columns: list[str], rowcount: int):
        self._result_table.setRowCount(len(rows))
        self._result_table.setColumnCount(len(columns))
        self._result_table.setHorizontalHeaderLabels(columns)
        self._result_label.setText(f"Results — {len(rows)} row(s)")

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = "" if val is None else str(val)
                item = QTableWidgetItem(text)
                # Store original value and column name
                item.setData(Qt.UserRole, val)
                item.setData(Qt.UserRole + 1, columns[c])
                item.setToolTip(text)
                if val is None:
                    item.setForeground(QColor(150, 150, 150))
                    item.setText("NULL")
                elif isinstance(val, bytes):
                    item.setText(f"<BLOB: {len(val)} bytes>")
                self._result_table.setItem(r, c, item)

        self._result_table.resizeColumnsToContents()
        self._info_label.setText(f"Returned {len(rows)} row(s), {len(columns)} column(s)")
        self._info_label.setObjectName("infoLabel")
        self._info_label.setStyleSheet("")

    def _clear(self):
        self._sql_input.clear()
        self._result_table.setRowCount(0)
        self._result_table.setColumnCount(0)
        self._result_label.setText("Results")
        self._info_label.setText("")

    def set_db(self, db_manager: DatabaseManager):
        self._db = db_manager

    def clear_editor(self):
        """Clear the editor content."""
        self._sql_input.clear()
        self._result_table.setRowCount(0)
        self._result_table.setColumnCount(0)
        self._result_label.setText("Results")
        self._info_label.setText("")

    def set_placeholder(self, text: str):
        """Set the placeholder text in the SQL input area."""
        self._sql_input.setPlaceholderText(text)

    def _on_result_cell_double_clicked(self, row: int, column: int):
        """Show full value details when a result cell is double-clicked."""
        item = self._result_table.item(row, column)
        if not item:
            return

        field_name = item.data(Qt.UserRole + 1) or ""
        original_value = item.data(Qt.UserRole)

        dlg = CellValueDetailsDialog(field_name, row + 1, original_value, self)
        dlg.exec()
