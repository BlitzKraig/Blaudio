from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from PyQt6.QtGui import QIcon, QAction

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("resources/storm.png"))  # Set your icon path
        self.tray_menu = QMenu()
        show_action = QAction("Show", self)
        close_action = QAction("Close", self)
        show_action.triggered.connect(parent.show)
        close_action.triggered.connect(parent.exit_app)
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(close_action)
        self.setContextMenu(self.tray_menu)
        self.show()