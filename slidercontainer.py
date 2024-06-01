# slidercontainer.py

from PyQt6.QtWidgets import QWidget, QScrollArea, QHBoxLayout, QSlider, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class SliderContainer(QWidget):
    def __init__(self):
        super().__init__()

        # Create scroll area and container for sliders
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.container = QWidget()
        self.scrollArea.setWidget(self.container)  # Set container as the widget for scrollArea

        self.sliders_layout = QVBoxLayout(self.container)

    def addSlider(self):
        print("addSlider method called") 
        slider = QSlider(Qt.Orientation.Horizontal, self.container)
        button = QPushButton("Remove", self.container)
        button.clicked.connect(lambda: self.removeSlider(slider, button))
        
        layout = QVBoxLayout()
        layout.addWidget(slider)
        layout.addWidget(button)
        self.sliders_layout.addLayout(layout)

    def removeSlider(self, slider, button):
        # Remove slider and button from layout and delete them
        button.deleteLater()
        slider.deleteLater()