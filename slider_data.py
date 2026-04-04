import os
import sys
import json
import pickle
from slider import Slider

class SliderData:
    def __init__(self, parent):
        self.parent = parent
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(application_path, 'slider_data.json')
        self.master_data_file = os.path.join(application_path, 'master_slider_data.json')

    def load(self):
        self._migrate_pickle(
            os.path.splitext(self.data_file)[0] + '.pkl',
            self.data_file,
            is_list=True,
        )
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                slider_data = json.load(f)
        except FileNotFoundError:
            return

        for data in slider_data:
            slider = Slider.deserialize(data)
            self.parent.add_slider(slider)

    def save(self, should_notify=True):
        slider_data = [slider.serialize() for slider in self.parent.sliders]
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(slider_data, f, indent=2)
        if should_notify:
            self.parent.show_notification('Slider data saved successfully!')

    def load_master(self):
        self._migrate_pickle(
            os.path.splitext(self.master_data_file)[0] + '.pkl',
            self.master_data_file,
            is_list=False,
        )
        try:
            with open(self.master_data_file, 'r', encoding='utf-8') as f:
                master_data = json.load(f)
        except FileNotFoundError:
            return

        return Slider.deserialize(master_data)

    def save_master(self, should_notify=True):
        master_data = self.parent.master_slider.slider_object.serialize()
        with open(self.master_data_file, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2)
        if should_notify:
            self.parent.show_notification('Master slider data saved successfully!')

    def _migrate_pickle(self, pkl_path, json_path, is_list):
        """One-time migration: convert a legacy .pkl file to .json then delete it."""
        if os.path.exists(json_path) or not os.path.exists(pkl_path):
            return
        try:
            with open(pkl_path, 'rb') as f:
                raw = pickle.load(f)
            # Legacy format is a tuple: (name, app_names, volume, knob_index, mute)
            if is_list:
                data = [self._tuple_to_dict(item) for item in raw]
            else:
                data = self._tuple_to_dict(raw)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.remove(pkl_path)
        except Exception:
            pass  # If migration fails, load() will just start fresh

    @staticmethod
    def _tuple_to_dict(t):
        """Convert a legacy (name, app_names, volume, knob_index, mute) tuple to a dict."""
        return {
            'name': t[0],
            'app_names': t[1],
            'volume': t[2],
            'knob_index': t[3],
            'mute': t[4],
        }
