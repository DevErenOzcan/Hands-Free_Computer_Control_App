# Hands-Free Computer Control Application

<img width="1920" height="1080" alt="Screenshot from 2026-01-02 00-19-36" src="https://github.com/user-attachments/assets/f8c66e81-bc2d-41a4-80f9-360e164b9ecf" />


This application allows you to control your mouse and keyboard using head movements and eye gestures.

## Features

-   **Mouse Mode:**
    -   **Cursor Movement:** Track head orientation (nose tip).
    -   **Left Click:** Left Eye Blink.
    -   **Right Click:** Right Eye Blink.
    -   **Scroll:** Close both eyes and move head vertically (Inverted control: Head Down -> Scroll Up).
-   **Keyboard Mode:**
    -   Transparent virtual keyboard.
    -   Hover over keys to type.
-   **Mode Switching:** Double blink to toggle between Mouse and Keyboard modes.

## Requirements

-   Python 3.x
-   Webcam

## Installation

1.  Install the required packages:

```bash
pip install -r requirements.txt

```
2. Run the application:

```bash
python main.py

```

## Usage

1. **Calibration:** When the application starts, it calibrates the "center" position based on your initial head position. You can press `c` at any time to recalibrate the center.
2. **Mouse Control:** Move your head to move the cursor.
3. **Clicking:** Blink your left eye for left-click, right eye for right-click.
4. **Scrolling:** Close both eyes and move your head up or down.
5. **Keyboard:** Perform a double blink (two rapid blinks) to bring up the virtual keyboard. Move the cursor over a key and hold it there for a second to press it. Double blink again to return to Mouse Mode.
6. **Quit:** Press `q` to exit the application.
