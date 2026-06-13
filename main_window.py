import os
import sqlite3 as sqlite3_mod
from PySide6.QtWidgets import (
    QMainWindow, QTreeWidget,
    QTreeWidgetItem, QSplitter, QFileDialog, QMessageBox, QLabel,
    QWidget, QVBoxLayout, QStackedWidget, QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QAction, QActionGroup

from database import DatabaseManager
from table_browser import TableBrowser
from sql_editor import SqlEditor
from db_structure import DbStructureView
from themes import THEMES, DEFAULT_THEME
from create_table_dialog import CreateTableDialog
from table_info_dialog import TableInfoDialog


class MainWindow(QMainWindow):
    """Main application window for SQLite Viewer."""

    def __init__(self):
        super().__init__()
        self._db = DatabaseManager()
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self._status_label.setText("Ready"))
        self.setWindowTitle("SQLite Viewer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._init_menubar()
        self._init_toolbar()
        self._init_statusbar()
        self._init_central()
        self._update_ui_state()
        self._apply_theme(DEFAULT_THEME)

    # ───────────────────── Menu Bar ─────────────────────

    def _init_menubar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        self._new_action = QAction("&New Database...", self)
        self._new_action.setShortcut("Ctrl+N")
        self._new_action.triggered.connect(self._new_database)
        file_menu.addAction(self._new_action)

        self._open_action = QAction("&Open Database...", self)
        self._open_action.setShortcut("Ctrl+O")
        self._open_action.triggered.connect(self._open_database)
        file_menu.addAction(self._open_action)

        self._close_action = QAction("&Close Database", self)
        self._close_action.setShortcut("Ctrl+W")
        self._close_action.triggered.connect(self._close_database)
        file_menu.addAction(self._close_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self._toggle_sql_action = QAction("Show SQL Editor", self)
        self._toggle_sql_action.setCheckable(True)
        self._toggle_sql_action.setChecked(False)
        self._toggle_sql_action.setShortcut("Ctrl+E")
        self._toggle_sql_action.triggered.connect(self._toggle_sql_editor)
        view_menu.addAction(self._toggle_sql_action)

        view_menu.addSeparator()

        self._refresh_action = QAction("&Refresh", self)
        self._refresh_action.setShortcut("F5")
        self._refresh_action.triggered.connect(self._refresh_db)
        view_menu.addAction(self._refresh_action)

        view_menu.addSeparator()

        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        self._theme_action_group = QActionGroup(self)
        self._theme_action_group.setExclusive(True)
        self._theme_actions = {}
        for name in THEMES:
            action = QAction(name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, n=name: self._apply_theme(n))
            self._theme_action_group.addAction(action)
            theme_menu.addAction(action)
            self._theme_actions[name] = action
        self._theme_actions.get(DEFAULT_THEME, next(iter(self._theme_actions.values()))).setChecked(True)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ───────────────────── Toolbar ─────────────────────

    def _init_toolbar(self):
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        toolbar.addAction(self._new_action)
        toolbar.addAction(self._open_action)
        toolbar.addAction(self._close_action)
        toolbar.addSeparator()
        toolbar.addAction(self._refresh_action)
        toolbar.addSeparator()
        toolbar.addAction(self._toggle_sql_action)

    # ───────────────────── Status Bar ─────────────────────

    def _init_statusbar(self):
        statusbar = self.statusBar()
        self._status_label = QLabel("Ready")
        self._db_path_permanent_label = QLabel("No database")
        self._db_path_permanent_label.setObjectName("dbPathLabel")
        statusbar.addWidget(self._status_label, 1)
        statusbar.addPermanentWidget(self._db_path_permanent_label)

    # ───────────────────── Central Widget ─────────────────────

    def _init_central(self):
        self._splitter = QSplitter(Qt.Horizontal)

        # Left: tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Database Objects")
        self._tree.setMinimumWidth(200)
        self._tree.setMaximumWidth(400)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self._splitter.addWidget(self._tree)

        # Right: stacked pages
        self._stack = QStackedWidget()

        # Page 0: welcome
        welcome = QWidget()
        wl = QVBoxLayout(welcome)
        lbl = QLabel("Welcome to SQLite Viewer\n\nOpen a database file to get started.\n(File → Open Database or Ctrl+O)")
        lbl.setObjectName("welcomeLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("")
        wl.addWidget(lbl)
        self._stack.addWidget(welcome)

        # Page 1: table browser
        self._table_browser = TableBrowser(self._db)
        self._table_browser.status_message.connect(self._set_status)
        self._stack.addWidget(self._table_browser)

        # Page 2: SQL editor
        self._sql_editor = SqlEditor(self._db)
        self._sql_editor.status_message.connect(self._set_status)
        self._stack.addWidget(self._sql_editor)

        # Page 3: schema view
        self._db_structure = DbStructureView(self._db)
        self._stack.addWidget(self._db_structure)

        self._splitter.addWidget(self._stack)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([250, 950])

        self.setCentralWidget(self._splitter)

    # ───────────────────── Actions ─────────────────────

    def _new_database(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Create New Database", "",
            "SQLite Database (*.db);;All Files (*)"
        )
        if not path:
            return

        try:
            # Create empty database file
            conn = sqlite3_mod.connect(path)
            conn.close()

            # Open the newly created database
            self._db.connect(path)
            self._db_path_permanent_label.setText(f"Database: {path}")
            self._set_status(f"Created: {os.path.basename(path)}")
            self._update_ui_state()

            # Show create table dialog
            dlg = CreateTableDialog(self)
            if dlg.exec() == CreateTableDialog.Accepted:
                sql = dlg.get_sql()
                if sql:
                    self._db.execute_script(sql)
                    self._set_status("Schema created successfully.")

            self._populate_tree()
            self._stack.setCurrentWidget(self._table_browser)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create database:\n{e}")
            self._set_status("Failed to create database.")

    def _open_database(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Database", "", "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        if not path:
            return

        try:
            self._db.connect(path)
            self._db_path_permanent_label.setText(f"Database: {path}")
            self._set_status(f"Opened: {os.path.basename(path)}")
            self._populate_tree()
            self._stack.setCurrentWidget(self._table_browser)
            self._update_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open database:\n{e}")
            self._set_status("Failed to open database.")

    def _close_database(self):
        self._db.close()
        self._tree.clear()
        self._table_browser.clear()
        self._sql_editor.clear_editor()
        self._db_structure.clear()
        self._stack.setCurrentIndex(0)  # welcome page
        self._db_path_permanent_label.setText("No database")
        self._set_status("Database closed.")
        self._update_ui_state()

    def _refresh_db(self):
        if not self._db.is_connected:
            return
        self._populate_tree()
        self._set_status("Database refreshed.")

    def _toggle_sql_editor(self, checked: bool):
        if checked:
            self._stack.setCurrentWidget(self._sql_editor)
            self._toggle_sql_action.setText("Hide SQL Editor")
        else:
            if self._db.is_connected:
                self._stack.setCurrentWidget(self._table_browser)
            self._toggle_sql_action.setText("Show SQL Editor")

    def _show_about(self):
        QMessageBox.about(
            self,
            "About SQLite Viewer",
            "<h3>SQLite Viewer</h3>"
            "<p>A lightweight SQLite database browser and query tool.</p>"
            "<p>Built with Python and PySide6.</p>"
        )

    # ───────────────────── Tree ─────────────────────

    def _populate_tree(self):
        self._tree.clear()
        if not self._db.is_connected:
            return

        db_name = os.path.basename(self._db.db_path)
        root = QTreeWidgetItem(self._tree, [db_name])
        root.setExpanded(True)

        # Tables
        tables_node = QTreeWidgetItem(root, ["Tables"])
        tables_node.setExpanded(True)
        for t in self._db.get_tables():
            count = self._db.get_row_count(t)
            item = QTreeWidgetItem(tables_node, [f"{t}  ({count} rows)"])
            item.setData(0, Qt.UserRole, ("table", t))
            # Add column children
            for col in self._db.get_table_info(t):
                col_item = QTreeWidgetItem(item, [f"{col['name']}  [{col['type'] or 'ANY'}]"])
                col_item.setData(0, Qt.UserRole, ("column", col["name"]))

        # Views
        views = self._db.get_views()
        if views:
            views_node = QTreeWidgetItem(root, ["Views"])
            views_node.setExpanded(True)
            for v in views:
                item = QTreeWidgetItem(views_node, [v])
                item.setData(0, Qt.UserRole, ("view", v))

        # Indexes
        indexes = self._db.get_indexes()
        if indexes:
            idx_node = QTreeWidgetItem(root, ["Indexes"])
            idx_node.setExpanded(True)
            for idx in indexes:
                item = QTreeWidgetItem(idx_node, [idx])
                item.setData(0, Qt.UserRole, ("index", idx))

        # Triggers
        triggers = self._db.get_triggers()
        if triggers:
            trig_node = QTreeWidgetItem(root, ["Triggers"])
            trig_node.setExpanded(True)
            for trig in triggers:
                item = QTreeWidgetItem(trig_node, [trig])
                item.setData(0, Qt.UserRole, ("trigger", trig))

        # Full schema node
        schema_item = QTreeWidgetItem(root, ["[Full Schema]"])
        schema_item.setData(0, Qt.UserRole, ("schema", "__all__"))

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        obj_type, obj_name = data

        if obj_type == "table":
            self._table_browser.load_table(obj_name)
            self._stack.setCurrentWidget(self._table_browser)
        elif obj_type in ("view", "index", "trigger", "column"):
            target = obj_name if obj_type != "column" else item.parent().text(0).split("  (")[0]
            self._db_structure.show_object(target)
            self._stack.setCurrentWidget(self._db_structure)
        elif obj_type == "schema":
            self._db_structure.show_full_schema()
            self._stack.setCurrentWidget(self._db_structure)

    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Show table info dialog on double-click for table items."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        obj_type, obj_name = data

        if obj_type == "table":
            dlg = TableInfoDialog(self._db, obj_name, self)
            dlg.exec()
        elif obj_type == "column":
            # Double-click on a column shows parent table info
            parent_table = item.parent().text(0).split("  (")[0]
            dlg = TableInfoDialog(self._db, parent_table, self)
            dlg.exec()

    # ───────────────────── Helpers ─────────────────────

    def _apply_theme(self, theme_name: str):
        """Apply the given theme to the entire application."""
        stylesheet = THEMES.get(theme_name, "")
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
        if theme_name in self._theme_actions:
            self._theme_actions[theme_name].setChecked(True)
        self._set_status(f"Theme switched to: {theme_name}")

    def _set_status(self, message: str):
        self._status_label.setText(message)
        self._status_timer.start(3000)

    def _update_ui_state(self):
        connected = self._db.is_connected
        self._close_action.setEnabled(connected)
        self._refresh_action.setEnabled(connected)
        self._toggle_sql_action.setEnabled(connected)

    def closeEvent(self, event):
        self._db.close()
        event.accept()
