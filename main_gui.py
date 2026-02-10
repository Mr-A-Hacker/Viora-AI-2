import sys
import multiprocessing
import os
from kivy.lang import Builder
from kivymd.app import MDApp
# Compatible with KivyMD 2.0+
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.screen import MDScreen
from kivy.core.window import Window

# Import your working logic from computer_vision.py
# Ensure computer_vision.py is in the same directory!
import computer_vision

# Set window size for 4.3" screen (Portrait Mode)
Window.size = (480, 800)

# -----------------------------------------------------------------------------------------------
# KivyMD GUI Interface (Portrait Layout)
# -----------------------------------------------------------------------------------------------

KV = '''
MDScreen:
    # Set background to transparent (0,0,0,0) so the video overlay (if behind) is visible.
    # If the video is a separate layer, this helps avoid blocking it.
    md_bg_color: 0, 0, 0, 0

    # --- Top Status Bar ---
    MDLabel:
        id: status_label
        text: "Status: Ready"
        halign: "center"
        pos_hint: {"center_x": 0.5, "top": 0.98}
        size_hint: 1, 0.05
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        font_style: "Title"
        role: "small"
        
        # Add a semi-transparent background to the label so text pops
        canvas.before:
            Color:
                rgba: 0, 0, 0, 0.5
            Rectangle:
                pos: self.pos
                size: self.size

    # --- Bottom Control Panel ---
    # We place controls at the bottom for a "Phone-style" portrait layout
    MDBoxLayout:
        orientation: "vertical"
        pos_hint: {"center_x": 0.5, "y": 0.02}
        size_hint: 0.9, 0.25
        spacing: "15dp"

        # Row 1: STREAM and STOP
        MDBoxLayout:
            orientation: "horizontal"
            spacing: "15dp"
            
            MDButton:
                style: "filled"
                theme_bg_color: "Custom"
                md_bg_color: 0, 0.5, 1, 1
                size_hint_x: 0.5
                size_hint_y: 1
                on_release: app.switch_mode("stream")
                
                MDButtonText:
                    text: "STREAM"
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}

            MDButton:
                style: "filled"
                theme_bg_color: "Custom"
                md_bg_color: 1, 0.2, 0.2, 1
                size_hint_x: 0.5
                size_hint_y: 1
                on_release: app.switch_mode("stop")

                MDButtonText:
                    text: "STOP"
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}

        # Row 2: DETECT and POSE
        MDBoxLayout:
            orientation: "horizontal"
            spacing: "15dp"

            MDButton:
                style: "filled"
                theme_bg_color: "Custom"
                md_bg_color: 0.2, 0.8, 0.2, 1
                size_hint_x: 0.5
                size_hint_y: 1
                on_release: app.switch_mode("detect")

                MDButtonText:
                    text: "DETECT"
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}

            MDButton:
                style: "filled"
                theme_bg_color: "Custom"
                md_bg_color: 0.6, 0.2, 0.8, 1
                size_hint_x: 0.5
                size_hint_y: 1
                on_release: app.switch_mode("pose")
                
                MDButtonText:
                    text: "POSE"
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}
'''

class AICameraApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_process = None
        self.active_mode = "None"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

    def on_start(self):
        # Auto-start the raw stream
        self.switch_mode("stream")

    def on_stop(self):
        self.kill_active_process()

    def kill_active_process(self):
        if self.current_process and self.current_process.is_alive():
            # 1. Try graceful termination first (SIGTERM)
            self.current_process.terminate()
            
            # 2. Wait 1 second for the process to clean up and exit
            self.current_process.join(timeout=1)
            
            # 3. If it's still alive (stuck), FORCE KILL it (SIGKILL)
            if self.current_process.is_alive():
                print("Process refused to close. Forcing kill...")
                self.current_process.kill()
                self.current_process.join()  # Ensure it is fully gone
            
            self.current_process = None

    def switch_mode(self, mode):
        status_label = self.root.ids.status_label
        
        if mode == self.active_mode:
            status_label.text = f"Already in {mode.upper()} mode"
            return

        status_label.text = f"Switching to {mode.upper()}..."
        self.kill_active_process()

        if mode == "stop":
            status_label.text = "Status: Stopped"
            self.active_mode = "stop"
            return

        # Map modes to the functions in computer_vision.py
        target_func = None
        if mode == "stream":
            target_func = computer_vision.run_raw_camera_app
        elif mode == "detect":
            target_func = computer_vision.run_detection_app
        elif mode == "pose":
            target_func = computer_vision.run_pose_app

        if target_func:
            self.current_process = multiprocessing.Process(target=target_func)
            self.current_process.daemon = True  # <--- Add this line
            self.current_process.start()
            status_label.text = f"Status: Running {mode.upper()}"
            self.active_mode = mode

if __name__ == "__main__":
    AICameraApp().run()