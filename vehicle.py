"""
vehicle.py - Porsche 911 Simulation & Procedural Model for RealDrive
--------------------------------------------------------------------
This module models an authentic Porsche 911 (992 generation inspired):
- Iconic low-slung aerodynamic sports car silhouette and teardrop fastback roofline ("flyline").
- Elevated front fender humps with distinctive oval bug-eye headlights.
- Low-sloping front hood and flared muscular rear haunches (widebody rear fenders).
- Modern full-width slim rear LED lightbar, rear engine deck louvers, and twin sport exhausts.
- Performance sports alloy wheels with visible red brake calipers.
- True bicycle kinematics with standard Python `math`.
- Crash detection state, recoil reactions, and damage feedback.
"""

import math
from panda3d.core import NodePath, Vec3, Vec4
from utils import create_box, create_cylinder


class Vehicle:
    """Simulates player-controlled Porsche 911 with kinematics and collision response."""

    def __init__(self, render: NodePath, init_pos: Vec3 = Vec3(0, 0, 0), init_heading: float = 0.0):
        """
        Initializes vehicle kinematics and procedural Porsche 911 model.
        
        Args:
            render: Root render NodePath to attach to.
            init_pos: Starting position (X, Y, Z) in meters.
            init_heading: Starting heading in degrees (0 = +Y).
        """
        # World Transform State
        self.pos_x = float(init_pos.x)
        self.pos_y = float(init_pos.y)
        self.pos_z = float(init_pos.z)
        self.heading = float(init_heading)

        # Kinematic State
        self.speed = 0.0            # Forward velocity (m/s)
        self.steering_angle = 0.0   # Front wheel steering angle (degrees)
        self.wheel_spin = 0.0       # Wheel pitch spin (degrees)
        self.gear = "N"

        # Porsche 911 Sports Car Tuning Parameters
        self.wheelbase = 2.45               # Authentic Porsche 911 wheelbase (meters)
        self.max_forward_speed = 48.0       # Top speed ~173 km/h (m/s)
        self.max_reverse_speed = 12.0       # Reverse speed ~43 km/h (m/s)
        self.accel_rate = 18.0              # Brisk 0-100 sports car acceleration (m/s^2)
        self.reverse_accel_rate = 8.0       # Reverse acceleration (m/s^2)
        self.brake_decel_rate = 28.0        # High-performance disc brake stopping power (m/s^2)
        self.coast_drag = 3.2               # Aerodynamic drag & engine braking (m/s^2)
        self.max_steer_angle = 30.0         # Front wheel lock (degrees)
        self.steer_speed = 70.0             # Sharp steering response (degrees/s)
        self.steer_return_speed = 85.0      # Self-centering speed (degrees/s)
        self.wheel_radius = 0.34            # 20-inch low profile sports wheel (meters)

        # Crash & Impact State
        self.crashed = False
        self.crash_timer = 0.0
        self.last_impact_severity = 0.0

        # Visual Scenegraph Root
        self.root = NodePath("porsche_911_root")
        self.root.reparentTo(render)
        self.root.setPos(self.pos_x, self.pos_y, self.pos_z)
        self.root.setH(self.heading)

        # Wheel node references for animations
        self.fl_pivot = None
        self.fr_pivot = None
        self.fl_wheel = None
        self.fr_wheel = None
        self.rl_wheel = None
        self.rr_wheel = None

        self._build_porsche_911_model()

    # -------------------------------------------------------------------------
    # Porsche 911 Procedural 3D Model
    # -------------------------------------------------------------------------
    def _build_porsche_911_model(self):
        """Builds a detailed, authentic Porsche 911 Carrera procedural model."""
        # Signature Porsche Guards Red body color
        guards_red = Vec4(0.88, 0.10, 0.12, 1.0)
        dark_chassis = Vec4(0.12, 0.12, 0.13, 1.0)
        tinted_glass = Vec4(0.15, 0.18, 0.22, 1.0)
        gloss_black = Vec4(0.08, 0.08, 0.09, 1.0)

        # 1. Lower Aerodynamic Undertray / Splitter
        undertray = create_box(dx=1.80, dy=4.40, dz=0.18, color=dark_chassis)
        undertray.setPos(0, 0, 0.20)
        undertray.reparentTo(self.root)

        # 2. Main Center Body Shell
        center_body = create_box(dx=1.76, dy=4.30, dz=0.45, color=guards_red)
        center_body.setPos(0, 0, 0.48)
        center_body.reparentTo(self.root)

        # 3. Flared Widebody Rear Haunches (Muscular rear fenders, iconic to 911)
        rear_flares = create_box(dx=1.92, dy=1.80, dz=0.48, color=guards_red)
        rear_flares.setPos(0, -1.15, 0.50)
        rear_flares.reparentTo(self.root)

        # 4. Low-Sloping Front Bonnet / Hood
        front_hood = create_box(dx=1.40, dy=1.55, dz=0.24, color=guards_red)
        front_hood.setPos(0, 1.25, 0.60)
        front_hood.reparentTo(self.root)

        # 5. Distinctive Porsche Raised Front Fender Humps (Left & Right)
        # These create the classic 911 headlights bug-eye profile when viewed from the driver's seat
        fender_l = create_box(dx=0.32, dy=1.70, dz=0.34, color=guards_red)
        fender_l.setPos(-0.76, 1.20, 0.65)
        fender_l.reparentTo(self.root)

        fender_r = create_box(dx=0.32, dy=1.70, dz=0.34, color=guards_red)
        fender_r.setPos(0.76, 1.20, 0.65)
        fender_r.reparentTo(self.root)

        # 6. Oval Xenon Headlights embedded into front fenders
        hl_color = Vec4(1.0, 1.0, 0.95, 1.0)
        hl_l = create_cylinder(radius=0.16, height=0.12, num_segments=14, color=hl_color, axis="y")
        hl_l.setPos(-0.76, 2.05, 0.72)
        hl_l.reparentTo(self.root)

        hl_r = create_cylinder(radius=0.16, height=0.12, num_segments=14, color=hl_color, axis="y")
        hl_r.setPos(0.76, 2.05, 0.72)
        hl_r.reparentTo(self.root)

        # 7. Iconic Fastback Teardrop Cockpit Roofline ("Flyline")
        # Windshield section
        windshield = create_box(dx=1.48, dy=1.10, dz=0.42, color=tinted_glass)
        windshield.setPos(0, 0.35, 0.88)
        windshield.reparentTo(self.root)

        # Roof Peak
        roof = create_box(dx=1.36, dy=1.20, dz=0.12, color=guards_red)
        roof.setPos(0, -0.20, 1.15)
        roof.reparentTo(self.root)

        # Sloping Rear Fastback Window (tapers smoothly toward rear engine deck)
        rear_fastback = create_box(dx=1.40, dy=1.25, dz=0.38, color=tinted_glass)
        rear_fastback.setPos(0, -0.85, 0.92)
        rear_fastback.reparentTo(self.root)

        # 8. Rear Engine Deck with Louver Grille & Subtle Ducktail Spoiler Lip
        engine_deck = create_box(dx=1.42, dy=0.90, dz=0.22, color=guards_red)
        engine_deck.setPos(0, -1.65, 0.68)
        engine_deck.reparentTo(self.root)

        # Louver Cooling Grille (gloss black)
        louver_grille = create_box(dx=0.85, dy=0.60, dz=0.04, color=gloss_black)
        louver_grille.setPos(0, -1.60, 0.80)
        louver_grille.reparentTo(self.root)

        # Aerodynamic Rear Spoiler Lip
        spoiler_lip = create_box(dx=1.52, dy=0.18, dz=0.10, color=guards_red)
        spoiler_lip.setPos(0, -2.12, 0.78)
        spoiler_lip.reparentTo(self.root)

        # 9. Modern 992-Style Full-Width Slim LED Rear Lightbar
        led_red = Vec4(1.0, 0.05, 0.05, 1.0)
        rear_lightbar = create_box(dx=1.65, dy=0.12, dz=0.08, color=led_red)
        rear_lightbar.setPos(0, -2.18, 0.66)
        rear_lightbar.reparentTo(self.root)

        # 10. Dual Chrome Exhaust Tips & Rear Aerodynamic Diffuser
        diffuser = create_box(dx=1.55, dy=0.45, dz=0.16, color=dark_chassis)
        diffuser.setPos(0, -2.05, 0.28)
        diffuser.reparentTo(self.root)

        chrome = Vec4(0.9, 0.92, 0.95, 1.0)
        exh_l = create_cylinder(radius=0.07, height=0.22, num_segments=10, color=chrome, axis="y")
        exh_l.setPos(-0.45, -2.25, 0.28)
        exh_l.reparentTo(self.root)

        exh_r = create_cylinder(radius=0.07, height=0.22, num_segments=10, color=chrome, axis="y")
        exh_r.setPos(0.45, -2.25, 0.28)
        exh_r.reparentTo(self.root)

        # 11. Low-Profile Performance Wheels with Red Brake Calipers
        self._build_porsche_wheels()

    def _build_porsche_wheels(self):
        """Constructs 20-inch staggered alloy wheels with visible brake calipers."""
        tire_radius = self.wheel_radius
        tire_width = 0.28
        rubber_color = Vec4(0.12, 0.12, 0.14, 1.0)
        alloy_silver = Vec4(0.78, 0.80, 0.84, 1.0)
        caliper_red = Vec4(0.95, 0.10, 0.10, 1.0)

        def make_porsche_wheel(is_left: bool):
            wheel_node = NodePath("porsche_wheel")
            # Tire
            tire = create_cylinder(radius=tire_radius, height=tire_width, num_segments=16,
                                   color=rubber_color, axis="x")
            tire.reparentTo(wheel_node)

            # Center Alloy Rim
            rim = create_cylinder(radius=tire_radius * 0.70, height=tire_width * 1.02, num_segments=12,
                                  color=alloy_silver, axis="x")
            rim.reparentTo(wheel_node)

            # Red Brake Caliper
            caliper = create_box(dx=0.08, dy=0.18, dz=0.14, color=caliper_red)
            side_offset = -tire_width * 0.25 if is_left else tire_width * 0.25
            caliper.setPos(side_offset, 0.12, 0.08)
            caliper.reparentTo(wheel_node)

            return wheel_node

        wheel_x = 0.88
        wheel_y_front = 1.25
        wheel_y_rear = -1.25
        wheel_z = 0.34

        # Front Steerable Wheels
        self.fl_pivot = NodePath("fl_pivot")
        self.fl_pivot.setPos(-wheel_x, wheel_y_front, wheel_z)
        self.fl_pivot.reparentTo(self.root)
        self.fl_wheel = make_porsche_wheel(is_left=True)
        self.fl_wheel.reparentTo(self.fl_pivot)

        self.fr_pivot = NodePath("fr_pivot")
        self.fr_pivot.setPos(wheel_x, wheel_y_front, wheel_z)
        self.fr_pivot.reparentTo(self.root)
        self.fr_wheel = make_porsche_wheel(is_left=False)
        self.fr_wheel.reparentTo(self.fr_pivot)

        # Rear Fixed Wheels
        self.rl_wheel = make_porsche_wheel(is_left=True)
        self.rl_wheel.setPos(-wheel_x * 1.04, wheel_y_rear, wheel_z)  # Slightly wider rear track
        self.rl_wheel.reparentTo(self.root)

        self.rr_wheel = make_porsche_wheel(is_left=False)
        self.rr_wheel.setPos(wheel_x * 1.04, wheel_y_rear, wheel_z)
        self.rr_wheel.reparentTo(self.root)

    # -------------------------------------------------------------------------
    # Kinematics & Physics Update
    # -------------------------------------------------------------------------
    def update(self, dt: float, throttle: float, brake: float, steer_left: bool, steer_right: bool):
        """
        Updates kinematics, steering, velocity, crash recovery, and wheel spin.
        """
        dt = max(0.0001, min(dt, 0.1))

        # Handle Crash Recovery Timer
        if self.crash_timer > 0.0:
            self.crash_timer -= dt
            if self.crash_timer <= 0.0:
                self.crashed = False

        # 1. Steering Dynamics
        if steer_left and not steer_right:
            self.steering_angle += self.steer_speed * dt
        elif steer_right and not steer_left:
            self.steering_angle -= self.steer_speed * dt
        else:
            if abs(self.steering_angle) < (self.steer_return_speed * dt):
                self.steering_angle = 0.0
            else:
                self.steering_angle -= math.copysign(self.steer_return_speed * dt, self.steering_angle)

        self.steering_angle = max(-self.max_steer_angle, min(self.steering_angle, self.max_steer_angle))

        # 2. Acceleration, Braking, and Reverse
        is_moving_forward = self.speed > 0.05
        is_moving_reverse = self.speed < -0.05

        if throttle > 0.0:
            if is_moving_reverse:
                self.speed += self.brake_decel_rate * throttle * dt
            else:
                self.speed += self.accel_rate * throttle * dt
                if self.speed > self.max_forward_speed:
                    self.speed = self.max_forward_speed

        elif brake > 0.0:
            if is_moving_forward:
                self.speed -= self.brake_decel_rate * brake * dt
                if self.speed < 0.0:
                    self.speed = 0.0
            else:
                self.speed -= self.reverse_accel_rate * brake * dt
                if self.speed < -self.max_reverse_speed:
                    self.speed = -self.max_reverse_speed
        else:
            if abs(self.speed) < (self.coast_drag * dt):
                self.speed = 0.0
            else:
                self.speed -= math.copysign(self.coast_drag * dt, self.speed)

        # 3. Angular Velocity & Heading Update (Bicycle model)
        if abs(self.speed) > 0.001 and abs(self.steering_angle) > 0.001:
            steer_rad = math.radians(self.steering_angle)
            omega_rad = (self.speed / self.wheelbase) * math.tan(steer_rad)
            heading_delta_deg = math.degrees(omega_rad) * dt
            self.heading = (self.heading + heading_delta_deg) % 360.0

        # 4. Position Translation
        heading_rad = math.radians(self.heading)
        dx = -self.speed * math.sin(heading_rad) * dt
        dy = self.speed * math.cos(heading_rad) * dt

        self.pos_x += dx
        self.pos_y += dy

        # 5. Gear Determination
        if abs(self.speed) < 0.1 and throttle == 0.0 and brake == 0.0:
            self.gear = "N"
        elif self.speed >= -0.05 and (throttle > 0.0 or self.speed > 0.1):
            self.gear = "D"
        elif self.speed <= 0.05 and (brake > 0.0 or self.speed < -0.1):
            self.gear = "R"
        else:
            self.gear = "N"

        # 6. Apply Transforms to Panda3D Scenegraph
        self.root.setPos(self.pos_x, self.pos_y, self.pos_z)
        self.root.setH(self.heading)

        # Wheel Steering Rotation
        self.fl_pivot.setH(self.steering_angle)
        self.fr_pivot.setH(self.steering_angle)

        # Wheel Pitch Spin
        wheel_rot_delta_deg = math.degrees((self.speed * dt) / self.wheel_radius)
        self.wheel_spin = (self.wheel_spin + wheel_rot_delta_deg) % 360.0

        self.fl_wheel.setP(self.wheel_spin)
        self.fr_wheel.setP(self.wheel_spin)
        self.rl_wheel.setP(self.wheel_spin)
        self.rr_wheel.setP(self.wheel_spin)

    # -------------------------------------------------------------------------
    # Crash Trigger & Telemetry
    # -------------------------------------------------------------------------
    def on_crash(self, impact_intensity: float):
        """Called by collision system when vehicle suffers a collision."""
        self.crashed = True
        self.crash_timer = 2.5
        self.last_impact_severity = impact_intensity

    def is_crashed(self) -> bool:
        """Returns True if vehicle is currently in crashed state."""
        return self.crashed

    def get_speed_kmh(self) -> float:
        """Speed in km/h."""
        return abs(self.speed) * 3.6

    def get_gear(self) -> str:
        """Active gear string."""
        return self.gear

    def get_pos(self) -> Vec3:
        """World position."""
        return Vec3(self.pos_x, self.pos_y, self.pos_z)

    def get_heading(self) -> float:
        """Heading in degrees."""
        return self.heading

    def reset(self, pos: Vec3 = Vec3(0, 0, 0), heading: float = 0.0):
        """Resets vehicle position, heading, velocity, and crash state."""
        self.pos_x = float(pos.x)
        self.pos_y = float(pos.y)
        self.pos_z = float(pos.z)
        self.heading = float(heading)
        self.speed = 0.0
        self.steering_angle = 0.0
        self.gear = "P"
        self.crashed = False
        self.crash_timer = 0.0
        self.root.setPos(self.pos_x, self.pos_y, self.pos_z)
        self.root.setH(self.heading)
        self.fl_pivot.setH(0)
        self.fr_pivot.setH(0)
