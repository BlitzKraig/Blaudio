class Slider:
    def __init__(self, name, app_names, volume, knob_index=None, button_index=None, mute=False):
        self.name         = name
        self.app_names    = app_names
        self.volume       = volume
        self.knob_index   = knob_index
        self.button_index = button_index   # hardware button that mutes/unmutes this slider
        self.mute         = mute

    def serialize(self):
        return {
            'name':         self.name,
            'app_names':    self.app_names,
            'volume':       self.volume,
            'knob_index':   self.knob_index,
            'button_index': self.button_index,
            'mute':         self.mute,
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            name=data['name'],
            app_names=data['app_names'],
            volume=data['volume'],
            knob_index=data['knob_index'],
            button_index=data.get('button_index'),   # .get() for backwards compatibility
            mute=data['mute'],
        )