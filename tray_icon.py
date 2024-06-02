import os
import sys
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from PyQt6.QtGui import QIcon, QAction

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        
         # Check if we're running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # We're running in a PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # We're running in a normal Python environment
            base_path = os.path.dirname(__file__)
        
        self.setIcon(QIcon(os.path.join(base_path, "resources/storm.ico")))  # Set your icon path
        self.setToolTip("Blaudio Volume Controller")
        self.tray_menu = QMenu()
        show_action = QAction("Show", self)
        close_action = QAction("Close", self)
        show_action.triggered.connect(parent.show)
        close_action.triggered.connect(parent.exit_app)
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(close_action)
        self.setContextMenu(self.tray_menu)
        self.activated.connect(self.on_activated)
        self.show()
        
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.parent().show()