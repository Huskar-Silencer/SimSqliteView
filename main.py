import csv
import os
import sqlite3
from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    message: str = ""


@dataclass(frozen=True)
class HistoryEntry:
    columns: list[str]
    rows: list[tuple]
    status_message: str


class SqliteTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._columns: list[str] = []
        self._rows: list[tuple] = []

    def set_result(self, columns: list[str], rows: list[tuple]) -> None:
        self.beginResetModel()
        self._columns = columns
        self._rows = rows
        self.endResetModel()

    def is_empty(self) -> bool:
        return not self._columns and not self._rows

    def snapshot(self) -> tuple[list[str], list[tuple]]:
        return list(self._columns), list(self._rows)

    def raw_value(self, index: QModelIndex):
        if not index.isValid():
            return None
        return self._rows[index.row()][index.column()]

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        value = self._rows[index.row()][index.column()]
        if value is None:
            return "NULL"
        if isinstance(value, (bytes, bytearray, memoryview)):
            try:
                return bytes(value).hex()
            except Exception:
                return "<BLOB>"
        return str(value)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
            return str(section)
        return str(section + 1)


class ValueViewerDialog(QDialog):
    def __init__(self, *, column_name: str, value, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("View Full Value")
        self.resize(800, 500)

        value_type = type(value).__name__
        full_text, byte_count, char_count = self._format_value(value)

        self._meta_label = QLabel(
            f"Column: {column_name} | Type: {value_type} | Bytes: {byte_count} | Chars: {char_count}"
        )
        self._meta_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._text.setPlainText(full_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._meta_label)
        layout.addWidget(self._text, 1)
        layout.addWidget(buttons)

    @staticmethod
    def _format_value(value) -> tuple[str, int, int]:
        if value is None:
            return "NULL", 0, 4

        if isinstance(value, (bytes, bytearray, memoryview)):
            data = bytes(value)
            return (
                ValueViewerDialog._bytes_to_hex_multiline(data),
                len(data),
                len(data) * 2,
            )

        if isinstance(value, str):
            b = value.encode("utf-8")
            return value, len(b), len(value)

        text = str(value)
        b = text.encode("utf-8")
        return text, len(b), len(text)

    @staticmethod
    def _bytes_to_hex_multiline(data: bytes) -> str:
        if not data:
            return ""
        lines: list[str] = []
        chunk_size = 16
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            lines.append(hex_part)
        return "\n".join(lines)


class SqliteClient:
    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None
        self._path: str | None = None
        self._readonly: bool = False

    @property
    def is_open(self) -> bool:
        return self._conn is not None

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def readonly(self) -> bool:
        return self._readonly

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None
                self._path = None
                self._readonly = False

    def open(self, db_path: str, *, readonly: bool) -> None:
        self.close()
        if readonly:
            uri = f"file:{db_path}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
        else:
            conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        self._conn = conn
        self._path = db_path
        self._readonly = readonly

    def list_tables(self) -> list[str]:
        conn = self._require_conn()
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cur.fetchall()]

    def execute(self, sql: str) -> QueryResult:
        conn = self._require_conn()
        sql_stripped = sql.strip().rstrip(";")
        if not sql_stripped:
            return QueryResult(columns=[], rows=[], message="SQL is empty")

        cur = conn.cursor()
        try:
            cur.execute(sql_stripped)
            if cur.description is not None:
                columns = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return QueryResult(
                    columns=columns,
                    rows=[tuple(r) for r in rows],
                    message=f"Returned {len(rows)} rows",
                )
            else:
                if self._readonly:
                    conn.rollback()
                    return QueryResult(
                        columns=[],
                        rows=[],
                        message="Non-query statements are not allowed in read-only mode",
                    )
                conn.commit()
                return QueryResult(
                    columns=[], rows=[], message=f"Rows affected: {cur.rowcount}"
                )
        finally:
            cur.close()

    def preview_table(
        self, table_name: str, *, limit: int = 500, offset: int = 0
    ) -> QueryResult:
        conn = self._require_conn()
        safe_table_name = table_name.replace('"', '""')
        sql = f'SELECT * FROM "{safe_table_name}" LIMIT ? OFFSET ?'
        cur = conn.execute(sql, (limit, offset))
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return QueryResult(
            columns=columns,
            rows=[tuple(r) for r in rows],
            message=f"Previewed {len(rows)} rows",
        )

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not open")
        return self._conn


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SqliteView (PySide6)")
        self.resize(1100, 700)

        self._client = SqliteClient()
        self._model = SqliteTableModel(self)
        self._back_stack: list[HistoryEntry] = []
        self._last_status_message: str = ""

        self._table_list = QListWidget()
        self._table_list.itemSelectionChanged.connect(self._on_table_selected)

        self._table_view = QTableView()
        self._table_view.setModel(self._model)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.horizontalHeader().setMinimumSectionSize(80)
        self._table_view.horizontalHeader().setTextElideMode(Qt.ElideNone)
        self._table_view.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self._table_view.setSelectionMode(QTableView.ExtendedSelection)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._table_view.setStyleSheet(
            "QTableView::item:selected { background-color: #1e6bd6; color: white; }"
        )
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(
            self._show_table_context_menu
        )
        self._table_view.doubleClicked.connect(self._view_index_value)

        self._sql_input = QPlainTextEdit()
        self._sql_input.setPlaceholderText(
            "Enter SQL (supports SELECT/UPDATE/INSERT/DELETE, etc.)"
        )
        self._sql_input.setPlainText(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )

        self._limit_input = QLineEdit("500")
        self._limit_input.setFixedWidth(90)
        self._limit_input.setPlaceholderText("limit")

        self._run_btn = QPushButton("Run SQL")
        self._run_btn.clicked.connect(self._run_sql)

        self._back_btn = QPushButton("Back")
        self._back_btn.clicked.connect(self._go_back)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.clicked.connect(self._export_csv)

        query_panel = QWidget()
        query_panel_layout = QVBoxLayout(query_panel)
        query_panel_layout.setContentsMargins(0, 0, 0, 0)
        query_panel_layout.addWidget(self._sql_input, 1)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self._table_view)
        right_splitter.addWidget(query_panel)
        right_splitter.setStretchFactor(0, 4)
        right_splitter.setStretchFactor(1, 2)
        self._right_splitter = right_splitter
        self._query_panel = query_panel
        self._query_panel.setVisible(False)
        self._right_splitter.setSizes([1, 0])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self._table_list)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 4)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(main_splitter)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self._build_actions()
        self._refresh_ui_state()

        self.setAcceptDrops(True)

    def closeEvent(self, event) -> None:
        self._client.close()
        super().closeEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        local_path = urls[0].toLocalFile()
        if local_path and os.path.isfile(local_path):
            self._open_db(local_path, readonly=False)

    def _build_actions(self) -> None:
        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_dialog)

        open_ro_action = QAction("Open Read-Only...", self)
        open_ro_action.triggered.connect(lambda: self._open_dialog(readonly=True))

        close_action = QAction("Close Database", self)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self._close_db)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)

        self._toggle_sql_panel_action = QAction("SQL", self)
        self._toggle_sql_panel_action.setCheckable(True)
        self._toggle_sql_panel_action.setChecked(False)
        self._toggle_sql_panel_action.triggered.connect(self._toggle_sql_panel)

        self.addAction(open_action)
        self.addAction(open_ro_action)
        self.addAction(close_action)
        self.addAction(exit_action)
        self.addAction(self._toggle_sql_panel_action)
        self.menuBar().setVisible(False)

        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(open_action)
        toolbar.addAction(open_ro_action)
        toolbar.addAction(close_action)
        toolbar.addAction(exit_action)
        toolbar.addSeparator()
        toolbar.addAction(self._toggle_sql_panel_action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Limit"))
        toolbar.addWidget(self._limit_input)
        toolbar.addSeparator()
        toolbar.addWidget(self._back_btn)
        toolbar.addWidget(self._export_btn)
        toolbar.addWidget(self._run_btn)

    @Slot()
    def _open_dialog(self, readonly: bool = False) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQLite Database",
            "",
            "SQLite (*.db *.sqlite *.sqlite3);;All Files (*.*)",
        )
        if not path:
            return
        self._open_db(path, readonly=readonly)

    def _open_db(self, path: str, *, readonly: bool) -> None:
        try:
            self._client.open(path, readonly=readonly)
            self._back_stack.clear()
            self._model.set_result([], [])
            self._set_status_message(self._format_db_status("Opened"))
            self._load_tables()
            self._refresh_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Open Failed", str(e))

    @Slot()
    def _close_db(self) -> None:
        self._client.close()
        self._back_stack.clear()
        self._model.set_result([], [])
        self._table_list.clear()
        self._set_status_message("Database closed")
        self._refresh_ui_state()

    def _load_tables(self) -> None:
        self._table_list.clear()
        try:
            for name in self._client.list_tables():
                self._table_list.addItem(QListWidgetItem(name))
        except Exception as e:
            QMessageBox.critical(self, "Failed to load tables", str(e))

    def _refresh_ui_state(self) -> None:
        is_open = self._client.is_open
        self._table_list.setEnabled(is_open)
        self._table_view.setEnabled(is_open)
        self._sql_input.setEnabled(is_open)
        self._run_btn.setEnabled(is_open)
        self._export_btn.setEnabled(is_open)
        self._limit_input.setEnabled(is_open)
        self._back_btn.setEnabled(is_open and bool(self._back_stack))
        if not is_open:
            self.setWindowTitle("SqliteView (PySide6)")
        else:
            self.setWindowTitle(
                f"SqliteView - {os.path.basename(self._client.path or '')}"
            )

    def _format_db_status(self, prefix: str) -> str:
        path = self._client.path or ""
        mode = "readOnly" if self._client.readonly else "writeAndRead"
        return f"{prefix}: {path}({mode})"

    @Slot(bool)
    def _toggle_sql_panel(self, visible: bool) -> None:
        self._query_panel.setVisible(visible)
        if visible:
            total = max(self._right_splitter.height(), 1)
            self._right_splitter.setSizes([int(total * 0.65), int(total * 0.35)])
            self._sql_input.setFocus()
        else:
            self._right_splitter.setSizes([1, 0])

    @Slot()
    def _on_table_selected(self) -> None:
        if not self._client.is_open:
            return
        items = self._table_list.selectedItems()
        if not items:
            return
        table_name = items[0].text()
        limit = self._safe_int(
            self._limit_input.text(), default=500, minimum=1, maximum=50_000
        )
        try:
            result = self._client.preview_table(table_name, limit=limit)
            self._apply_result(
                result,
                status_message=f"{self._format_db_status('Table Preview')} | {table_name} | {result.message}",
            )
            self._table_view.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Preview Failed", str(e))

    @Slot()
    def _run_sql(self) -> None:
        if not self._client.is_open:
            return
        sql = self._sql_input.toPlainText()
        try:
            result = self._client.execute(sql)
            if result.columns:
                self._apply_result(
                    result,
                    status_message=f"{self._format_db_status('SQL')} | {result.message}",
                )
                self._table_view.resizeColumnsToContents()
            else:
                self._set_status_message(
                    f"{self._format_db_status('SQL')} | {result.message}"
                )
            self._load_tables()
        except Exception as e:
            QMessageBox.critical(self, "Execution Failed", str(e))

    @Slot()
    def _go_back(self) -> None:
        if not self._client.is_open:
            return
        if not self._back_stack:
            return
        entry = self._back_stack.pop()
        self._model.set_result(entry.columns, entry.rows)
        self._table_view.resizeColumnsToContents()
        self._set_status_message(entry.status_message)
        self._refresh_ui_state()

    @Slot()
    def _show_table_context_menu(self, pos) -> None:
        index = self._table_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        view_action = menu.addAction("View Full Value")
        selected = menu.exec(self._table_view.viewport().mapToGlobal(pos))
        if selected == view_action:
            self._view_index_value(index)

    @Slot(QModelIndex)
    def _view_index_value(self, index: QModelIndex) -> None:
        if not self._client.is_open:
            return
        if not index.isValid():
            return
        column_name = self._model.headerData(
            index.column(), Qt.Horizontal, Qt.DisplayRole
        ) or str(index.column())
        value = self._model.raw_value(index)
        dlg = ValueViewerDialog(column_name=str(column_name), value=value, parent=self)
        dlg.exec()

    @Slot()
    def _export_csv(self) -> None:
        if not self._client.is_open:
            return
        if self._model.rowCount() == 0 or self._model.columnCount() == 0:
            QMessageBox.information(self, "Export CSV", "No query results to export")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save as CSV", "result.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                headers = [
                    self._model.headerData(c, Qt.Horizontal, Qt.DisplayRole)
                    for c in range(self._model.columnCount())
                ]
                writer.writerow(headers)
                for r in range(self._model.rowCount()):
                    row = []
                    for c in range(self._model.columnCount()):
                        row.append(
                            self._model.data(self._model.index(r, c), Qt.DisplayRole)
                        )
                    writer.writerow(row)
            self._set_status_message(f"Exported: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _apply_result(self, result: QueryResult, *, status_message: str) -> None:
        if not self._model.is_empty():
            columns, rows = self._model.snapshot()
            self._back_stack.append(
                HistoryEntry(
                    columns=columns, rows=rows, status_message=self._last_status_message
                )
            )
            if len(self._back_stack) > 50:
                self._back_stack.pop(0)
        self._model.set_result(result.columns, result.rows)
        self._set_status_message(status_message)
        self._refresh_ui_state()

    def _set_status_message(self, message: str) -> None:
        self._last_status_message = message
        self.statusBar().showMessage(message)

    @staticmethod
    def _safe_int(text: str, *, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(text.strip())
        except Exception:
            return default
        return max(minimum, min(maximum, value))


def main() -> int:
    app = QApplication([])
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
