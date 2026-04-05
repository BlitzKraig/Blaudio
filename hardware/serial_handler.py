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

    def __init__(self, config, api):
        """
        Args:
            config: The loaded blaudio_config.json dict.
            api:    The Api instance (used for state access and high-level actions).
        """
        self._config             = config
        self._api                = api
        self._last_knob_values   = {}
        self._last_button_values = {}

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

            if master_slider.knob_index == knob_index:
                # Hardware moved the master knob
                self._api._master_volume  = knob_value
                master_slider.volume      = knob_value
                self._api._audio.apply_master_volume(knob_value)
                self._api._push('master_volume', {'volume': knob_value})
            else:
                # Check whether any app slider is mapped to this knob
                for i, slider in enumerate(sliders):
                    if slider.knob_index == knob_index:
                        slider.volume = knob_value
                        self._api._audio.apply_slider_volume(knob_value, slider, sliders)
                        self._api._push('slider_volume', {'index': i, 'volume': knob_value})

        for button_index, button_value in buttons.items():
            # Detect falling edge (button pressed down)
            if button_value == 0 and self._last_button_values.get(button_index, 1) == 1:
                if button_index == self._config['MUTE_BUTTON_INDEX']:
                    muted = self._api.toggle_master_mute()
                    self._api._push('master_mute', {'mute': muted})
                elif button_index == self._config['SHOW_HIDE_BUTTON_INDEX']:
                    if self._api._visible:
                        self._api.hide_window()
                    else:
                        self._api.show_window()
                self._api._push('notification', {'message': f'Button {button_index} pressed'})
            self._last_button_values[button_index] = button_value

    def on_message(self, message):
        """Called by SerialReader to forward informational/error messages."""
        self._api._push('notification', {'message': message})
