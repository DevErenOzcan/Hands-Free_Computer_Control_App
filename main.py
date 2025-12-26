import cv2
import mediapipe as mp
import pyautogui
import math
import time
import tkinter as tk
import threading
import numpy as np

# PyAutoGUI Safety Failsafe
pyautogui.FAILSAFE = False

class FaceMeshDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def find_face_mesh(self, img, draw=True):
        self.img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.face_mesh.process(self.img_rgb)
        faces = []
        if self.results.multi_face_landmarks:
            for face_landmarks in self.results.multi_face_landmarks:
                face = []
                for id, lm in enumerate(face_landmarks.landmark):
                    ih, iw, ic = img.shape
                    x, y = int(lm.x * iw), int(lm.y * ih)
                    face.append([x, y])
                faces.append(face)
        return faces

class MouseController:
    def __init__(self, sensitivity=3.0, smoothing=5):
        self.screen_w, self.screen_h = pyautogui.size()
        self.sensitivity = sensitivity
        self.smoothing = smoothing
        self.prev_x, self.prev_y = 0, 0
        self.history_x = []
        self.history_y = []

    def move_cursor(self, x, y, frame_center):
        # Calculate delta from center (Nose position vs Frame Center)
        # Note: Inverted x because of camera flip
        dx = x - frame_center[0]
        dy = y - frame_center[1]

        # Apply Sensitivity
        target_x = self.screen_w / 2 + (dx * self.sensitivity * 5)
        target_y = self.screen_h / 2 + (dy * self.sensitivity * 5)

        # Clamp to screen
        target_x = max(0, min(self.screen_w, target_x))
        target_y = max(0, min(self.screen_h, target_y))

        # Smoothing (Moving Average)
        self.history_x.append(target_x)
        self.history_y.append(target_y)

        if len(self.history_x) > self.smoothing:
            self.history_x.pop(0)
            self.history_y.pop(0)

        avg_x = sum(self.history_x) / len(self.history_x)
        avg_y = sum(self.history_y) / len(self.history_y)

        try:
            pyautogui.moveTo(avg_x, avg_y)
        except pyautogui.FailSafeException:
            pass

        return avg_x, avg_y

    def click(self, button='left'):
        pyautogui.click(button=button)

    def scroll(self, direction):
        # direction > 0: UP, direction < 0: DOWN
        pyautogui.scroll(direction * 50) # Scroll unit

class VirtualKeyboard(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.root = None
        self.running = True
        self.visible = False
        self.keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'Back'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'Enter'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', '"'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Space']
        ]
        self.buttons = {}
        self.hover_key = None
        self.hover_start_time = 0
        self.dwell_time = 1.0 # Seconds to trigger key
        self.cursor_pos = (0, 0)
        self.screen_w, self.screen_h = pyautogui.size()
        self.lock = threading.Lock()

    def run(self):
        # Running Tkinter in a separate thread can be problematic, but requested structure
        # implies decoupling. We'll try to keep it safe by only using local root.
        self.root = tk.Tk()
        self.root.title("Virtual Keyboard")

        # Make transparent and always on top
        self.root.wait_visibility(self.root)
        self.root.attributes('-alpha', 0.7)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True) # Remove window decorations

        # Position at bottom of screen
        kb_height = 300
        self.root.geometry(f"{self.screen_w}x{kb_height}+0+{self.screen_h - kb_height}")

        # Layout
        for r, row_keys in enumerate(self.keys):
            self.root.grid_rowconfigure(r, weight=1)
            for c, key_char in enumerate(row_keys):
                self.root.grid_columnconfigure(c, weight=1)
                btn = tk.Label(self.root, text=key_char, font=("Arial", 20), bg="black", fg="white", relief="raised")
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                self.buttons[key_char] = btn

        self.update_loop()
        self.root.mainloop()

    def update_loop(self):
        if not self.running:
            self.root.destroy()
            return

        with self.lock:
            current_visible = self.visible
            current_cursor = self.cursor_pos

        if current_visible:
            self.root.deiconify()
            self.check_hover(current_cursor)
        else:
            self.root.withdraw()

        self.root.after(50, self.update_loop)

    def check_hover(self, cursor_pos):
        # Convert screen cursor pos to keyboard local pos
        kb_x = self.root.winfo_x()
        kb_y = self.root.winfo_y()
        cx, cy = cursor_pos

        local_x = cx - kb_x
        local_y = cy - kb_y

        found_hover = None

        for key, btn in self.buttons.items():
            bx = btn.winfo_x()
            by = btn.winfo_y()
            bw = btn.winfo_width()
            bh = btn.winfo_height()

            if bx <= local_x <= bx + bw and by <= local_y <= by + bh:
                found_hover = key
                btn.config(bg="gray")
            else:
                btn.config(bg="black")

        if found_hover:
            if self.hover_key == found_hover:
                if time.time() - self.hover_start_time > self.dwell_time:
                    self.press_key(found_hover)
                    self.hover_key = None # Reset
            else:
                self.hover_key = found_hover
                self.hover_start_time = time.time()
        else:
            self.hover_key = None

    def press_key(self, key):
        print(f"Key Pressed: {key}")
        # Visual feedback
        if key in self.buttons:
            self.buttons[key].config(bg="green")
            self.root.update()
            time.sleep(0.1)

        if key == 'Space':
            pyautogui.press('space')
        elif key == 'Enter':
            pyautogui.press('enter')
        elif key == 'Back':
            pyautogui.press('backspace')
        else:
            pyautogui.write(key.lower())

    def set_visibility(self, visible):
        with self.lock:
            self.visible = visible

    def set_cursor(self, x, y):
        with self.lock:
            self.cursor_pos = (x, y)

    def stop(self):
        self.running = False


class Application:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.detector = FaceMeshDetector()
        self.mouse = MouseController()

        # Check for X11/Headless environment to avoid crashes on keyboard init
        # For this environment we will proceed, assuming a display might be attached or simulated
        # But wrapped in try-except in actual run might be safer.
        self.keyboard = VirtualKeyboard()
        self.keyboard.start()

        self.mode = "MOUSE" # or "KEYBOARD"

        # Blink config
        self.EAR_THRESHOLD = 0.25 # Calibration needed per user maybe
        self.BLINK_CONSEC_FRAMES = 2

        self.blink_counter_l = 0
        self.blink_counter_r = 0
        self.blink_counter_both = 0
        self.total_blinks = 0

        # Mode switch config
        self.last_blink_time = 0
        self.double_blink_window = 1.0 # seconds
        self.blink_sequence = [] # timestamps of blinks

        # Scroll config
        self.scroll_active = False
        self.last_head_y = 0

        # Iris/Nose tracking
        self.frame_center = (0,0)

        # Calibration (Simple center reset)
        self.calibrated_center = None

    def calculate_ear(self, eye_points):
        # Vertical distances
        A = math.hypot(eye_points[1][0] - eye_points[5][0], eye_points[1][1] - eye_points[5][1])
        B = math.hypot(eye_points[2][0] - eye_points[4][0], eye_points[2][1] - eye_points[4][1])
        # Horizontal distance
        C = math.hypot(eye_points[0][0] - eye_points[3][0], eye_points[0][1] - eye_points[3][1])
        ear = (A + B) / (2.0 * C)
        return ear

    def run(self):
        while True:
            success, img = self.cap.read()
            if not success:
                break

            img = cv2.flip(img, 1) # Mirror view
            h, w, c = img.shape
            self.frame_center = (w//2, h//2)

            # Use nose tip as center for calibration if not set
            if self.calibrated_center is None:
                self.calibrated_center = (w//2, h//2)

            faces = self.detector.find_face_mesh(img)

            if faces:
                face = faces[0]

                # Landmarks indices
                # Left Eye: 33, 160, 158, 133, 153, 144 (approx for EAR)
                # Right Eye: 362, 385, 387, 263, 373, 380
                # Nose Tip: 1

                left_eye_indices = [33, 160, 158, 133, 153, 144]
                right_eye_indices = [362, 385, 387, 263, 373, 380]

                left_eye = [face[i] for i in left_eye_indices]
                right_eye = [face[i] for i in right_eye_indices]
                nose_tip = face[1] # Tip of nose

                ear_left = self.calculate_ear(left_eye)
                ear_right = self.calculate_ear(right_eye)

                # --- LOGIC ---

                # 1. Blink Detection
                left_closed = ear_left < self.EAR_THRESHOLD
                right_closed = ear_right < self.EAR_THRESHOLD
                both_closed = left_closed and right_closed

                current_time = time.time()

                # --- BOTH EYES ---
                if both_closed:
                    self.blink_counter_both += 1
                else:
                    # Detect blink end (Falling edge of closed signal)
                    if self.blink_counter_both > self.BLINK_CONSEC_FRAMES:
                        # Valid Double Blink candidate OR Scroll initiation
                        if not self.scroll_active: # If we were not scrolling
                             # Check if it was a quick blink (potential mode switch)
                             # or if it was held (scroll setup - handled separately below)
                             self.register_blink(current_time)
                    self.blink_counter_both = 0

                # --- SCROLLING ---
                # Trigger: Both eyes closed AND head moves vertically
                if both_closed:
                     if self.mode == "MOUSE":
                         self.handle_scrolling(nose_tip)
                else:
                    self.scroll_active = False # Reset scroll if eyes open


                # --- SINGLE EYE CLICKS ---
                # Only process single eye clicks if we are NOT in the middle of a both-eye blink
                # and we are NOT scrolling

                if not both_closed and not self.scroll_active:
                    # Left Click
                    if left_closed and not right_closed:
                        self.blink_counter_l += 1
                    else:
                        if self.blink_counter_l > self.BLINK_CONSEC_FRAMES:
                            if self.mode == "MOUSE":
                                # Logic to avoid false positive if it was actually part of a double blink:
                                # This is hard without delay.
                                # Simpler approach: If "both_closed" happened recently, ignore single blinks?
                                # Or: Rely on "both_closed" taking precedence in state.
                                # Given the frame-by-frame, if both close, 'left_closed' is also true.
                                # So 'left_closed and not right_closed' ensures mutual exclusivity.
                                # Thus, if both close, this block is SKIPPED.
                                # So this block only runs if ONLY left eye is closed (Wink).
                                self.mouse.click('left')
                        self.blink_counter_l = 0

                    # Right Click
                    if right_closed and not left_closed:
                        self.blink_counter_r += 1
                    else:
                        if self.blink_counter_r > self.BLINK_CONSEC_FRAMES:
                            if self.mode == "MOUSE":
                                self.mouse.click('right')
                        self.blink_counter_r = 0

                # Check Double Blink for Mode Switch
                # We register 'both' blinks.
                # If we get 2 'both' blinks in window -> Switch Mode
                if self.check_mode_switch():
                    print("Double Blink Detected! Switching Mode.")
                    self.mode = "KEYBOARD" if self.mode == "MOUSE" else "MOUSE"
                    self.blink_sequence = [] # Reset


                # 2. Movement
                if self.mode == "MOUSE":
                    # Map Nose Tip to Screen
                    # Using calibration center
                    current_mx, current_my = self.mouse.move_cursor(nose_tip[0], nose_tip[1], self.calibrated_center)
                    self.keyboard.set_visibility(False)

                elif self.mode == "KEYBOARD":
                    # In keyboard mode, we still move cursor to hover keys
                    current_mx, current_my = self.mouse.move_cursor(nose_tip[0], nose_tip[1], self.calibrated_center)
                    self.keyboard.set_cursor(current_mx, current_my)
                    self.keyboard.set_visibility(True)

                # Visual Feedback
                cv2.circle(img, (nose_tip[0], nose_tip[1]), 5, (0, 255, 0), -1)
                cv2.putText(img, f"Mode: {self.mode}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(img, f"EAR: {ear_left:.2f} {ear_right:.2f}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            cv2.imshow("Head Tracker", img)

            # Calibration shortcut 'c'
            key = cv2.waitKey(1)
            if key == ord('c') and faces:
                self.calibrated_center = faces[0][1] # Set center to current nose pos
                print("Calibrated Center")
            if key == ord('q'):
                break

        self.keyboard.stop()
        self.cap.release()
        cv2.destroyAllWindows()

    def register_blink(self, timestamp):
        # Add blink timestamp
        self.blink_sequence.append(timestamp)
        # Clean old blinks
        self.blink_sequence = [t for t in self.blink_sequence if timestamp - t < self.double_blink_window]

    def check_mode_switch(self):
        # If we have 2 blinks in the window
        return len(self.blink_sequence) >= 2

    def handle_scrolling(self, nose_pos):
        # If head moves vertically while eyes closed
        current_y = nose_pos[1]

        if not self.scroll_active:
            self.scroll_active = True
            self.last_head_y = current_y
            return

        diff = current_y - self.last_head_y

        # Threshold for movement
        if abs(diff) > 5:
            # Inverted Control: Head DOWN (diff > 0) -> Scroll UP (direction > 0)
            direction = 1 if diff > 0 else -1
            self.mouse.scroll(direction)
            self.last_head_y = current_y

if __name__ == "__main__":
    app = Application()
    app.run()
