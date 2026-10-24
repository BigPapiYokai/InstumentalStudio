from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 12pt;
}
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #3a3a3a; }
QPushButton:pressed { background-color: #1a1a1a; }
QPushButton:disabled { color: #666; background-color: #252525; }
QSlider::groove:horizontal { height: 6px; background: #2d2d2d; border-radius: 3px; }
QSlider::handle:horizontal { width: 14px; margin: -4px 0; border-radius: 7px; background: #0078d4; }
QComboBox { background: #2d2d2d; border: 1px solid #444; border-radius: 4px; padding: 4px; }
QComboBox::drop-down { border: none; }
QScrollBar:vertical { background: #1e1e1e; width: 8px; }
QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 4px; }
QGroupBox { border: 1px solid #444; border-radius: 4px; margin-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLineEdit { background: #2d2d2d; border: 1px solid #444; border-radius: 4px; padding: 4px; }
QProgressBar { border: 1px solid #444; border-radius: 4px; background: #2d2d2d; text-align: center; }
QProgressBar::chunk { background: #0078d4; border-radius: 3px; }
QMenuBar { background: #1e1e1e; }
QMenuBar::item { padding: 6px 12px; }
QMenuBar::item:selected { background: #2d2d2d; }
QMenu { background: #2d2d2d; border: 1px solid #444; }
QMenu::item { padding: 6px 24px; }
QMenu::item:selected { background: #3a3a3a; }
"""

def apply_dark_theme(app: QApplication):
    app.setStyleSheet(DARK_THEME_QSS)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1e1e"))
    palette.setColor(QPalette.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Base, QColor("#252525"))
    palette.setColor(QPalette.AlternateBase, QColor("#2d2d2d"))
    palette.setColor(QPalette.ToolTipBase, QColor("#e0e0e0"))
    palette.setColor(QPalette.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.Button, QColor("#2d2d2d"))
    palette.setColor(QPalette.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.BrightText, QColor("#ff0000"))
    palette.setColor(QPalette.Link, QColor("#0078d4"))
    palette.setColor(QPalette.Highlight, QColor("#0078d4"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)