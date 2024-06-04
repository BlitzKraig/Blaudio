class Slider:
    def __init__(self, name, app_names, volume, knob_index=None, mute=False):
        self.name = name
        self.app_names = app_names
        self.volume = volume
        self.knob_index = knob_index
        self.mute = mute

    def serialize(self):
        return self.name, self.app_names, self.volume, self.knob_index, self.mute

    @classmethod
    def deserialize(cls, data):
        return cls(*data)