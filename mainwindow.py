# mainwindow.py

from PyQt6.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout, QPushButton, QGridLayout, QHBoxLayout, QScrollArea, QSizePolicy, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon, QAction
from slidercontainer import SliderContainer

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.sliderContainer = SliderContainer()
        self.initUI()
        # Create a System Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("resources/storm.png"))  # Set your icon path

        # Create a context menu
        self.tray_menu = QMenu()

        # Create actions
        show_action = QAction("Show", self)
        close_action = QAction("Close", self)

        # Connect actions to functions
        show_action.triggered.connect(self.show)
        close_action.triggered.connect(self.exit_app)

        # Add actions to context menu
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(close_action)

        # Set the context menu
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Show the tray icon
        self.tray_icon.show()
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def exit_app(self):
        QCoreApplication.quit()

    def initUI(self):
        # Create main layout
        self.layout = QGridLayout(self)

        self.layout.addWidget(self.sliderContainer, 0, 0, 1, -1)
        
        # Add stretchable space above the button
        self.layout.setRowStretch(0, 1)

        # Create add button
        addButton = QPushButton("+", self)
        addButton.setFixedSize(20, 20)
        addButton.clicked.connect(self.sliderContainer.addSlider)
        self.layout.addWidget(addButton, 1, 1)  # Add button to bottom right

        self.setLayout(self.layout)

        self.setGeometry(100, 100, 300, 300)
        self.setFixedHeight(300)
        self.setMinimumWidth(300)
        self.setMaximumWidth(900)
        self.setWindowTitle('Slider Application')
        self.show()