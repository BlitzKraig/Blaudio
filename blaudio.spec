# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Collect everything pywebview needs: Python modules, data files (JS bridge,
# .NET WebView2 host assemblies, DLLs), and hidden imports.  Without this,
# pywebview's Edge WebView2 backend falls back silently and the JS bridge
# never initialises — evaluate_js always throws "Main window failed to start"
# and window.pywebview.api is never defined in JS.
webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')

a = Analysis(
    ['blaudio.py'],
    pathex=[],
    binaries=webview_binaries,
    datas=[('resources', 'resources'), ('ui/web', 'ui/web')] + webview_datas,
    hiddenimports=[
        'pystray._win32',
        'PIL.Image',
        'PIL.IcoImagePlugin',
        # pycaw / comtypes — COM audio interfaces used throughout the app
        'pycaw',
        'pycaw.pycaw',
        'comtypes',
        'comtypes.client',
        'comtypes.automation',
        # pyserial — port enumeration for device detection
        'serial.tools.list_ports',
        'serial.tools',
    ] + webview_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_comtypes.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='blaudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/storm.ico',
    version='version.txt'
)
