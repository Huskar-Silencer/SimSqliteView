from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QTextEdit,
    QHeaderView, QAbstractItemView, QSplitter, QMessageBox, QGroupBox,
    QFormLayout, QListWidget, QListWidgetItem, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


# SQLite common types
SQLITE_TYPES = [
    "INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC",
    "BOOLEAN", "DATE", "DATETIME", "VARCHAR", "FLOAT",
]


class _SingleTableEditor:
    """Helper that holds widgets for editing one table's definition."""

    def __init__(self):
        self.name: str = ""
        self.columns: list[dict] = []


class CreateTableDialog(QDialog):
    """Dialog for defining table structure when creating a new database."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Database Schema")
        self.resize(900, 650)
        self._tables: list[_SingleTableEditor] = []
        self._init_ui()
        self._add_new_table()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # ── Left: table list ──
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Tables"))
        self._table_list = QListWidget()
        self._table_list.currentRowChanged.connect(self._on_table_selected)
        left_layout.addWidget(self._table_list, 1)

        list_btn_layout = QHBoxLayout()
        self._add_table_btn = QPushButton("+ Add Table")
        self._add_table_btn.clicked.connect(self._add_new_table)
        list_btn_layout.addWidget(self._add_table_btn)

        self._remove_table_btn = QPushButton("- Remove")
        self._remove_table_btn.clicked.connect(self._remove_current_table)
        list_btn_layout.addWidget(self._remove_table_btn)
        left_layout.addLayout(list_btn_layout)

        splitter.addWidget(left_widget)

        # ── Right: table editor ──
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Table name
        name_group = QGroupBox("Table Name")
        name_form = QFormLayout(name_group)
        self._table_name_edit = QLineEdit()
        self._table_name_edit.setPlaceholderText("e.g. users, orders, products...")
        self._table_name_edit.textChanged.connect(self._on_name_changed)
        name_form.addRow("Name:", self._table_name_edit)
        right_layout.addWidget(name_group)

        # Columns editor
        col_group = QGroupBox("Columns")
        col_layout = QVBoxLayout(col_group)

        self._col_table = QTableWidget(0, 6)
        self._col_table.setHorizontalHeaderLabels(
            ["Column Name", "Type", "NOT NULL", "PK", "Auto Inc", "Default"]
        )
        self._col_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._col_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self._col_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self._col_table.setColumnWidth(1, 120)
        self._col_table.setColumnWidth(2, 70)
        self._col_table.setColumnWidth(3, 50)
        self._col_table.setColumnWidth(4, 70)
        self._col_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._col_table.verticalHeader().setVisible(False)
        self._col_table.cellChanged.connect(self._on_columns_changed)
        col_layout.addWidget(self._col_table, 1)

        col_btn_layout = QHBoxLayout()
        self._add_col_btn = QPushButton("+ Add Column")
        self._add_col_btn.clicked.connect(self._add_column)
        col_btn_layout.addWidget(self._add_col_btn)

        self._remove_col_btn = QPushButton("- Remove Column")
        self._remove_col_btn.clicked.connect(self._remove_column)
        col_btn_layout.addWidget(self._remove_col_btn)

        col_btn_layout.addStretch()
        col_layout.addLayout(col_btn_layout)
        right_layout.addWidget(col_group, 1)

        # SQL Preview
        sql_group = QGroupBox("SQL Preview")
        sql_layout = QVBoxLayout(sql_group)
        self._sql_preview = QTextEdit()
        self._sql_preview.setReadOnly(True)
        self._sql_preview.setFont(QFont("Consolas", 11))
        self._sql_preview.setMaximumHeight(180)
        sql_layout.addWidget(self._sql_preview)
        right_layout.addWidget(sql_group)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 700])

        main_layout.addWidget(splitter, 1)

        # ── Bottom buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("Create")
        ok_btn.setObjectName("primaryBtn")
        ok_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Skip")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)

    # ── Table management ──

    def _save_current_table(self):
        """Save the current editor state into self._tables."""
        idx = self._table_list.currentRow()
        if idx < 0 or idx >= len(self._tables):
            return
        editor = self._tables[idx]
        editor.name = self._table_name_edit.text().strip()
        editor.columns = self._read_columns_from_table()

    def _load_table(self, idx: int):
        """Load a table definition into the editor."""
        if idx < 0 or idx >= len(self._tables):
            return
        editor = self._tables[idx]
        self._block_signals(True)
        self._table_name_edit.setText(editor.name)
        self._populate_columns(editor.columns)
        self._block_signals(False)
        self._update_sql_preview()

    def _add_new_table(self):
        self._save_current_table()
        editor = _SingleTableEditor()
        editor.name = f"table_{len(self._tables) + 1}"
        editor.columns = [
            {"name": "id", "type": "INTEGER", "notnull": True, "pk": True, "autoinc": True, "default": ""},
        ]
        self._tables.append(editor)
        self._table_list.addItem(QListWidgetItem(editor.name))
        self._table_list.setCurrentRow(len(self._tables) - 1)

    def _remove_current_table(self):
        idx = self._table_list.currentRow()
        if idx < 0 or len(self._tables) <= 1:
            return
        self._tables.pop(idx)
        self._table_list.takeItem(idx)
        if self._table_list.count() > 0:
            self._table_list.setCurrentRow(min(idx, self._table_list.count() - 1))

    def _on_table_selected(self, row: int):
        self._save_current_table()
        if row >= 0:
            self._load_table(row)
        self._update_remove_table_btn()

    def _update_remove_table_btn(self):
        self._remove_table_btn.setEnabled(len(self._tables) > 1)

    # ── Column management ──

    def _read_columns_from_table(self) -> list[dict]:
        columns = []
        for r in range(self._col_table.rowCount()):
            name_item = self._col_table.item(r, 0)
            name = name_item.text().strip() if name_item else ""
            if not name:
                continue

            type_combo = self._col_table.cellWidget(r, 1)
            col_type = type_combo.currentText() if type_combo else "TEXT"

            notnull_cb = self._col_table.cellWidget(r, 2)
            pk_cb = self._col_table.cellWidget(r, 3)
            autoinc_cb = self._col_table.cellWidget(r, 4)

            default_item = self._col_table.item(r, 5)
            default_val = default_item.text().strip() if default_item else ""

            columns.append({
                "name": name,
                "type": col_type,
                "notnull": notnull_cb.isChecked() if notnull_cb else False,
                "pk": pk_cb.isChecked() if pk_cb else False,
                "autoinc": autoinc_cb.isChecked() if autoinc_cb else False,
                "default": default_val,
            })
        return columns

    def _populate_columns(self, columns: list[dict]):
        self._col_table.setRowCount(len(columns))
        for r, col in enumerate(columns):
            self._set_column_row(r, col)

    def _set_column_row(self, row: int, col: dict):
        # Name
        name_item = QTableWidgetItem(col.get("name", ""))
        self._col_table.setItem(row, 0, name_item)

        # Type combo
        type_combo = QComboBox()
        type_combo.addItems(SQLITE_TYPES)
        current_type = col.get("type", "TEXT")
        if current_type in SQLITE_TYPES:
            type_combo.setCurrentText(current_type)
        else:
            type_combo.addItem(current_type)
            type_combo.setCurrentText(current_type)
        type_combo.setEditable(True)
        type_combo.currentTextChanged.connect(lambda _: self._update_sql_preview())
        self._col_table.setCellWidget(row, 1, type_combo)

        # NOT NULL checkbox
        notnull_cb = QCheckBox()
        notnull_cb.setChecked(col.get("notnull", False))
        notnull_cb.stateChanged.connect(lambda _: self._update_sql_preview())
        self._col_table.setCellWidget(row, 2, self._center_checkbox(notnull_cb))

        # PK checkbox
        pk_cb = QCheckBox()
        pk_cb.setChecked(col.get("pk", False))
        pk_cb.stateChanged.connect(lambda _: self._update_sql_preview())
        self._col_table.setCellWidget(row, 3, self._center_checkbox(pk_cb))

        # Auto Increment checkbox
        autoinc_cb = QCheckBox()
        autoinc_cb.setChecked(col.get("autoinc", False))
        autoinc_cb.stateChanged.connect(lambda _: self._update_sql_preview())
        self._col_table.setCellWidget(row, 4, self._center_checkbox(autoinc_cb))

        # Default
        default_item = QTableWidgetItem(col.get("default", ""))
        self._col_table.setItem(row, 5, default_item)

    def _center_checkbox(self, cb: QCheckBox) -> QWidget:
        """Wrap checkbox in a centered container widget."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(cb)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return container

    def _add_column(self):
        self._col_table.insertRow(self._col_table.rowCount())
        row = self._col_table.rowCount() - 1
        self._set_column_row(row, {
            "name": "", "type": "TEXT", "notnull": False,
            "pk": False, "autoinc": False, "default": ""
        })
        self._update_sql_preview()

    def _remove_column(self):
        row = self._col_table.currentRow()
        if row >= 0:
            self._col_table.removeRow(row)
            self._update_sql_preview()

    # ── SQL generation ──

    def _generate_sql(self) -> str:
        """Generate CREATE TABLE SQL for all tables."""
        self._save_current_table()
        statements = []

        for editor in self._tables:
            name = editor.name.strip()
            if not name:
                continue
            cols = editor.columns
            if not cols:
                continue

            col_defs = []
            pk_cols = []
            for col in cols:
                parts = [f'    "{col["name"]}"', col["type"]]
                if col["pk"]:
                    pk_cols.append(col["name"])
                    if col["autoinc"]:
                        parts.append("PRIMARY KEY AUTOINCREMENT")
                    else:
                        parts.append("PRIMARY KEY")
                if col["notnull"] and not col["pk"]:
                    parts.append("NOT NULL")
                if col["default"]:
                    parts.append(f"DEFAULT {col['default']}")
                col_defs.append(" ".join(parts))

            sql = f'CREATE TABLE "{name}" (\n'
            sql += ",\n".join(col_defs)
            sql += "\n);"
            statements.append(sql)

        return "\n\n".join(statements)

    def _update_sql_preview(self):
        self._sql_preview.setPlainText(self._generate_sql())

    # ── Events ──

    def _on_name_changed(self, text: str):
        idx = self._table_list.currentRow()
        if idx >= 0:
            display_name = text.strip() or f"table_{idx + 1}"
            self._table_list.item(idx).setText(display_name)
        self._update_sql_preview()

    def _on_columns_changed(self, row: int, column: int):
        self._update_sql_preview()

    def _block_signals(self, block: bool):
        self._table_name_edit.blockSignals(block)
        self._col_table.blockSignals(block)

    def _on_create(self):
        """Validate and accept the dialog."""
        self._save_current_table()

        valid_tables = []
        for editor in self._tables:
            name = editor.name.strip()
            if not name:
                continue
            if not editor.columns:
                continue
            valid_tables.append(editor)

        if not valid_tables:
            QMessageBox.warning(self, "Warning", "Please define at least one table with columns.")
            return

        # Check for duplicate table names
        names = [t.name.strip() for t in valid_tables]
        if len(names) != len(set(names)):
            QMessageBox.warning(self, "Warning", "Duplicate table names found.")
            return

        self.accept()

    def get_sql(self) -> str:
        """Return the generated CREATE TABLE SQL."""
        return self._generate_sql()
