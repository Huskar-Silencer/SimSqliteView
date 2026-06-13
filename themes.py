"""Theme stylesheets for SQLite Viewer (Light & Dark)."""


LIGHT_THEME = """
/* ── Global ── */
* {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #f5f5f5;
}

/* ── Menu Bar ── */
QMenuBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #d0d0d0;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 10px;
    background: transparent;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #d0d0d0;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #0078d4;
    color: white;
}
QMenu::separator {
    height: 1px;
    background: #d8d8d8;
    margin: 4px 8px;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #d0d0d0;
    spacing: 4px;
    padding: 2px;
}
QToolBar::separator {
    width: 1px;
    background: #c0c0c0;
    margin: 4px 2px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
}
QToolButton:hover {
    background-color: #d0d0d0;
    border-color: #b0b0b0;
}
QToolButton:pressed {
    background-color: #c0c0c0;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #e0e0e0;
    border-top: 1px solid #d0d0d0;
    color: #333;
}

/* ── Tree Widget ── */
QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    alternate-background-color: #f7f7f7;
    outline: none;
}
QTreeWidget::item {
    padding: 4px 2px;
    border-radius: 3px;
}
QTreeWidget::item:selected {
    background-color: #0078d4;
    color: white;
}
QTreeWidget::item:hover {
    background-color: #e8f0fe;
    color: #1a1a1a;
}
QTreeWidget::item:selected:hover {
    background-color: #006abc;
    color: white;
}
QHeaderView::section {
    background-color: #e8e8e8;
    padding: 4px;
    border: 1px solid #d0d0d0;
    font-weight: bold;
}

/* ── Table Widget ── */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f9f9f9;
    gridline-color: #e0e0e0;
    border: 1px solid #d0d0d0;
    selection-background-color: #0078d4;
    selection-color: white;
}
QTableWidget::item {
    padding: 3px 6px;
}
QTableView QTableCornerButton::section {
    background-color: #e8e8e8;
    border: 1px solid #d0d0d0;
}

/* ── Buttons ── */
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    padding: 5px 14px;
    color: #1a1a1a;
}
QPushButton:hover {
    background-color: #d0d0d0;
    border-color: #0078d4;
}
QPushButton:pressed {
    background-color: #c0c0c0;
}
QPushButton:disabled {
    background-color: #f0f0f0;
    color: #a0a0a0;
    border-color: #d0d0d0;
}

/* ── Text Edits ── */
QTextEdit, QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px;
    color: #1a1a1a;
    selection-background-color: #0078d4;
    selection-color: white;
}
QTextEdit:focus, QLineEdit:focus {
    border-color: #0078d4;
}

/* ── Labels ── */
QLabel {
    color: #1a1a1a;
    background: transparent;
}

/* ── Combo Box ── */
QComboBox {
    background-color: #e0e0e0;
    border: 1px solid #b0b0b0;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox:hover {
    border-color: #0078d4;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    selection-background-color: #0078d4;
    selection-color: white;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #c0c0c0;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #0078d4;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #d0d0d0;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QSplitter::handle:hover {
    background-color: #0078d4;
}

/* ── Scroll Bar ── */
QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #f0f0f0;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #a0a0a0;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Message Box ── */
QMessageBox {
    background-color: #f5f5f5;
}

/* ── Custom object styles ── */
QLabel#welcomeLabel {
    font-size: 16px;
    color: #888888;
}
QLabel#dbPathLabel {
    color: #666666;
}
QLabel#sectionLabel {
    font-weight: bold;
    font-size: 12px;
    padding: 4px;
}
QPushButton#primaryBtn {
    font-weight: bold;
    padding: 4px 12px;
}
QLabel#infoLabel {
    color: #666666;
    padding: 2px;
}
QLabel#errorLabel {
    color: #d32f2f;
    padding: 2px;
}
"""


DARK_THEME = """
/* ── Global ── */
* {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #1e1e2e;
}

/* ── Menu Bar ── */
QMenuBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 2px;
    color: #cdd6f4;
}
QMenuBar::item {
    padding: 4px 10px;
    background: transparent;
    border-radius: 4px;
    color: #cdd6f4;
}
QMenuBar::item:selected {
    background-color: #45475a;
}
QMenu {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    border-radius: 3px;
    color: #cdd6f4;
}
QMenu::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QMenu::separator {
    height: 1px;
    background: #313244;
    margin: 4px 8px;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    spacing: 4px;
    padding: 2px;
}
QToolBar::separator {
    width: 1px;
    background: #45475a;
    margin: 4px 2px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QToolButton:hover {
    background-color: #313244;
    border-color: #45475a;
}
QToolButton:pressed {
    background-color: #45475a;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #181825;
    border-top: 1px solid #313244;
    color: #a6adc8;
}

/* ── Tree Widget ── */
QTreeWidget {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    alternate-background-color: #181825;
    color: #cdd6f4;
    outline: none;
}
QTreeWidget::item {
    padding: 4px 2px;
    border-radius: 3px;
    color: #cdd6f4;
}
QTreeWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QTreeWidget::item:hover {
    background-color: #313244;
    color: #cdd6f4;
}
QTreeWidget::item:selected:hover {
    background-color: #74a8f7;
    color: #1e1e2e;
}
QHeaderView::section {
    background-color: #181825;
    padding: 4px;
    border: 1px solid #313244;
    font-weight: bold;
    color: #cdd6f4;
}

/* ── Table Widget ── */
QTableWidget {
    background-color: #1e1e2e;
    alternate-background-color: #181825;
    gridline-color: #313244;
    border: 1px solid #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QTableWidget::item {
    padding: 3px 6px;
    color: #cdd6f4;
}
QTableView QTableCornerButton::section {
    background-color: #181825;
    border: 1px solid #313244;
}

/* ── Buttons ── */
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 14px;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
    border-color: #313244;
}

/* ── Text Edits ── */
QTextEdit, QLineEdit {
    background-color: #11111b;
    border: 1px solid #313244;
    border-radius: 4px;
    padding: 4px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QTextEdit:focus, QLineEdit:focus {
    border-color: #89b4fa;
}

/* ── Labels ── */
QLabel {
    color: #cdd6f4;
    background: transparent;
}

/* ── Combo Box ── */
QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QComboBox:hover {
    border-color: #89b4fa;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: bold;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #89b4fa;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #313244;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QSplitter::handle:hover {
    background-color: #89b4fa;
}

/* ── Scroll Bar ── */
QScrollBar:vertical {
    background-color: #181825;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #181825;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Message Box ── */
QMessageBox {
    background-color: #1e1e2e;
}

/* ── Custom object styles ── */
QLabel#welcomeLabel {
    font-size: 16px;
    color: #6c7086;
}
QLabel#dbPathLabel {
    color: #a6adc8;
}
QLabel#sectionLabel {
    font-weight: bold;
    font-size: 12px;
    padding: 4px;
}
QPushButton#primaryBtn {
    font-weight: bold;
    padding: 4px 12px;
}
QLabel#infoLabel {
    color: #a6adc8;
    padding: 2px;
}
QLabel#errorLabel {
    color: #f38ba8;
    padding: 2px;
}
"""


# ── Theme registry ──

THEMES = {
    "Light": LIGHT_THEME,
    "Dark": DARK_THEME,
}

DEFAULT_THEME = "Light"
