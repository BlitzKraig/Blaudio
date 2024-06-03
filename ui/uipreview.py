import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget
from uitest import Ui_MainWindow
from slidertest import Ui_DynamicSlider


    
def add_slider():
    # Create a widget for each slider
    slider1_widget = QWidget()
    slider1 = Ui_DynamicSlider()
    slider1.setupUi(slider1_widget)

    ui.dynamicSlidersHorzLayout.insertWidget(ui.dynamicSlidersHorzLayout.count() - 1, slider1_widget)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    
    ui.addSliderButton.clicked.connect(add_slider)
    
    
    window.show()
    sys.exit(app.exec())