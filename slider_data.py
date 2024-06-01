import pickle

class SliderData:
    def __init__(self, parent):
        self.parent = parent
        
    def load(self):
        try:
            with open('slider_data.pkl', 'rb') as f:
                slider_data = pickle.load(f)
        except FileNotFoundError:
            return

        for name, app_names, volume in slider_data:
            self.parent.addSlider(name, app_names, volume)

    def save(self, should_notify=True):
        slider_data = [(layout.itemAt(0).widget().text(), layout.itemAt(1).widget().app_names, layout.itemAt(1).widget().value()) 
                       for layout in self.parent.slider_layouts]
        with open('slider_data.pkl', 'wb') as f:
            pickle.dump(slider_data, f)
        if should_notify:
            self.parent.show_notification('Slider data saved successfully!')