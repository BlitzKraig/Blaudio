# Blaudio
Grouped Windows audio control with custom hardware support

This is the first thing I've ever built with Python - the structure is not ideal. Improvements welcome.

## Description
Inspired by Deej, Blaudio is designed to work with custom Arduino hardware.

Assign programs to sliders, and control their volume with the Blaudio box, or directly via the GUI.

Automatically handles re-connection silently if your computer is put to sleep.

Includes a custom GUI to assign knobs to sliders, or control sliders directly.

## Installation
### For developers
WIP
### For consumers
Simply unzip the latest release from the Releases section into a folder of your choice.

You may need to whitelist the exe in Windows Defender, since we use PyInstaller to create the bundle.

Edit blaudio_config.json with your devices COM port index (can be found in Device Manager or Arduino IDE).

Run the exe normally.

Consider adding the exe as a Startup App by creating a shortcut in USER_DIR\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup

NOTE: You can navigate here by typing `shell:startup` in Run (Windows Key + R)

## Hardware
An Arduino Nano is recommended. An ESP32 can be used, but suffers from more significant issues when your computer is put to sleep.

With a Nano, we can easily re-establish the serial connection without resetting the hardware.

An in-depth build guide is planned.

### Installing or Updating hardware
From the release, open Arduino/Config.h in the text editor of your choice (or Arduino/Nano/BlaudioNano/Config.h from source)

Update `KNOB_COUNT`, `analogInputs`, `BUTTON_COUNT` and `digitalInputs` to match your hardware configuration.

NOTE: `analogInputs` and `digitalInputs` are ordered. The default sketch (ino file) is set up to work with the original Blaudio prototype which I use for development.

Your setup is likely:

```
const int KNOB_COUNT = 5;
const int analogInputs[KNOB_COUNT] = {A1, A2, A3, A4, A5};
const int BUTTON_COUNT = 6;
const int digitalInputs[BUTTON_COUNT] = {2, 3, 4, 5, 6, 7};
```

In case of future updates, you might want to copy this Config.h file somewhere safe so you can re-use it in future. Simply replace the Config.h in future releases with your own version (assuming no breaking updates)

Install and open the [Arduino IDE](https://www.arduino.cc/en/software)

From the release, open Arduino/BlaudioNano.ino in the Arduino IDE (or Arduino/Nano/BlaudioNano/BlaudioNano.ino from source)

Connect your Blaudio box

Ensure your board is selected in the dropdown

Click Upload

You can open the Serial Monitor to check your hardware. Ensure the Serial Monitor tool is closed before attempting to run Blaudio.

## Contributing
WIP