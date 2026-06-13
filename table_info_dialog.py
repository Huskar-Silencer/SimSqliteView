from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QGroupBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from database import DatabaseManager


class TableInfoDialog(QDialog):
    """Dialog for viewing comprehensive table information."""

    def __init__(self, db_manager: DatabaseManager, table_name: str, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self._table_name = table_name
        self.setWindowTitle(f"Table Details — {table_name}")
        self.resize(750, 600)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # ── Summary ──
        summary_group = QGroupBox("Summary")
        summary_form = QFormLayout(summary_group)

        columns = self._db.get_table_info(self._table_name)
        row_count = self._db.get_row_count(self._table_name)
        indexes = self._db.get_table_indexes(self._table_name)
        fks = self._db.get_foreign_keys(self._table_name)

        name_edit = QLineEdit(self._table_name)
        name_edit.setReadOnly(True)
        summary_form.addRow("Table Name:", name_edit)

        rows_edit = QLineEdit(str(row_count))
        rows_edit.setReadOnly(True)
        summary_form.addRow("Row Count:", rows_edit)

        cols_edit = QLineEdit(str(len(columns)))
        cols_edit.setReadOnly(True)
        summary_form.addRow("Column Count:", cols_edit)

        idx_edit = QLineEdit(str(len(indexes)))
        idx_edit.setReadOnly(True)
        summary_form.addRow("Index Count:", idx_edit)

        fk_edit = QLineEdit(str(len(fks)))
        fk_edit.setReadOnly(True)
        summary_form.addRow("Foreign Keys:", fk_edit)

        layout.addWidget(summary_group)

        # ── Tabs ──
        tabs = QTabWidget()

        # Tab 1: Columns
        cols_tab = QWidget()
        cols_layout = QVBoxLayout(cols_tab)
        cols_table = QTableWidget(len(columns), 6)
        cols_table.setHorizontalHeaderLabels(
            ["#", "Column Name", "Type", "Not Null", "Default", "Primary Key"]
        )
        cols_table.horizontalHeader().setStretchLastSection(True)
        cols_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        cols_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        cols_table.setAlternatingRowColors(True)
        cols_table.verticalHeader().setVisible(False)

        for i, col in enumerate(columns):
            cols_table.setItem(i, 0, QTableWidgetItem(str(col["cid"])))
            cols_table.setItem(i, 1, QTableWidgetItem(col["name"]))
            cols_table.setItem(i, 2, QTableWidgetItem(col["type"] or "—"))
            cols_table.setItem(i, 3, QTableWidgetItem("Yes" if col["notnull"] else "No"))
            dv = col["default_value"]
            cols_table.setItem(i, 4, QTableWidgetItem(str(dv) if dv is not None else "—"))
            cols_table.setItem(i, 5, QTableWidgetItem("Yes" if col["pk"] else "No"))
            # Highlight PK rows
            if col["pk"]:
                for c in range(6):
                    item = cols_table.item(i, c)
                    if item:
                        item.setBackground(QColor(255, 255, 200))

        cols_table.resizeColumnsToContents()
        cols_layout.addWidget(cols_table)
        tabs.addTab(cols_tab, "Columns")

        # Tab 2: Indexes
        idx_tab = QWidget()
        idx_layout = QVBoxLayout(idx_tab)
        if indexes:
            idx_table = QTableWidget(len(indexes), 3)
            idx_table.setHorizontalHeaderLabels(["Index Name", "Unique", "Columns"])
            idx_table.horizontalHeader().setStretchLastSection(True)
            idx_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            idx_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            idx_table.setAlternatingRowColors(True)
            idx_table.verticalHeader().setVisible(False)

            for i, idx in enumerate(indexes):
                idx_table.setItem(i, 0, QTableWidgetItem(idx["name"]))
                idx_table.setItem(i, 1, QTableWidgetItem("Yes" if idx["unique"] else "No"))
                idx_table.setItem(i, 2, QTableWidgetItem(", ".join(idx["columns"])))

            idx_table.resizeColumnsToContents()
            idx_layout.addWidget(idx_table)
        else:
            lbl = QLabel("No indexes on this table.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #888; padding: 20px;")
            idx_layout.addWidget(lbl)
        tabs.addTab(idx_tab, "Indexes")

        # Tab 3: Foreign Keys
        fk_tab = QWidget()
        fk_layout = QVBoxLayout(fk_tab)
        if fks:
            fk_table = QTableWidget(len(fks), 5)
            fk_table.setHorizontalHeaderLabels(
                ["From Column", "To Table", "To Column", "On Update", "On Delete"]
            )
            fk_table.horizontalHeader().setStretchLastSection(True)
            fk_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            fk_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            fk_table.setAlternatingRowColors(True)
            fk_table.verticalHeader().setVisible(False)

            for i, fk in enumerate(fks):
                fk_table.setItem(i, 0, QTableWidgetItem(fk["from"]))
                fk_table.setItem(i, 1, QTableWidgetItem(fk["table"]))
                fk_table.setItem(i, 2, QTableWidgetItem(fk["to"]))
                fk_table.setItem(i, 3, QTableWidgetItem(fk["on_update"]))
                fk_table.setItem(i, 4, QTableWidgetItem(fk["on_delete"]))

            fk_table.resizeColumnsToContents()
            fk_layout.addWidget(fk_table)
        else:
            lbl = QLabel("No foreign keys on this table.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #888; padding: 20px;")
            fk_layout.addWidget(lbl)
        tabs.addTab(fk_tab, "Foreign Keys")

        # Tab 4: CREATE SQL
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        sql_view = QTextEdit()
        sql_view.setReadOnly(True)
        sql_view.setFont(QFont("Consolas", 11))
        create_sql = self._db.get_create_sql(self._table_name)
        sql_view.setPlainText(create_sql if create_sql else "No CREATE SQL available.")
        sql_layout.addWidget(sql_view)
        tabs.addTab(sql_tab, "CREATE SQL")

        layout.addWidget(tabs, 1)

        # ── Close button ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
