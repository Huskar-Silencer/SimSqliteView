from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel
)
from PySide6.QtGui import QFont

from database import DatabaseManager


class DbStructureView(QWidget):
    """Widget for viewing the CREATE SQL of database objects."""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("Schema")
        self._label.setObjectName("sectionLabel")
        self._label.setStyleSheet("")
        layout.addWidget(self._label)

        self._sql_view = QTextEdit()
        self._sql_view.setReadOnly(True)
        self._sql_view.setFont(QFont("Consolas", 11))
        self._sql_view.setPlaceholderText("Select an object from the tree to view its schema...")
        layout.addWidget(self._sql_view, 1)

    def show_object(self, object_name: str):
        """Display the CREATE SQL for the given database object."""
        if not self._db.is_connected:
            return
        try:
            sql = self._db.get_create_sql(object_name)
            self._label.setText(f"Schema — {object_name}")
            self._sql_view.setPlainText(sql if sql else "No schema available.")
        except Exception as e:
            self._sql_view.setPlainText(f"Error: {e}")

    def show_full_schema(self):
        """Display the full schema of all database objects."""
        if not self._db.is_connected:
            return
        try:
            objects = self._db.get_all_objects()
            lines = []
            for obj in objects:
                if obj["sql"]:
                    lines.append(f"-- {obj['type'].upper()}: {obj['name']}")
                    lines.append(obj["sql"])
                    lines.append("")
            self._label.setText("Full Database Schema")
            self._sql_view.setPlainText("\n".join(lines) if lines else "No schema objects found.")
        except Exception as e:
            self._sql_view.setPlainText(f"Error: {e}")

    def clear(self):
        self._sql_view.clear()
        self._label.setText("Schema")

    def set_db(self, db_manager: DatabaseManager):
        self._db = db_manager
