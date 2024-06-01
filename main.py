import sys
import pickle
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from plyer import notification
from PyQt6.QtWidgets import (QApplication, QWidget, QSlider, QVBoxLayout, QPushButton, QGridLayout, 
                             QHBoxLayout, QScrollArea, QSystemTrayIcon, QMenu, QInputDialog, 
                             QLabel, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, QMessageBox,
                             QSizePolicy, QGraphicsOpacityEffect, QLineEdit)
from PyQt6.QtCore import Qt, QCoreApplication, QSystemSemaphore, QLockFile, QTimer, QPropertyAnimation
from PyQt6.QtGui import QIcon, QAction
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
from tray_icon import TrayIcon
from slider_data import SliderData

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.slider_layouts = []
        self.initUI()
        
        self.tray_icon = TrayIcon(self)
       
        self.slider_data = SliderData(self)
        self.slider_data.load()
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def exit_app(self):
        self.slider_data.save(should_notify=False)
        QCoreApplication.quit()

    def initUI(self):
        # Create main layout
        self.layout = QGridLayout()

      # Create scroll area and container for sliders
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.container = QWidget()
        self.sliders_layout = QHBoxLayout(self.container)
        self.sliders_layout.addStretch(1)
        self.scrollArea.setWidget(self.container)
        self.layout.addWidget(self.scrollArea, 0, 0, 1, -1)  # Add scroll area to top row


        # Add stretchable space above the button
        self.layout.setRowStretch(0, 1)

        # Create add button
        addButton = QPushButton("+")
        addButton.setFixedSize(20, 20)
        addButton.clicked.connect(self.createSlider)
        self.layout.addWidget(addButton, 1, 1)  # Add button to bottom right

        self.setLayout(self.layout)

        self.setGeometry(100, 100, 300, 300)
        self.setFixedHeight(300)
        self.setMinimumWidth(300)
        self.setMaximumWidth(900)
        self.setWindowTitle('Blaudio')
    
        self.toast_label = QLabel(self)
        # self.toast_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toast_label.setFixedWidth(300)
        self.toast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast_label.setStyleSheet("background-color: purple; color: white; padding: 10px;")
        self.toast_label.hide()
        # Add an opacity effect to the toast label
        self.toast_label_opacity_effect = QGraphicsOpacityEffect(self.toast_label)
        self.toast_label.setGraphicsEffect(self.toast_label_opacity_effect)
        

        self.show()

    def createSlider(self):
        # Create a dialog
        dialog = QDialog()
        dialog.setWindowTitle('Create Slider')

        # Create a line edit for the name
        name_edit = QLineEdit()
        name_edit.setPlaceholderText('Enter your slider name')

        # Create a list of running apps
        app_list = QListWidget()
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process:
                item = QListWidgetItem(session.Process.name())
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # Make the item checkable
                item.setCheckState(Qt.CheckState.Unchecked)  # Set initial check state to unchecked
                app_list.addItem(item)

        # Create an All Unassigned option
        all_unassigned_item = QListWidgetItem('All Unassigned')
        all_unassigned_item.setFlags(all_unassigned_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # Make the item checkable
        all_unassigned_item.setCheckState(Qt.CheckState.Unchecked)  # Set initial check state to unchecked
        app_list.addItem(all_unassigned_item)

        # Create a Master Volume option
        master_volume_item = QListWidgetItem('Master Volume')
        master_volume_item.setFlags(master_volume_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # Make the item checkable
        master_volume_item.setCheckState(Qt.CheckState.Unchecked)  # Set initial check state to unchecked
        app_list.addItem(master_volume_item)

        # Connect the itemChanged signal to a function that deselects all other items when master_volume_item is selected
        app_list.itemChanged.connect(lambda item: self.check_selection(item, app_list, master_volume_item))

        # Add the line edit and list widget to the dialog
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(name_edit)
        dialog.layout().addWidget(app_list)

        # Add a "Confirm" button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        dialog.layout().addWidget(button_box)

        result = dialog.exec()

        # If the "OK" button was clicked, create the slider
        if result == QDialog.DialogCode.Accepted:
            text = name_edit.text()
            selected_apps = [item.text() for item in app_list.findItems("*", Qt.MatchFlag.MatchWildcard) if item.checkState() == Qt.CheckState.Checked]

            self.addSlider(text, selected_apps, 50)
            self.slider_data.save()
            
    def check_selection(self, item, app_list, master_volume_item):
        if item == master_volume_item:
            if item.checkState() == Qt.CheckState.Checked:
                for i in range(app_list.count()):
                    if app_list.item(i) != master_volume_item:
                        app_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        elif item != master_volume_item:
            if item.checkState() == Qt.CheckState.Checked:
                master_volume_item.setCheckState(Qt.CheckState.Unchecked)
                       
    def addSlider(self, name, app_names, volume):
            slider = QSlider()
            slider.setOrientation(Qt.Orientation.Vertical)
            slider.valueChanged.connect(self.change_volume)
            slider.app_names = app_names
            slider.setValue(volume)
            
            removeButton = QPushButton("X")
            removeButton.setFixedSize(20, 20)
            removeButton.clicked.connect(lambda: self.removeSlider(slider, removeButton))
            
            # Create an "Edit" button
            edit_button = QPushButton("O")
            edit_button.setFixedSize(20, 20)
            # edit_button.clicked.connect(lambda: self.editSlider(slider, name, app_names))

            slider_layout = QVBoxLayout()
            slider_layout.addWidget(QLabel(name))  # Add the slider name
            slider_layout.addWidget(slider)
            slider_layout.addWidget(removeButton)
            slider_layout.addWidget(edit_button)

            # Create a widget for the slider layout and set a fixed width
            slider_widget = QWidget()
            slider_widget.setLayout(slider_layout)
            slider_widget.setFixedWidth(60)

            self.slider_layouts.append(slider_layout)
            self.sliders_layout.insertWidget(self.sliders_layout.count() - 1, slider_widget)  # Insert the widget before the last item (the stretch)
            

    def removeSlider(self, slider, button):
        slider.deleteLater()
        button.deleteLater()

        for layout in self.slider_layouts:
            if layout.itemAt(1).widget() == slider:  # The slider is now the second item in the layout
                label = layout.itemAt(0).widget()  # The label is the first item in the layout
                label.deleteLater()  # Delete the label
                self.slider_layouts.remove(layout)
                layout.parentWidget().deleteLater()  # Delete the widget containing the layout
                break
        self.slider_data.save()
                        
    def show_notification(self, message, shouldUseSystem=False):
        if shouldUseSystem:
            notification.notify(
                title='Blaudio',
                message=message,
                app_name='Blaudio',
                app_icon='resources/storm.ico'
            )
        else:
            # Set the text of the toast label and show it
            self.toast_label.setText(message)
            self.toast_label.show()

            # Create an animation to fade in the toast label
            self.fade_in_animation = QPropertyAnimation(self.toast_label_opacity_effect, b"opacity")
            self.fade_in_animation.setDuration(300)
            self.fade_in_animation.setStartValue(0)
            self.fade_in_animation.setEndValue(1)
            self.fade_in_animation.start()

            # Use a QTimer to start the fade out animation after the given duration
            QTimer.singleShot(2000, self.startFadeOutAnimation)
        
    def startFadeOutAnimation(self):
        # Create an animation to fade out the toast label
        self.fade_out_animation = QPropertyAnimation(self.toast_label_opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(2000 // 2)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.start()
        
    def change_volume(self, value):
        slider = self.sender()  # Get the slider that triggered the function
        app_names = slider.app_names  # Get the app names from the slider

        if 'Master Volume' in app_names:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            volume.SetMasterVolumeLevelScalar(value / 100.0, None)
            # Convert QSlider value range (0-100) to volume range (0.0-1.0)
            # volume.SetMasterVolumeLevelScalar(value / 100.0, None)            
        else:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                    if session.Process:
                        if 'All Unassigned' in app_names:
                            # Change the volume of the app if it's not assigned to another slider
                            if not self.is_app_assigned(session.Process.name()):
                                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                                # Convert QSlider value range (0-100) to volume range (0.0-1.0)
                                volume.SetMasterVolume(value / 100.0, None)
                        elif session.Process.name() in app_names:
                            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                            # Convert QSlider value range (0-100) to volume range (0.0-1.0)
                            volume.SetMasterVolume(value / 100.0, None)
    
    def is_app_assigned(self, app_name):
        for slider in self.slider_layouts:
            if app_name in slider.itemAt(1).widget().app_names:
                return True
        return False
            

if __name__ == '__main__':
    # TODO: Add a check to see if the app is already running
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec())