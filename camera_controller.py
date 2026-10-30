"""
camera_controller.py - Multi-Mode Dynamic Camera System for RealDrive
---------------------------------------------------------------------
Manages camera perspectives for the driving simulator, providing seamless
switching between distinct camera modes:

1. Chase Camera (3rd Person): Smoothly follows the vehicle from behind and above
   using exponential damping, giving a dynamic feel as the car turns and accelerates.
2. Cockpit / Hood Camera (1st Person): Mounted at the driver's eye level for an
   immersive first-person cockpit driving perspective.
3. Top-Down / Helicopter Camera: Elevated perspective providing high-altitude
   situational awareness of the surrounding city grid.

Supports switching via the 'C' key or on-screen HUD button.
"""

import math
from panda3d.core import NodePath, Vec3


class CameraController:
    """Controls the main camera behavior and transitions between driving modes."""

    # Available camera view modes
    MODE_CHASE = 0
    MODE_COCKPIT = 1
    MODE_TOPDOWN = 2

    MODE_NAMES = {
        MODE_CHASE: "Chase View",
        MODE_COCKPIT: "Cockpit View",
        MODE_TOPDOWN: "Top-Down View",
    }

    def __init__(self, camera: NodePath):
        """
        Initializes the camera controller.
        
        Args:
            camera: The Panda3D base camera NodePath (base.camera).
        """
        self.camera = camera
        self.current_mode = self.MODE_CHASE

        # Current camera world coordinates
        self.cam_x = 0.0
        self.cam_y = -10.0
        self.cam_z = 4.0

        # Look-at point coordinates
        self.target_look_x = 0.0
        self.target_look_y = 0.0
        self.target_look_z = 0.0

        # Chase Camera Configuration
        self.chase_distance = 8.0     # Distance behind the car (meters)
        self.chase_height = 3.2       # Height above ground (meters)
        self.chase_look_ahead = 4.0   # Point in front of the car to look at
        self.chase_look_height = 1.2  # Look-at height
        self.chase_follow_speed = 6.5 # Damping factor for smooth following

        # Cockpit Camera Configuration
        self.cockpit_offset_forward = 0.35  # Driver eye position along car Y
        self.cockpit_offset_side = -0.35    # Driver eye position along car X (left-hand drive)
        self.cockpit_offset_height = 1.25   # Driver eye height along car Z
        self.cockpit_look_ahead = 15.0      # Forward focal target

        # Top-Down Camera Configuration
        self.topdown_height = 32.0          # Altitude above the car
        self.topdown_distance = 12.0        # Offset behind the car for slight angle
        self.topdown_follow_speed = 5.0     # Smooth pan speed

        # Flag to indicate immediate position snap on mode switch
        self.snap_next_frame = True

    def toggle_mode(self):
        """Cycles to the next camera perspective."""
        self.current_mode = (self.current_mode + 1) % len(self.MODE_NAMES)
        self.snap_next_frame = True

    def set_mode(self, mode: int):
        """Sets a specific camera mode directly."""
        if mode in self.MODE_NAMES:
            self.current_mode = mode
            self.snap_next_frame = True

    def get_mode_name(self) -> str:
        """Returns the human-readable name of the active camera mode."""
        return self.MODE_NAMES.get(self.current_mode, "Unknown View")

    def update(self, dt: float, vehicle):
        """
        Updates camera position and orientation based on vehicle movement.
        
        Args:
            dt: Delta time in seconds.
            vehicle: Vehicle instance.
        """
        car_pos = vehicle.get_pos()
        car_h = vehicle.get_heading()
        car_h_rad = math.radians(car_h)

        # In Panda3D:
        # Car forward vector = (-sin(car_h_rad), cos(car_h_rad))
        # Car right vector   = (cos(car_h_rad), sin(car_h_rad))
        fwd_x = -math.sin(car_h_rad)
        fwd_y = math.cos(car_h_rad)
        right_x = math.cos(car_h_rad)
        right_y = math.sin(car_h_rad)

        if self.current_mode == self.MODE_CHASE:
            self._update_chase_mode(dt, car_pos, fwd_x, fwd_y)
        elif self.current_mode == self.MODE_COCKPIT:
            self._update_cockpit_mode(car_pos, car_h, fwd_x, fwd_y, right_x, right_y)
        elif self.current_mode == self.MODE_TOPDOWN:
            self._update_topdown_mode(dt, car_pos, fwd_x, fwd_y)

        self.snap_next_frame = False

    def _update_chase_mode(self, dt: float, car_pos: Vec3, fwd_x: float, fwd_y: float):
        """3rd-person smooth trailing chase camera."""
        # Desired position is behind (-fwd) and above car
        desired_x = car_pos.x - fwd_x * self.chase_distance
        desired_y = car_pos.y - fwd_y * self.chase_distance
        desired_z = car_pos.z + self.chase_height

        # Desired look-at target is in front of car
        desired_look_x = car_pos.x + fwd_x * self.chase_look_ahead
        desired_look_y = car_pos.y + fwd_y * self.chase_look_ahead
        desired_look_z = car_pos.z + self.chase_look_height

        if self.snap_next_frame:
            self.cam_x, self.cam_y, self.cam_z = desired_x, desired_y, desired_z
            self.target_look_x = desired_look_x
            self.target_look_y = desired_look_y
            self.target_look_z = desired_look_z
        else:
            # Exponential smooth damping
            lerp_factor = 1.0 - math.exp(-self.chase_follow_speed * dt)
            self.cam_x += (desired_x - self.cam_x) * lerp_factor
            self.cam_y += (desired_y - self.cam_y) * lerp_factor
            self.cam_z += (desired_z - self.cam_z) * lerp_factor

            self.target_look_x += (desired_look_x - self.target_look_x) * lerp_factor
            self.target_look_y += (desired_look_y - self.target_look_y) * lerp_factor
            self.target_look_z += (desired_look_z - self.target_look_z) * lerp_factor

        if self.camera:
            self.camera.setPos(self.cam_x, self.cam_y, self.cam_z)
            self.camera.lookAt(self.target_look_x, self.target_look_y, self.target_look_z)

    def _update_cockpit_mode(self, car_pos: Vec3, car_h: float,
                             fwd_x: float, fwd_y: float, right_x: float, right_y: float):
        """1st-person interior driver perspective."""
        # Compute exact driver eye position
        cam_x = car_pos.x + fwd_x * self.cockpit_offset_forward + right_x * self.cockpit_offset_side
        cam_y = car_pos.y + fwd_y * self.cockpit_offset_forward + right_y * self.cockpit_offset_side
        cam_z = car_pos.z + self.cockpit_offset_height

        # Look target directly ahead along vehicle line of sight
        look_x = cam_x + fwd_x * self.cockpit_look_ahead
        look_y = cam_y + fwd_y * self.cockpit_look_ahead
        look_z = cam_z - 0.2  # Slightly down toward the road horizon

        if self.camera:
            self.camera.setPos(cam_x, cam_y, cam_z)
            self.camera.lookAt(look_x, look_y, look_z)

    def _update_topdown_mode(self, dt: float, car_pos: Vec3, fwd_x: float, fwd_y: float):
        """Elevated top-down view showing the vehicle in its city environment."""
        desired_x = car_pos.x - fwd_x * self.topdown_distance
        desired_y = car_pos.y - fwd_y * self.topdown_distance
        desired_z = car_pos.z + self.topdown_height

        if self.snap_next_frame:
            self.cam_x, self.cam_y, self.cam_z = desired_x, desired_y, desired_z
        else:
            lerp_factor = 1.0 - math.exp(-self.topdown_follow_speed * dt)
            self.cam_x += (desired_x - self.cam_x) * lerp_factor
            self.cam_y += (desired_y - self.cam_y) * lerp_factor
            self.cam_z += (desired_z - self.cam_z) * lerp_factor

        if self.camera:
            self.camera.setPos(self.cam_x, self.cam_y, self.cam_z)
            self.camera.lookAt(car_pos.x, car_pos.y, car_pos.z + 0.5)
