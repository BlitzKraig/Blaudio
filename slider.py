class Slider:
    def __init__(self, name, app_names, volume, knob_index=None):
        self.name = name
        self.app_names = app_names
        self.volume = volume
        self.knob_index = knob_index

    def serialize(self):
        return self.name, self.app_names, self.volume, self.knob_index

    @classmethod
    def deserialize(cls, data):
        return cls(*data)