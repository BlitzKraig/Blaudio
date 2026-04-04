class Slider:
    def __init__(self, name, app_names, volume, knob_index=None, mute=False):
        self.name = name
        self.app_names = app_names
        self.volume = volume
        self.knob_index = knob_index
        self.mute = mute

    def serialize(self):
        return {
            'name': self.name,
            'app_names': self.app_names,
            'volume': self.volume,
            'knob_index': self.knob_index,
            'mute': self.mute,
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            name=data['name'],
            app_names=data['app_names'],
            volume=data['volume'],
            knob_index=data['knob_index'],
            mute=data['mute'],
        )