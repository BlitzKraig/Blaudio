import os
import sys
import pickle
from slider import Slider

class SliderData:
    def __init__(self, parent):
        self.parent = parent
        if getattr(sys, 'frozen', False):
            # The application is running as a standalone executable
            application_path = os.path.dirname(sys.executable)
        else:
            # The application is running from a script (e.g., via VS Code)
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(application_path, 'slider_data.pkl')
        
    def load(self):
        try:
            with open(self.data_file, 'rb') as f:
                slider_data = pickle.load(f)
        except FileNotFoundError:
            return

        for data in slider_data:
            slider = Slider.deserialize(data)
            self.parent.add_slider(slider)

    def save(self, should_notify=True):
        slider_data = [slider.serialize() for slider in self.parent.sliders]
        with open(self.data_file, 'wb') as f:
            pickle.dump(slider_data, f)
        if should_notify:
            self.parent.show_notification('Slider data saved successfully!')