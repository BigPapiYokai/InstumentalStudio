import sys
import os
from PySide6.QtWidgets import QApplication

# Add app directory to path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.main_window import MainWindow
from app.ui.theme import apply_dark_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SonicLoom Studio")
    app.setOrganizationName("SonicLoom")
    
    apply_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())