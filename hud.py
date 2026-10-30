"""
hud.py - DirectGUI Dashboard & On-Screen Vehicle Controls for RealDrive
-----------------------------------------------------------------------
This module manages all 2D screen interface elements using Panda3D's DirectGUI:

1. Digital Telemetry Dashboard:
   - Real-time digital speedometer (KM/H)
   - Dynamic gear indicator badge (D, N, R, P) with contextual color changes
   - Current camera mode display
   - Intersection Traffic Signal status badge (GREEN / YELLOW / RED)
   - Impact & Crash Alert warning banner

2. Interactive On-Screen Driving Controls:
   - Accelerate / Gas button
   - Brake / Reverse button
   - Steer Left and Steer Right buttons
   - Supports mouse press-and-hold (B1PRESS / B1RELEASE / WITHOUT) for smooth
     on-screen vehicle operation alongside keyboard controls.
   - Camera Mode toggle button
   - Vehicle Reset button
"""

from direct.gui.DirectGui import (
    DirectFrame,
    DirectLabel,
    DirectButton,
    DGG,
)
from panda3d.core import Vec4, TextNode


class HUD:
    """Manages the 2D cockpit dashboard, traffic signal telemetry, and on-screen controls."""

    def __init__(self, on_camera_toggle_callback=None, on_reset_callback=None):
        """
        Initializes the DirectGUI dashboard overlay.
        
        Args:
            on_camera_toggle_callback: Callable triggered when camera button is clicked.
            on_reset_callback: Callable triggered when reset button is clicked.
        """
        self.on_camera_toggle = on_camera_toggle_callback
        self.on_reset = on_reset_callback

        # Button holding states for mouse / touch input
        self.gui_throttle = False
        self.gui_brake = False
        self.gui_steer_left = False
        self.gui_steer_right = False

        self._build_dashboard_panel()
        self._build_onscreen_controls()
        self._build_crash_banner()
        self._build_help_overlay()

    # -------------------------------------------------------------------------
    # Dashboard Telemetry Cluster (Bottom Center)
    # -------------------------------------------------------------------------
    def _build_dashboard_panel(self):
        """Creates the central instrument cluster showing speed, gear, camera, and signals."""
        # Main semi-transparent background panel
        self.dash_frame = DirectFrame(
            frameColor=(0.08, 0.10, 0.14, 0.85),
            frameSize=(-0.40, 0.40, -0.17, 0.17),
            pos=(0.0, 0.0, -0.78),
        )

        # Speed readout (large bold number)
        self.speed_label = DirectLabel(
            parent=self.dash_frame,
            text="0",
            text_scale=0.13,
            text_fg=(1.0, 1.0, 1.0, 1.0),
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(0.06, 0.0, -0.05),
        )

        # Speed units label
        self.unit_label = DirectLabel(
            parent=self.dash_frame,
            text="KM/H",
            text_scale=0.038,
            text_fg=(0.65, 0.72, 0.85, 1.0),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(0.09, 0.0, -0.05),
        )

        # Gear indicator badge
        self.gear_frame = DirectFrame(
            parent=self.dash_frame,
            frameColor=(0.15, 0.45, 0.20, 0.9),  # Green for Drive initially
            frameSize=(-0.07, 0.07, -0.05, 0.05),
            pos=(-0.25, 0.0, -0.02),
        )
        self.gear_label = DirectLabel(
            parent=self.gear_frame,
            text="D",
            text_scale=0.07,
            text_fg=(1.0, 1.0, 1.0, 1.0),
            frameColor=(0, 0, 0, 0),
            pos=(0.0, 0.0, -0.022),
        )

        # Active Camera View badge
        self.camera_badge = DirectLabel(
            parent=self.dash_frame,
            text="CAM: Chase View [C]",
            text_scale=0.032,
            text_fg=(0.75, 0.82, 0.95, 1.0),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0.0, 0.0, 0.10),
        )

        # Traffic Signal Status Ahead Badge
        self.signal_badge = DirectLabel(
            parent=self.dash_frame,
            text="SIGNAL: OPEN ROAD",
            text_scale=0.032,
            text_fg=(0.65, 0.85, 0.65, 1.0),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0.0, 0.0, -0.13),
        )

    # -------------------------------------------------------------------------
    # Crash Warning Banner (Screen Center Alert)
    # -------------------------------------------------------------------------
    def _build_crash_banner(self):
        """Displays prominent warning when vehicle impacts an obstacle or car."""
        self.crash_frame = DirectFrame(
            frameColor=(0.85, 0.10, 0.10, 0.90),
            frameSize=(-0.52, 0.52, -0.09, 0.09),
            pos=(0.0, 0.0, 0.35),
        )
        self.crash_label = DirectLabel(
            parent=self.crash_frame,
            text="! CRASH DETECTED !\nREVERSE OR PRESS [R] TO RESET",
            text_scale=0.046,
            text_fg=(1.0, 1.0, 1.0, 1.0),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            pos=(0.0, 0.0, 0.015),
        )
        self.crash_frame.hide()

    # -------------------------------------------------------------------------
    # On-Screen Touch / Mouse Driving Buttons
    # -------------------------------------------------------------------------
    def _build_onscreen_controls(self):
        """Creates on-screen touch/mouse buttons for steering and pedals."""
        btn_bg = (0.15, 0.22, 0.32, 0.75)
        btn_active = (0.25, 0.45, 0.65, 0.95)
        btn_text_color = (1.0, 1.0, 1.0, 1.0)

        # Left: Steer Left Button
        self.btn_steer_l = DirectButton(
            text="< LEFT",
            text_scale=0.045,
            text_fg=btn_text_color,
            frameColor=btn_bg,
            frameSize=(-0.16, 0.16, -0.08, 0.08),
            pos=(-0.95, 0.0, -0.78),
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
        )
        self._bind_hold_events(self.btn_steer_l, "steer_left", btn_bg, btn_active)

        # Left: Steer Right Button
        self.btn_steer_r = DirectButton(
            text="RIGHT >",
            text_scale=0.045,
            text_fg=btn_text_color,
            frameColor=btn_bg,
            frameSize=(-0.16, 0.16, -0.08, 0.08),
            pos=(-0.58, 0.0, -0.78),
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
        )
        self._bind_hold_events(self.btn_steer_r, "steer_right", btn_bg, btn_active)

        # Right: Gas / Accelerate Button
        gas_bg = (0.12, 0.40, 0.20, 0.75)
        gas_active = (0.20, 0.65, 0.32, 0.95)
        self.btn_gas = DirectButton(
            text="GAS ^",
            text_scale=0.045,
            text_fg=btn_text_color,
            frameColor=gas_bg,
            frameSize=(-0.16, 0.16, -0.08, 0.08),
            pos=(0.95, 0.0, -0.78),
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
        )
        self._bind_hold_events(self.btn_gas, "gas", gas_bg, gas_active)

        # Right: Brake / Reverse Button
        brake_bg = (0.45, 0.15, 0.15, 0.75)
        brake_active = (0.75, 0.22, 0.22, 0.95)
        self.btn_brake = DirectButton(
            text="BRAKE v",
            text_scale=0.045,
            text_fg=btn_text_color,
            frameColor=brake_bg,
            frameSize=(-0.16, 0.16, -0.08, 0.08),
            pos=(0.58, 0.0, -0.78),
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
        )
        self._bind_hold_events(self.btn_brake, "brake", brake_bg, brake_active)

        # Top Menu Action Buttons
        self.btn_cam = DirectButton(
            text="CAM MODE [C]",
            text_scale=0.038,
            text_fg=btn_text_color,
            frameColor=(0.20, 0.25, 0.35, 0.80),
            frameSize=(-0.18, 0.18, -0.05, 0.05),
            pos=(-0.95, 0.0, 0.88),
            command=self._on_cam_clicked,
            relief=DGG.RAISED,
            borderWidth=(0.008, 0.008),
        )

        self.btn_reset = DirectButton(
            text="RESET CAR [R]",
            text_scale=0.038,
            text_fg=btn_text_color,
            frameColor=(0.35, 0.22, 0.20, 0.80),
            frameSize=(-0.18, 0.18, -0.05, 0.05),
            pos=(-0.54, 0.0, 0.88),
            command=self._on_reset_clicked,
            relief=DGG.RAISED,
            borderWidth=(0.008, 0.008),
        )

    def _bind_hold_events(self, button: DirectButton, action_key: str,
                          normal_color: tuple, active_color: tuple):
        def on_press(event=None):
            self._set_action_state(action_key, True)
            button["frameColor"] = active_color

        def on_release(event=None):
            self._set_action_state(action_key, False)
            button["frameColor"] = normal_color

        button.bind(DGG.B1PRESS, on_press)
        button.bind(DGG.B1RELEASE, on_release)
        button.bind(DGG.WITHOUT, on_release)

    def _set_action_state(self, action_key: str, state: bool):
        if action_key == "gas":
            self.gui_throttle = state
        elif action_key == "brake":
            self.gui_brake = state
        elif action_key == "steer_left":
            self.gui_steer_left = state
        elif action_key == "steer_right":
            self.gui_steer_right = state

    def _on_cam_clicked(self):
        if self.on_camera_toggle:
            self.on_camera_toggle()

    def _on_reset_clicked(self):
        if self.on_reset:
            self.on_reset()

    # -------------------------------------------------------------------------
    # Controls Help Overlay (Top Right)
    # -------------------------------------------------------------------------
    def _build_help_overlay(self):
        help_text = (
            "CONTROLS (Porsche 911)\n"
            "Accelerate: W / Up Arrow\n"
            "Brake / Rev: S / Down Arrow\n"
            "Steer: A / D or Left / Right\n"
            "Camera View: C\n"
            "Reset Car: R\n"
            "Exit: Esc\n\n"
            "* Traffic obeys signals.\n"
            "* You can obey or break rules!"
        )
        self.help_frame = DirectFrame(
            frameColor=(0.06, 0.08, 0.12, 0.70),
            frameSize=(-0.30, 0.30, -0.20, 0.20),
            pos=(0.95, 0.0, 0.74),
        )
        self.help_label = DirectLabel(
            parent=self.help_frame,
            text=help_text,
            text_scale=0.032,
            text_fg=(0.85, 0.88, 0.95, 0.95),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(-0.27, 0.0, 0.14),
        )

    # -------------------------------------------------------------------------
    # Frame Telemetry Update
    # -------------------------------------------------------------------------
    def update(self, speed_kmh: float, gear: str, camera_mode_name: str,
               signal_state: str = None, is_crashed: bool = False):
        """
        Updates dashboard speed, gear, camera, upcoming traffic light, and crash warning.
        """
        int_speed = int(round(speed_kmh))
        self.speed_label["text"] = f"{int_speed}"

        if int_speed < 60:
            self.speed_label["text_fg"] = (1.0, 1.0, 1.0, 1.0)
        elif int_speed < 110:
            self.speed_label["text_fg"] = (1.0, 0.85, 0.2, 1.0)
        else:
            self.speed_label["text_fg"] = (1.0, 0.35, 0.25, 1.0)

        # Update gear indicator
        self.gear_label["text"] = gear
        if gear == "D":
            self.gear_frame["frameColor"] = (0.15, 0.45, 0.20, 0.9)
        elif gear == "R":
            self.gear_frame["frameColor"] = (0.55, 0.15, 0.15, 0.9)
        elif gear == "N":
            self.gear_frame["frameColor"] = (0.45, 0.40, 0.15, 0.9)
        else:
            self.gear_frame["frameColor"] = (0.25, 0.25, 0.30, 0.9)

        # Update camera mode text
        self.camera_badge["text"] = f"CAM: {camera_mode_name} [C]"

        # Update Traffic Light Ahead Telemetry
        if signal_state == "GREEN":
            self.signal_badge["text"] = "SIGNAL AHEAD: [ GREEN ]"
            self.signal_badge["text_fg"] = (0.2, 1.0, 0.3, 1.0)
        elif signal_state == "YELLOW":
            self.signal_badge["text"] = "SIGNAL AHEAD: [ YELLOW ]"
            self.signal_badge["text_fg"] = (1.0, 0.88, 0.2, 1.0)
        elif signal_state == "RED":
            self.signal_badge["text"] = "SIGNAL AHEAD: [ RED - STOP ]"
            self.signal_badge["text_fg"] = (1.0, 0.25, 0.25, 1.0)
        else:
            self.signal_badge["text"] = "SIGNAL: OPEN ROADWAY"
            self.signal_badge["text_fg"] = (0.7, 0.75, 0.85, 1.0)

        # Show/hide crash alert banner
        if is_crashed:
            self.crash_frame.show()
        else:
            self.crash_frame.hide()

    # -------------------------------------------------------------------------
    # Input Query Methods
    # -------------------------------------------------------------------------
    def get_throttle_input(self) -> float:
        return 1.0 if self.gui_throttle else 0.0

    def get_brake_input(self) -> float:
        return 1.0 if self.gui_brake else 0.0

    def get_steer_left_input(self) -> bool:
        return self.gui_steer_left

    def get_steer_right_input(self) -> bool:
        return self.gui_steer_right
