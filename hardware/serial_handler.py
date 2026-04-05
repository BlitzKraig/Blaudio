from audio.audio_controller import ensure_com


class SerialHandler:
    """
    Translates raw serial events (knob positions, button presses) into
    application-level actions: volume changes, mute toggles, window visibility.

    Receives knob/button data from SerialReader callbacks and calls back into
    the Api for state updates and audio control. No imports of api.py are
    needed — the Api instance is passed in at construction time to avoid
    circular imports.
    """

    _KNOB_LOW  = 10   # knob must dip to or below this value (0–100 scale)
    _KNOB_HIGH = 90   # knob must rise to or above this value (0–100 scale)

    def __init__(self, config, api):
        """
        Args:
            config: The loaded blaudio_config.json dict.
            api:    The Api instance (used for state access and high-level actions).
        """
        self._config              = config
        self._api                 = api
        self._last_knob_values    = {}
        self._last_button_values  = {}
        self._detection_callback  = None   # set while waiting for a button mapping press
        self._knob_detection_callback = None  # set while waiting for a knob sweep
        self._knob_detection_seen     = {}    # knob_index -> {'low': bool, 'high': bool}

    # ── Button detection mode ─────────────────────────────────────────

    def start_detection(self, callback):
        """
        Enter button-detection mode.  The next hardware button press will fire
        callback(button_index) instead of being handled normally, and detection
        mode will exit automatically.
        """
        self._detection_callback = callback

    def cancel_detection(self):
        """Cancel detection mode without firing the callback."""
        self._detection_callback = None

    # ── Knob detection mode ───────────────────────────────────────────

    def start_knob_detection(self, callback):
        """
        Enter knob-detection mode.  The first knob swept from low (≤_KNOB_LOW)
        to high (≥_KNOB_HIGH) — or high to low — fires callback(knob_index) and
        exits detection mode automatically.
        """
        self._knob_detection_callback = callback
        self._knob_detection_seen     = {}

    def cancel_knob_detection(self):
        """Cancel knob-detection mode without firing the callback."""
        self._knob_detection_callback = None
        self._knob_detection_seen     = {}

    # ── SerialReader callbacks ────────────────────────────────────────

    def on_serial_update(self, knobs, buttons):
        """Called by SerialReader whenever new knob/button data arrives."""
        ensure_com()

        master_slider = self._api._master_slider
        sliders       = self._api._sliders

        for knob_index, knob_value in knobs.items():
            # Skip if the value hasn't changed since the last poll.
            if self._last_knob_values.get(knob_index) == knob_value:
                continue
            self._last_knob_values[knob_index] = knob_value

            if self._knob_detection_callback is not None:
                seen = self._knob_detection_seen.setdefault(knob_index, {'low': False, 'high': False})
                if knob_value <= self._KNOB_LOW:
                    seen['low'] = True
                if knob_value >= self._KNOB_HIGH:
                    seen['high'] = True
                if seen['low'] and seen['high']:
                    cb = self._knob_detection_callback
                    self._knob_detection_callback = None
                    self._knob_detection_seen     = {}
                    cb(knob_index)
                continue   # don't apply volume changes while detecting

            if master_slider.knob_index == knob_index:
                self._api._master_volume  = knob_value
                master_slider.volume      = knob_value
                # Push UI update first so the display is always responsive,
                # then apply audio — a COM/pycaw error must not kill this thread.
                self._api._push('master_volume', {'volume': knob_value})
                try:
                    self._api._audio.apply_master_volume(knob_value)
                except Exception:
                    pass
            else:
                for i, slider in enumerate(sliders):
                    if slider.knob_index == knob_index:
                        slider.volume = knob_value
                        self._api._push('slider_volume', {'index': i, 'volume': knob_value})
                        try:
                            self._api._audio.apply_slider_volume(knob_value, slider, sliders)
                        except Exception:
                            pass

        for button_index, button_value in buttons.items():
            # Detect falling edge (button pressed, given INPUT_PULLUP wiring).
            if button_value == 0 and self._last_button_values.get(button_index, 1) == 1:
                if self._detection_callback is not None:
                    # Reject reserved buttons and keep listening.
                    reserved = {self._config['MUTE_BUTTON_INDEX'], self._config['SHOW_HIDE_BUTTON_INDEX']}
                    if button_index in reserved:
                        self._api._push('notification', {
                            'message': f'Button {button_index} is reserved. Press a different button.'
                        })
                    else:
                        cb = self._detection_callback
                        self._detection_callback = None
                        cb(button_index)
                elif button_index == self._config['MUTE_BUTTON_INDEX']:
                    muted = self._api.toggle_master_mute()
                    self._api._push('master_mute', {'mute': muted})
                elif button_index == self._config['SHOW_HIDE_BUTTON_INDEX']:
                    if self._api._visible:
                        self._api.hide_window()
                    else:
                        self._api.show_window()
                else:
                    # Check if this button is assigned to a slider's mute.
                    matched = False
                    for i, slider in enumerate(sliders):
                        if slider.button_index is not None and slider.button_index == button_index:
                            slider.mute = not slider.mute
                            self._api._audio.apply_slider_mute(slider, sliders)
                            self._api._slider_data.save(should_notify=False)
                            self._api._push('slider_mute', {'index': i, 'mute': slider.mute})
                            matched = True
                    if not matched:
                        self._api._push('notification', {
                            'message': f'Button {button_index} not mapped. Add or edit a slider to map this button.'
                        })

            self._last_button_values[button_index] = button_value

    def on_message(self, message):
        """Called by SerialReader to forward informational/error messages."""
        self._api._push('notification', {'message': message})
