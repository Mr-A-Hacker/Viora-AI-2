import sys
import cv2
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.screen import MDScreen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture

import computer_vision

# Force a portrait resolution
Window.size = (480, 800)

KV = '''
MDScreen:
    md_bg_color: 0, 0, 0, 1

    MDFloatLayout:
        # LAYER 1: The Camera Display (Background)
        Image:
            id: cam_display
            source: "" 
            allow_stretch: True
            keep_ratio: False 
            size_hint: 1, 1
            pos_hint: {"center_x": 0.5, "center_y": 0.5}

        # LAYER 2: Status Label
        MDLabel:
            id: status_label
            text: "Status: Ready"
            halign: "center"
            pos_hint: {"center_x": 0.5, "top": 0.96}
            size_hint: 0.8, None
            height: "40dp"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 0.6
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15]

        # LAYER 3: Controls
        MDBoxLayout:
            orientation: "vertical"
            pos_hint: {"center_x": 0.5, "y": 0.03}
            size_hint: 0.9, None
            height: "140dp"
            spacing: "10dp"

            # Row 1: Mode Selectors
            MDBoxLayout:
                orientation: "horizontal"
                spacing: "15dp"
                MDButton:
                    style: "filled"
                    md_bg_color: 0.2, 0.8, 0.2, 1
                    size_hint_x: 0.5
                    on_release: app.switch_mode("detect")
                    MDButtonText:
                        text: "DETECT"
                        pos_hint: {"center_x": 0.5, "center_y": 0.5}
                MDButton:
                    style: "filled"
                    md_bg_color: 0.6, 0.2, 0.8, 1
                    size_hint_x: 0.5
                    on_release: app.switch_mode("pose")
                    MDButtonText:
                        text: "POSE"
                        pos_hint: {"center_x": 0.5, "center_y": 0.5}

            # Row 2: Stream / Stop
            MDBoxLayout:
                orientation: "horizontal"
                spacing: "15dp"
                MDButton:
                    style: "filled"
                    md_bg_color: 0, 0.5, 1, 1
                    size_hint_x: 0.5
                    on_release: app.switch_mode("stream")
                    MDButtonText:
                        text: "STREAM"
                        pos_hint: {"center_x": 0.5, "center_y": 0.5}
                MDButton:
                    style: "filled"
                    md_bg_color: 1, 0.2, 0.2, 1
                    size_hint_x: 0.5
                    on_release: app.switch_mode("stop")
                    MDButtonText:
                        text: "STOP"
                        pos_hint: {"center_x": 0.5, "center_y": 0.5}
'''

class AICameraApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_mode = "None"
        self.update_event = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def on_start(self):
        self.update_event = Clock.schedule_interval(self.update_texture, 1.0 / 30.0)
        self.switch_mode("stream")

    def on_stop(self):
        if self.update_event:
            self.update_event.cancel()
        computer_vision.stop_task()

    def update_texture(self, dt):
        frame = computer_vision.get_latest_frame()
        
        if frame is not None:
            # 1. ROTATE (Landscape Camera -> Portrait Screen)
            try:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            except Exception:
                pass

            # 2. COLOR CORRECTION
            # The pipeline now outputs RGB directly to fix the blue tint.
            # So we DO NOT use cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) here.
            # We treat the frame as already RGB.
            
            # 3. TEXTURE CREATION
            h, w = frame.shape[:2]
            texture = Texture.create(size=(w, h), colorfmt='rgb')
            texture.blit_buffer(frame.flatten(), colorfmt='rgb', bufferfmt='ubyte')
            
            self.root.ids.cam_display.texture = texture

    def switch_mode(self, mode):
        status_label = self.root.ids.status_label
        if mode == self.active_mode: return

        status_label.text = f"Switching to {mode.upper()}..."
        if mode == "stop":
            computer_vision.stop_task()
            status_label.text = "Status: Stopped"
            self.active_mode = "stop"
            return

        target_func = None
        if mode == "stream": target_func = computer_vision.run_raw_camera_app
        elif mode == "detect": target_func = computer_vision.run_detection_app
        elif mode == "pose": target_func = computer_vision.run_pose_app

        if target_func:
            computer_vision.start_task(target_func)
            status_label.text = f"Active: {mode.upper()}"
            self.active_mode = mode

if __name__ == "__main__":
    AICameraApp().run()