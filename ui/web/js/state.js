'use strict';

// ── Mock state for browser-only development ──────────────────────────────────
const MOCK_STATE = {
  version: 'v0.1.2',
  masterVolume: 50,
  masterMute: false,
  sliders: [
    { name: 'Chrome',  volume: 70, mute: false, knob_index: 1, app_names: ['chrome.exe'] },
    { name: 'Discord', volume: 52, mute: false, knob_index: 3, app_names: ['Discord.exe'] },
    { name: 'Spotify', volume: 32, mute: false, knob_index: 2, app_names: ['Spotify.exe'] },
  ],
  theme: 'dark',
  layout: 'vertical',
}

// ── Blaudio namespace (extended by subsequent JS modules) ────────────────────
window.blaudio = {
  state: {
    version: '',
    masterVolume: 50,
    masterMute: false,
    sliders: [],
  },
}
