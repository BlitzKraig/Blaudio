import pickle
from slider import Slider

class SliderData:
    def __init__(self, parent):
        self.parent = parent
        
    def load(self):
        try:
            with open('slider_data.pkl', 'rb') as f:
                slider_data = pickle.load(f)
        except FileNotFoundError:
            return

        for data in slider_data:
            slider = Slider.deserialize(data)
            self.parent.add_slider(slider)

    def save(self, should_notify=True):
        slider_data = [slider.serialize() for slider in self.parent.sliders]
        with open('slider_data.pkl', 'wb') as f:
            pickle.dump(slider_data, f)
        if should_notify:
            self.parent.show_notification('Slider data saved successfully!')