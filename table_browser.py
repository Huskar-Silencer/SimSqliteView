from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QSpinBox, QHeaderView, QAbstractItemView, QComboBox,
    QDialog, QGroupBox, QTextEdit, QLineEdit, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from database import DatabaseManager


class CellValueDetailsDialog(QDialog):
    """Dialog for viewing full cell value details."""

    def __init__(self, field_name: str, row_number: int, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cell Value Details")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # --- Info group ---
        info_group = QGroupBox("Information")
        info_layout = QFormLayout(info_group)

        # Compute value text and stats
        if value is None:
            value_text = "NULL"
            char_count = 0
            byte_count = 0
            type_name = "NULL"
        elif isinstance(value, bytes):
            value_text = value.hex()
            char_count = len(value_text)
            byte_count = len(value)
            type_name = "BLOB"
        else:
            value_text = str(value)
            char_count = len(value_text)
            byte_count = len(value_text.encode("utf-8"))
            type_name = type(value).__name__

        self._field_edit = QLineEdit(field_name)
        self._field_edit.setReadOnly(True)
        info_layout.addRow("Field Name:", self._field_edit)

        self._row_edit = QLineEdit(str(row_number))
        self._row_edit.setReadOnly(True)
        info_layout.addRow("Row Number:", self._row_edit)

        self._type_edit = QLineEdit(type_name)
        self._type_edit.setReadOnly(True)
        info_layout.addRow("Python Type:", self._type_edit)

        self._char_edit = QLineEdit(str(char_count))
        self._char_edit.setReadOnly(True)
        info_layout.addRow("Character Count:", self._char_edit)

        self._byte_edit = QLineEdit(str(byte_count))
        self._byte_edit.setReadOnly(True)
        info_layout.addRow("UTF-8 Bytes:", self._byte_edit)

        layout.addWidget(info_group)

        # --- Value group ---
        value_group = QGroupBox("Value")
        value_layout = QVBoxLayout(value_group)

        self._value_text = QTextEdit()
        self._value_text.setFont(QFont("Consolas", 11))
        self._value_text.setPlainText(value_text)
        value_layout.addWidget(self._value_text)

        layout.addWidget(value_group, 1)

        # --- Close button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class TableBrowser(QWidget):
    """Widget for browsing and viewing table data."""

    status_message = Signal(str)

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self._current_table: str = ""
        self._total_rows: int = 0
        self._page_size: int = 100
        self._current_offset: int = 0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Structure table (column info) ---
        self._structure_label = QLabel("Table Structure")
        self._structure_label.setObjectName("sectionLabel")
        self._structure_label.setStyleSheet("")
        layout.addWidget(self._structure_label)

        self._structure_table = QTableWidget()
        self._structure_table.setColumnCount(6)
        self._structure_table.setHorizontalHeaderLabels(
            ["#", "Name", "Type", "Not Null", "Default", "Primary Key"]
        )
        self._structure_table.horizontalHeader().setStretchLastSection(True)
        self._structure_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._structure_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._structure_table.setAlternatingRowColors(True)
        self._structure_table.setMaximumHeight(180)
        self._structure_table.verticalHeader().setVisible(False)
        layout.addWidget(self._structure_table)

        # --- Data table ---
        self._data_label = QLabel("Table Data")
        self._data_label.setObjectName("sectionLabel")
        self._data_label.setStyleSheet("")
        layout.addWidget(self._data_label)

        self._data_table = QTableWidget()
        self._data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._data_table.setAlternatingRowColors(True)
        self._data_table.verticalHeader().setVisible(False)
        self._data_table.horizontalHeader().setStretchLastSection(True)
        self._data_table.setSortingEnabled(True)
        self._data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._data_table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self._data_table, 1)

        # --- Pagination bar ---
        pager = QHBoxLayout()

        pager.addWidget(QLabel("Page Size:"))
        self._page_size_combo = QComboBox()
        self._page_size_combo.addItems(["50", "100", "250", "500"])
        self._page_size_combo.setCurrentText("100")
        self._page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        pager.addWidget(self._page_size_combo)

        pager.addStretch()

        self._prev_btn = QPushButton("< Previous")
        self._prev_btn.clicked.connect(self._prev_page)
        pager.addWidget(self._prev_btn)

        self._page_label = QLabel("Page 1 / 1")
        self._page_label.setMinimumWidth(120)
        self._page_label.setAlignment(Qt.AlignCenter)
        pager.addWidget(self._page_label)

        self._next_btn = QPushButton("Next >")
        self._next_btn.clicked.connect(self._next_page)
        pager.addWidget(self._next_btn)

        pager.addStretch()

        self._row_count_label = QLabel("Total: 0 rows")
        pager.addWidget(self._row_count_label)

        layout.addLayout(pager)

    def load_table(self, table_name: str):
        """Load and display data and structure for the given table."""
        if not self._db.is_connected:
            return

        self._current_table = table_name
        self._current_offset = 0

        try:
            self._total_rows = self._db.get_row_count(table_name)
        except Exception:
            self._total_rows = 0

        self._load_structure(table_name)
        self._load_data()
        self._update_pagination()

    def _load_structure(self, table_name: str):
        columns = self._db.get_table_info(table_name)
        self._structure_table.setRowCount(len(columns))
        self._structure_label.setText(f"Table Structure — {table_name}")

        for i, col in enumerate(columns):
            self._structure_table.setItem(i, 0, QTableWidgetItem(str(col["cid"])))
            self._structure_table.setItem(i, 1, QTableWidgetItem(col["name"]))
            self._structure_table.setItem(i, 2, QTableWidgetItem(col["type"] or "—"))
            self._structure_table.setItem(i, 3, QTableWidgetItem("Yes" if col["notnull"] else "No"))
            dv = col["default_value"]
            self._structure_table.setItem(i, 4, QTableWidgetItem(str(dv) if dv is not None else "—"))
            self._structure_table.setItem(i, 5, QTableWidgetItem("Yes" if col["pk"] else "No"))

            # Highlight primary key rows
            if col["pk"]:
                for c in range(6):
                    item = self._structure_table.item(i, c)
                    if item:
                        item.setBackground(QColor(255, 255, 200))

        self._structure_table.resizeColumnsToContents()

    def _load_data(self):
        try:
            rows, columns = self._db.get_table_data(
                self._current_table, self._page_size, self._current_offset
            )
        except Exception as e:
            self.status_message.emit(f"Error loading data: {e}")
            return

        self._data_table.setSortingEnabled(False)
        self._data_table.setColumnCount(len(columns))
        self._data_table.setHorizontalHeaderLabels(columns)
        self._data_table.setRowCount(len(rows))
        self._data_label.setText(
            f"Table Data — {self._current_table} "
            f"(showing {self._current_offset + 1}–{self._current_offset + len(rows)} of {self._total_rows})"
        )

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = "" if val is None else str(val)
                item = QTableWidgetItem(text)
                # Store original Python value and column name
                item.setData(Qt.UserRole, val)
                item.setData(Qt.UserRole + 1, columns[c])
                if val is None:
                    item.setForeground(QColor(150, 150, 150))
                    item.setText("NULL")
                    item.setToolTip("NULL")
                else:
                    item.setToolTip(text)
                self._data_table.setItem(r, c, item)

        self._data_table.setSortingEnabled(True)
        self._data_table.resizeColumnsToContents()

    def _update_pagination(self):
        total_pages = max(1, (self._total_rows + self._page_size - 1) // self._page_size)
        current_page = self._current_offset // self._page_size + 1
        self._page_label.setText(f"Page {current_page} / {total_pages}")
        self._row_count_label.setText(f"Total: {self._total_rows} rows")
        self._prev_btn.setEnabled(self._current_offset > 0)
        self._next_btn.setEnabled(self._current_offset + self._page_size < self._total_rows)

    def _prev_page(self):
        self._current_offset = max(0, self._current_offset - self._page_size)
        self._load_data()
        self._update_pagination()

    def _next_page(self):
        self._current_offset += self._page_size
        self._load_data()
        self._update_pagination()

    def _on_page_size_changed(self, text: str):
        self._page_size = int(text)
        self._current_offset = 0
        self._load_data()
        self._update_pagination()

    def clear(self):
        """Clear all displayed data."""
        self._structure_table.setRowCount(0)
        self._data_table.setRowCount(0)
        self._data_table.setColumnCount(0)
        self._structure_label.setText("Table Structure")
        self._data_label.setText("Table Data")
        self._page_label.setText("Page 1 / 1")
        self._row_count_label.setText("Total: 0 rows")
        self._prev_btn.setEnabled(False)
        self._next_btn.setEnabled(False)
        self._current_table = ""
        self._total_rows = 0
        self._current_offset = 0

    def _on_cell_double_clicked(self, row: int, column: int):
        """Show full value details when a cell is double-clicked."""
        item = self._data_table.item(row, column)
        if not item:
            return

        field_name = item.data(Qt.UserRole + 1) or ""
        original_value = item.data(Qt.UserRole)
        actual_row = self._current_offset + row + 1

        dlg = CellValueDetailsDialog(field_name, actual_row, original_value, self)
        dlg.exec()
