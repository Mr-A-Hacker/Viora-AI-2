import os
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.core.window import Window

# Set window size for desktop testing (matches your 480x800 screen)
# This won't affect the Pi's fullscreen display
Window.size = (480, 800)

class PocketAI_GUI(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"

        screen = MDScreen()
        layout = MDBoxLayout(
            orientation='vertical',
            padding="20dp",
            spacing="15dp"
        )

        self.status_label = MDLabel(
            text="POCKET AI",
            halign="center",
            font_style="H4",
            size_hint_y=None,
            height="80dp",
            theme_text_color="Primary"
        )

        # FIX: We remove md_bg_color from the constructor 
        # to prevent the "NoneType" canvas error.
        self.detection_display = MDLabel(
            text="Waiting for Camera...",
            halign="center",
            theme_text_color="Secondary",
            font_style="Subtitle1",
        )
        
        # Optionally set the background color safely after initialization
        # or use a Card for better look on a small screen:
        from kivymd.uix.card import MDCard
        display_container = MDCard(
            md_bg_color=(0.15, 0.15, 0.15, 1),
            padding="10dp",
            radius=[15, 15, 15, 15]
        )
        display_container.add_widget(self.detection_display)

        btn_start = MDRaisedButton(
            text="START AI",
            pos_hint={"center_x": .5},
            size_hint=(0.8, None),
            height="60dp",
            on_release=self.start_detection
        )

        btn_stop = MDRaisedButton(
            text="STOP AI",
            pos_hint={"center_x": .5},
            size_hint=(0.8, None),
            height="60dp",
            md_bg_color=(0.8, 0.2, 0.2, 1),
            on_release=self.stop_detection
        )

        layout.add_widget(self.status_label)
        layout.add_widget(display_container) # Add the card instead of just the label
        layout.add_widget(btn_start)
        layout.add_widget(btn_stop)

        screen.add_widget(layout)
        return screen
    
    def start_detection(self, instance):
        self.detection_display.text = "Scanning..."
        print("Start command sent")

    def stop_detection(self, instance):
        self.detection_display.text = "System Idling"
        print("Stop command sent")

if __name__ == "__main__":
    PocketAI_GUI().run()