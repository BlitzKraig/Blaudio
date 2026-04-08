'use strict';
// Single source of truth for theme definitions.
// Also read by api.py — keep the array literal strictly valid JSON
// (double-quoted strings, no trailing commas, no comments inside the array).
//
// Each theme has:
//   id, label, bg, accent  — metadata (Python reads id + bg)
//   vars                   — full set of CSS custom properties
//   effects (optional)     — array of extra CSS rule strings injected dynamically
window.BLAUDIO_THEMES = [
  {
    "id": "dark",
    "label": "Dark",
    "bg": "#1a1a1a",
    "accent": "#9C27B0",
    "vars": {
      "--bg-primary":     "#1a1a1a",
      "--bg-secondary":   "#222222",
      "--bg-hover":       "#2a2a2a",
      "--bg-toolbar":     "#111111",
      "--bg-input":       "#2d2d2d",
      "--accent":         "#9C27B0",
      "--accent-rgb":     "156, 39, 176",
      "--accent-hover":   "#AB47BC",
      "--danger":         "#e53935",
      "--text-primary":   "#e0e0e0",
      "--text-secondary": "#9e9e9e",
      "--text-muted":     "#4a4a4a",
      "--divider":        "#2e2e2e",
      "--slider-track":   "#3d3d3d",
      "--vu-low":         "#00e676",
      "--vu-mid":         "#ffee58",
      "--vu-hi":          "#ff9800",
      "--vu-peak":        "#f44336",
      "--vu-tick":        "rgba(255,255,255,0.9)",
      "--vu-tick-glow":   "rgba(255,255,255,0.5)"
    }
  },
  {
    "id": "light",
    "label": "Light",
    "bg": "#f4f4f5",
    "accent": "#9C27B0",
    "vars": {
      "--bg-primary":     "#f4f4f5",
      "--bg-secondary":   "#ffffff",
      "--bg-hover":       "#eaeaec",
      "--bg-toolbar":     "#e2e2e6",
      "--bg-input":       "#ededf0",
      "--accent":         "#9C27B0",
      "--accent-rgb":     "156, 39, 176",
      "--accent-hover":   "#7B1FA2",
      "--danger":         "#d32f2f",
      "--text-primary":   "#1a1a1a",
      "--text-secondary": "#5a5a5a",
      "--text-muted":     "#b4b4b4",
      "--divider":        "#d4d4d8",
      "--slider-track":   "#c8c8cc",
      "--vu-low":         "#00c853",
      "--vu-mid":         "#f9a825",
      "--vu-hi":          "#e65100",
      "--vu-peak":        "#c62828",
      "--vu-tick":        "rgba(30,30,30,0.85)",
      "--vu-tick-glow":   "rgba(0,0,0,0.2)"
    },
    "effects": [
      ".menu-entry:hover                 { background: rgba(0,0,0,0.06); }",
      ".menu-drop                        { box-shadow: 0 8px 24px rgba(0,0,0,0.12); }",
      ".menu-action:hover:not(:disabled) { background: rgba(var(--accent-rgb),0.1); }",
      ".slider-col:hover                 { background: rgba(0,0,0,0.04); }",
      ".icon-btn:hover                   { background: rgba(0,0,0,0.07); }",
      ".btn-flat:hover                   { background: rgba(0,0,0,0.06); }",
      ".app-entry:hover                  { background: rgba(0,0,0,0.04); }",
      "#overlay                          { background: rgba(0,0,0,0.35); }",
      "#settings-overlay                 { background: rgba(0,0,0,0.35); }"
    ]
  },
  {
    "id": "ocean",
    "label": "Ocean",
    "bg": "#0d1b2a",
    "accent": "#00BCD4",
    "vars": {
      "--bg-primary":     "#0d1b2a",
      "--bg-secondary":   "#0f2236",
      "--bg-hover":       "#163047",
      "--bg-toolbar":     "#080e18",
      "--bg-input":       "#163047",
      "--accent":         "#00BCD4",
      "--accent-rgb":     "0, 188, 212",
      "--accent-hover":   "#26C6DA",
      "--danger":         "#ef5350",
      "--text-primary":   "#d6eeff",
      "--text-secondary": "#6aabcc",
      "--text-muted":     "#2a4a6a",
      "--divider":        "#18354f",
      "--slider-track":   "#18354f",
      "--vu-low":         "#00e5ff",
      "--vu-mid":         "#fff176",
      "--vu-hi":          "#ff9800",
      "--vu-peak":        "#ef5350",
      "--vu-tick":        "rgba(255,255,255,0.9)",
      "--vu-tick-glow":   "rgba(255,255,255,0.5)"
    }
  },
  {
    "id": "synthwave",
    "label": "Synthwave",
    "bg": "#0a0010",
    "accent": "#e040fb",
    "vars": {
      "--bg-primary":     "#0a0010",
      "--bg-secondary":   "#110022",
      "--bg-hover":       "#1d0038",
      "--bg-toolbar":     "#050008",
      "--bg-input":       "#16002a",
      "--accent":         "#e040fb",
      "--accent-rgb":     "224, 64, 251",
      "--accent-hover":   "#ea80fc",
      "--danger":         "#ff5370",
      "--text-primary":   "#f0e0ff",
      "--text-secondary": "#b080d0",
      "--text-muted":     "#5a2878",
      "--divider":        "#280050",
      "--slider-track":   "#200040",
      "--vu-low":         "#00ff9f",
      "--vu-mid":         "#f9f871",
      "--vu-hi":          "#e040fb",
      "--vu-peak":        "#ff1744",
      "--vu-tick":        "rgba(255,255,255,0.9)",
      "--vu-tick-glow":   "rgba(255,255,255,0.5)"
    },
    "effects": [
      "body::before { content:''; position:fixed; inset:0; background:repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(224,64,251,0.018) 2px, rgba(224,64,251,0.018) 4px); pointer-events:none; z-index:999; }",
      ".master-label { text-shadow: 0 0 8px var(--accent), 0 0 20px rgba(var(--accent-rgb),0.6); }",
      ".noUi-handle { box-shadow: 0 0 8px rgba(var(--accent-rgb),0.9), 0 0 22px rgba(var(--accent-rgb),0.5) !important; }",
      ".noUi-handle:hover { box-shadow: 0 0 12px rgba(var(--accent-rgb),1), 0 0 30px rgba(var(--accent-rgb),0.7) !important; }",
      "#menubar { border-bottom-color: rgba(var(--accent-rgb),0.5); box-shadow: 0 1px 16px rgba(var(--accent-rgb),0.15); }",
      "#toolbar { border-top-color: rgba(var(--accent-rgb),0.5); box-shadow: -0 -1px 16px rgba(var(--accent-rgb),0.15); }",
      ".btn-accent { box-shadow: 0 0 12px rgba(var(--accent-rgb),0.5); }",
      ".btn-accent:hover { box-shadow: 0 0 22px rgba(var(--accent-rgb),0.75); }",
      "#toast { box-shadow: 0 0 18px rgba(var(--accent-rgb),0.7); }"
    ]
  },
  {
    "id": "glitchmob",
    "label": "GLITCH",
    "bg": "#00ff11",
    "accent": "#ff0000",
    "vars": {
      "--bg-primary":     "#0a0a0a",
      "--bg-secondary":   "#111111",
      "--bg-hover":       "#1a1a1a",
      "--bg-toolbar":     "#050505",
      "--bg-input":       "#151515",
      "--accent":         "#ff0000",
      "--accent-rgb":     "255, 0, 0",
      "--accent-hover":   "#ff3333",
      "--danger":         "#ff0000",
      "--text-primary":   "#00ff11",
      "--text-secondary": "#00bb0d",
      "--text-muted":     "#005505",
      "--divider":        "#002200",
      "--slider-track":   "#003300",
      "--vu-low":         "#00ff11",
      "--vu-mid":         "#ffff00",
      "--vu-hi":          "#ff6600",
      "--vu-peak":        "#ff0000",
      "--vu-tick":        "rgba(0,255,17,0.9)",
      "--vu-tick-glow":   "rgba(0,255,17,0.5)"
    },
    "effects": [
      ".master-label { text-shadow: 0 0 8px #00ff11, 0 0 20px rgba(0,255,17,0.6); font-family: monospace; }",
      ".noUi-handle { box-shadow: 0 0 6px rgba(255,0,0,0.8), 0 0 16px rgba(255,0,0,0.4) !important; }",
      ".noUi-handle:hover { box-shadow: 0 0 10px rgba(255,0,0,1), 0 0 24px rgba(255,0,0,0.6) !important; }"
    ]
  }
];
