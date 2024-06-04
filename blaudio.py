import sys
import os
import subprocess
from ui.main_window import Ui_MainWindow
from ui.dynamic_slider import Ui_DynamicSliderContainer
from comtypes import CLSCTX_ALL
from plyer import notification
from PyQt6.QtWidgets import (QApplication, QWidget, QSlider, QVBoxLayout, QPushButton, QGridLayout, 
                             QHBoxLayout, QScrollArea, 
                             QLabel, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox,
                             QGraphicsOpacityEffect, QLineEdit, QComboBox, QMainWindow)
from PyQt6.QtCore import Qt, QCoreApplication, QTimer, QPropertyAnimation
from PyQt6.QtGui import QIcon
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
from tray_icon import TrayIcon
from slider_data import SliderData
from serial_reader import SerialReader
from slider import Slider

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Check if we're running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # We're running in a PyInstaller bundle
            base_path = sys._MEIPASS
            start_hidden = True
        else:
            # We're running in a normal Python environment
            base_path = os.path.dirname(__file__)
            start_hidden = False
            
        self.slider_data = SliderData(self)
        
        self.sliders = []
        self.master_slider = None
        self.slider_object_to_volume_slider = {}
        
        self.setup_ui(start_hidden=start_hidden)
        
        self.tray_icon = TrayIcon(self)
        self.setWindowIcon(QIcon(os.path.join(base_path, "resources/storm.ico")))
       
        self.slider_data.load()
        
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(lambda: (self.slider_data.save(should_notify=False), (self.slider_data.save_master(should_notify=False))))
        self.save_timer.start(300000)
    
        self.serial_reader = SerialReader('COM4', callback=self.on_knob_update)
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        
    def exit_app(self):
        self.slider_data.save(should_notify=False)
        QCoreApplication.quit()
        
    def setup_ui(self, start_hidden=True):
        
        ui = Ui_MainWindow()
        ui.setupUi(self)
        
        self.setWindowTitle("Blaudio")
        
        self.sliders_layout = ui.dynamicSlidersHorzLayout
        
        ui.addSliderButton.clicked.connect(self.create_slider)
        ui.openMixerButton.clicked.connect(self.open_windows_volume_mixer)
        
        self.master_slider = ui.masterSliderVolSlider
        
        loaded_master = self.slider_data.load_master()
        self.master_slider.slider_object = loaded_master if loaded_master else Slider('Master Volume', ['Blaudio: Master Volume'], 50, knob_index=0)
        self.master_slider.setValue(self.master_slider.slider_object.volume)
        self.master_slider.valueChanged.connect(lambda value: self.change_volume(value, self.master_slider.slider_object))
            
        self.slider_object_to_volume_slider[self.master_slider.slider_object] = self.master_slider
        
        if(self.master_slider.slider_object.mute):
            ui.masterSliderMuteButton.setText("🔊")
            
        ui.masterSliderMuteButton.clicked.connect(lambda active: self.toggle_mute(self.master_slider.slider_object))
        
        ui.actionQuit.triggered.connect(self.exit_app)
        ui.actionSettings.setEnabled(False)
        
        self.version_number = "v0.0.3"
        ui.actionAbout.triggered.connect(lambda: self.show_notification(f"Blaudio {self.version_number}"))
        
        self.toast_label = QLabel(self)
        self.toast_label.setFixedWidth(300)
        self.toast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast_label.setStyleSheet("background-color: purple; color: white;")
        self.toast_label.hide()
        self.toast_label_opacity_effect = QGraphicsOpacityEffect(self.toast_label)
        self.toast_label.setGraphicsEffect(self.toast_label_opacity_effect)
        self.toast_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
               
        if not start_hidden:
            self.show()
        
    def on_knob_update(self, knobs):
        # TODO: Improve the performance of this, it's messy
        # Iterate through the knobs
        for knob_index, knob_value in knobs.items():
            # Iterate through the sliders
            for slider in self.sliders:
                # Check if the slider is associated with the knob's index
                if slider.knob_index == knob_index:
                    # Update the slider's value to match the knob's value
                    self.slider_object_to_volume_slider[slider].setValue(knob_value)
            if self.master_slider.slider_object.knob_index == knob_index:
                self.master_slider.setValue(knob_value)
        
    def create_slider(self):
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

        # Create a label for knob assignment
        knob_assignment_label = QLabel("Hardware knob")
        # Create a dropdown for knob assignment
        knob_assignment = QComboBox()
        knob_assignment.addItem("None")
        for i in range(0, 9):
            knob_assignment.addItem(str(i))

        # Add the line edit and list widget to the dialog
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(name_edit)
        dialog.layout().addWidget(app_list)
        dialog.layout().addWidget(knob_assignment_label)
        dialog.layout().addWidget(knob_assignment)

        # Add a "Confirm" button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        dialog.layout().addWidget(button_box)

        result = dialog.exec()

        # If the "OK" button was clicked, create the slider
        if result == QDialog.DialogCode.Accepted:
            text = name_edit.text()
            selected_apps = [item.text() for item in app_list.findItems("*", Qt.MatchFlag.MatchWildcard) if item.checkState() == Qt.CheckState.Checked]

            knob_index = knob_assignment.currentText()
            if knob_index == "None":
                self.add_slider(Slider(text, selected_apps, 50))
            else:
                self.add_slider(Slider(text, selected_apps, 50, knob_index=int(knob_index)))
                
            self.slider_data.save()
            
    def add_slider(self, slider_object: Slider):
        
        slider_widget = QWidget()
        slider_container = Ui_DynamicSliderContainer()
        slider_container.setupUi(slider_widget)
        
        slider_container.widget = slider_widget
        slider_container.slider_object = slider_object
        
        slider_container.dynamicSliderVolSlider.valueChanged.connect(lambda value, apps=slider_object.app_names: self.change_volume(value, slider_container.slider_object))
        slider_container.dynamicSliderVolSlider.setValue(slider_object.volume)
        
        slider_container.dynamicSliderMuteButton.clicked.connect(lambda active, apps=slider_object.app_names: self.toggle_mute(slider_container.slider_object))
        if slider_object.mute:
            slider_container.dynamicSliderMuteButton.setText("🔊")
        
        self.slider_object_to_volume_slider[slider_object] = slider_container.dynamicSliderVolSlider
        
        slider_container.dynamicSliderDeleteButton.clicked.connect(lambda: self.remove_slider(slider_container))
        slider_container.dynamicSliderEditButton.clicked.connect(lambda: self.show_notification("Edit functionality coming soon"))

        slider_container.dynamicSliderLabel.setText(slider_object.name)
    
        self.sliders_layout.insertWidget(self.sliders_layout.count() - 1, slider_widget)  # Insert the widget before the last item (the stretch)

        self.sliders.append(slider_object)  # Add the Slider object to the list of sliders

    def remove_slider(self, slider_container):
        slider_container.widget.deleteLater()
        self.slider_object_to_volume_slider.pop(slider_container.slider_object)
        # Remove the Slider object associated with the slider
        for slider_object in self.sliders:
            if slider_object.name == slider_container.slider_object.name:
                self.sliders.remove(slider_object)
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
            QTimer.singleShot(2000, self.start_fade_out_animation)
        
    def start_fade_out_animation(self):
        # Create an animation to fade out the toast label
        self.fade_out_animation = QPropertyAnimation(self.toast_label_opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(2000 // 2)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.start()
        
    def toggle_mute(self, slider_object):
        slider_object.mute = not slider_object.mute
        if slider_object.mute:
            self.sender().setText("🔊")
        else:
            self.sender().setText("🔇")
        if 'Blaudio: Master Volume' in slider_object.app_names:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMute(slider_object.mute, None)    
        else:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                    if session.Process:
                        if 'All Unassigned' in slider_object.app_names:
                            # Change the volume of the app if it's not assigned to another slider
                            if not self.is_app_assigned(session.Process.name()):
                                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                                volume.SetMute(slider_object.mute, None)
                        elif session.Process.name() in slider_object.app_names:
                            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                            volume.SetMute(slider_object.mute, None)
        self.slider_data.save()
        self.slider_data.save_master()
        
        
    def change_volume(self, value, slider_object):
        slider_object.volume = value
        if 'Blaudio: Master Volume' in slider_object.app_names:
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
                        if 'All Unassigned' in slider_object.app_names:
                            # Change the volume of the app if it's not assigned to another slider
                            if not self.is_app_assigned(session.Process.name()):
                                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                                # Convert QSlider value range (0-100) to volume range (0.0-1.0)
                                volume.SetMasterVolume(value / 100.0, None)
                        elif session.Process.name() in slider_object.app_names:
                            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                            # Convert QSlider value range (0-100) to volume range (0.0-1.0)
                            volume.SetMasterVolume(value / 100.0, None)
    
    def is_app_assigned(self, app_name):
        for slider_object in self.sliders:
            for app_names in slider_object.app_names:
                if app_name in app_names:
                    return True
        return False
    
    def open_windows_volume_mixer(self):
        subprocess.Popen("SndVol.exe")
            

if __name__ == '__main__':
    # TODO: Add a check to see if the app is already running
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec())