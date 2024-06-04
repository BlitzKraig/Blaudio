import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget
from PyQt6.QtCore import QTimer
from main_window import Ui_MainWindow
from dynamic_slider import Ui_DynamicSliderContainer
from qtstyles import StylePicker


    
def add_slider():
    # Create a widget for each slider
    slider1_widget = QWidget()
    slider1 = Ui_DynamicSliderContainer()
    slider1.setupUi(slider1_widget)

    ui.dynamicSlidersHorzLayout.insertWidget(ui.dynamicSlidersHorzLayout.count() - 1, slider1_widget)
    

def change_style():
    global current_style_index
    current_style_index = (current_style_index + 1) % len(styles)
    app.setStyleSheet(StylePicker(styles[current_style_index]).get_sheet())
    
if __name__ == "__main__":
    styles = StylePicker().available_styles
    current_style_index = 0
    
    app = QApplication(sys.argv)
    window = QMainWindow()
    app.setStyleSheet(StylePicker(styles[current_style_index]).get_sheet())
    ui = Ui_MainWindow()
    ui.setupUi(window)
    
    ui.addSliderButton.clicked.connect(add_slider)
    
    # timer = QTimer()
    # timer.timeout.connect(change_style)
    # timer.start(1000)
    
    
    window.show()
    sys.exit(app.exec())
    