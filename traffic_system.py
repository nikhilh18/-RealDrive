"""
traffic_system.py - Traffic Signals & NPC AI Simulation for RealDrive
---------------------------------------------------------------------
Simulates realistic urban traffic systems:
- 4-Way Traffic Signal Gantries at every intersection with cycling state machine
  (Green -> Yellow -> Red).
- Moving NPC vehicles adhering strictly to traffic laws:
  1. Stopping smoothly at red & yellow lights before the intersection stop line.
  2. Maintaining safe following distances behind other vehicles (including player).
  3. Accelerating when lights turn green.
- Provides traffic signal telemetry for the player's dashboard while allowing the
  player total freedom to obey or ignore traffic rules.
"""

import math
import random
from typing import List, Tuple, Optional
from panda3d.core import NodePath, Vec3, Vec4
from utils import create_box, create_cylinder


class TrafficLightSignal:
    """Represents a 4-way intersection traffic light with procedural signal gantries."""

    def __init__(self, render: NodePath, center_x: float, center_y: float, road_width: float = 14.0):
        self.cx = center_x
        self.cy = center_y
        self.road_width = road_width

        # Stop lines are located at the edge of the intersection box
        self.stop_dist = (road_width * 0.5) + 1.5

        # Visual Signal Post Nodes
        self.posts_node = NodePath(f"traffic_signal_{center_x}_{center_y}")
        self.posts_node.reparentTo(render)

        # Lens mesh references to swap emissive colors: {direction: {"red": node, "yellow": node, "green": node}}
        self.lenses = {}
        self._build_signal_heads()

        # Timing Cycle Parameters
        self.green_duration = 9.0
        self.yellow_duration = 2.5
        self.all_red_duration = 1.5
        self.total_cycle = (self.green_duration + self.yellow_duration + self.all_red_duration) * 2.0

        # Offset by intersection spatial coordinates to create progressive "green waves"
        self.timer = abs(center_x * 0.3 + center_y * 0.2) % self.total_cycle

    def _build_signal_heads(self):
        """Constructs 4 traffic light gantries at the four corners of the intersection."""
        hw = self.road_width * 0.5 + 1.2
        # Corner gantry positions: (x, y, heading_degrees, dir_key)
        # Approaches:
        # S (driving +Y): post on right curb (X + hw, Y - hw), faces South (heading 0)
        # N (driving -Y): post on right curb (X - hw, Y + hw), faces North (heading 180)
        # W (driving +X): post on right curb (X - hw, Y - hw), faces West (heading -90)
        # E (driving -X): post on right curb (X + hw, Y + hw), faces East (heading 90)
        configs = [
            ("S", self.cx + hw, self.cy - hw, 0),
            ("N", self.cx - hw, self.cy + hw, 180),
            ("W", self.cx - hw, self.cy - hw, -90),
            ("E", self.cx + hw, self.cy + hw, 90),
        ]

        pole_color = Vec4(0.18, 0.20, 0.22, 1.0)
        box_color = Vec4(0.10, 0.11, 0.12, 1.0)

        for dir_key, px, py, heading in configs:
            post = NodePath(f"post_{dir_key}")
            post.setPos(px, py, 0.22)
            post.setH(heading)
            post.reparentTo(self.posts_node)

            # Vertical steel pole
            pole = create_cylinder(radius=0.14, height=4.8, num_segments=8, color=pole_color, axis="z")
            pole.setPos(0, 0, 2.4)
            pole.reparentTo(post)

            # Overhang mast arm
            arm = create_cylinder(radius=0.10, height=2.6, num_segments=8, color=pole_color, axis="y")
            arm.setPos(0, 1.3, 4.6)
            arm.reparentTo(post)

            # Signal Head Housing
            housing = create_box(dx=0.38, dy=0.32, dz=1.05, color=box_color)
            housing.setPos(0, 2.4, 4.2)
            housing.reparentTo(post)

            # 3 Lenses: Red (top), Yellow (mid), Green (bot)
            r_lens = create_cylinder(radius=0.12, height=0.08, num_segments=10,
                                     color=Vec4(0.2, 0.05, 0.05, 1.0), axis="y")
            r_lens.setPos(0, 2.22, 4.55)
            r_lens.reparentTo(post)

            y_lens = create_cylinder(radius=0.12, height=0.08, num_segments=10,
                                     color=Vec4(0.2, 0.18, 0.05, 1.0), axis="y")
            y_lens.setPos(0, 2.22, 4.20)
            y_lens.reparentTo(post)

            g_lens = create_cylinder(radius=0.12, height=0.08, num_segments=10,
                                     color=Vec4(0.05, 0.2, 0.08, 1.0), axis="y")
            g_lens.setPos(0, 2.22, 3.85)
            g_lens.reparentTo(post)

            self.lenses[dir_key] = {"red": r_lens, "yellow": y_lens, "green": g_lens}

    def update(self, dt: float):
        """Updates light cycle timer and updates lens colors."""
        self.timer = (self.timer + dt) % self.total_cycle
        ns_state, ew_state = self.get_current_states()
        self._apply_lens_colors("N", ns_state)
        self._apply_lens_colors("S", ns_state)
        self._apply_lens_colors("E", ew_state)
        self._apply_lens_colors("W", ew_state)

    def get_current_states(self) -> Tuple[str, str]:
        """Returns (north_south_state, east_west_state)."""
        t = self.timer
        g = self.green_duration
        y = self.yellow_duration
        r = self.all_red_duration
        half = g + y + r

        if t < g:
            return "GREEN", "RED"
        elif t < (g + y):
            return "YELLOW", "RED"
        elif t < half:
            return "RED", "RED"
        elif t < (half + g):
            return "RED", "GREEN"
        elif t < (half + g + y):
            return "RED", "YELLOW"
        else:
            return "RED", "RED"

    def _apply_lens_colors(self, dir_key: str, state: str):
        """Sets emissive bright vs dark colors for the lenses."""
        l = self.lenses[dir_key]
        bright_red = Vec4(1.0, 0.05, 0.05, 1.0)
        dim_red = Vec4(0.25, 0.05, 0.05, 1.0)
        bright_yellow = Vec4(1.0, 0.88, 0.10, 1.0)
        dim_yellow = Vec4(0.25, 0.22, 0.05, 1.0)
        bright_green = Vec4(0.10, 1.0, 0.25, 1.0)
        dim_green = Vec4(0.05, 0.25, 0.08, 1.0)

        l["red"].setColor(bright_red if state == "RED" else dim_red)
        l["yellow"].setColor(bright_yellow if state == "YELLOW" else dim_yellow)
        l["green"].setColor(bright_green if state == "GREEN" else dim_green)

    def get_state_for_approach(self, approach_dir: str) -> str:
        """Returns 'GREEN', 'YELLOW', or 'RED' for the specified approach direction ('N', 'S', 'E', 'W')."""
        ns_state, ew_state = self.get_current_states()
        if approach_dir in ("N", "S"):
            return ns_state
        return ew_state


class NPCVehicle:
    """Simulates an autonomous AI vehicle that strictly obeys traffic signals and car following."""

    def __init__(self, render: NodePath, start_x: float, start_y: float,
                 direction: str, model_type: str = "sedan", color: Vec4 = None):
        """
        direction:
            '+Y': driving North on right side of corridor
            '-Y': driving South on right side of corridor
            '+X': driving East on right side of corridor
            '-X': driving West on right side of corridor
        """
        self.pos_x = start_x
        self.pos_y = start_y
        self.pos_z = 0.0
        self.direction = direction

        # Align heading with travel direction
        heading_map = {'+Y': 0.0, '-Y': 180.0, '+X': -90.0, '-X': 90.0}
        self.heading = heading_map.get(direction, 0.0)

        # Kinematics
        self.speed = random.uniform(8.0, 11.5)  # ~30 - 41 km/h cruising speed
        self.target_speed = self.speed
        self.accel_rate = 7.0
        self.brake_decel_rate = 18.0
        self.wheel_spin = 0.0
        self.crashed = False

        # Visual Root
        self.root = NodePath("npc_vehicle")
        self.root.reparentTo(render)
        self.root.setPos(self.pos_x, self.pos_y, self.pos_z)
        self.root.setH(self.heading)

        # Model Appearance
        if color is None:
            colors = [
                Vec4(0.15, 0.35, 0.65, 1.0),  # Blue
                Vec4(0.80, 0.80, 0.82, 1.0),  # Silver
                Vec4(0.12, 0.12, 0.14, 1.0),  # Obsidian Black
                Vec4(0.78, 0.45, 0.15, 1.0),  # Sunset Orange
                Vec4(0.20, 0.55, 0.35, 1.0),  # Forest Green
                Vec4(0.90, 0.90, 0.92, 1.0),  # Glacier White
            ]
            color = random.choice(colors)

        self.wheels = []
        self._build_model(model_type, color)

    def _build_model(self, model_type: str, color: Vec4):
        """Builds a neat procedural NPC passenger car or SUV."""
        is_suv = (model_type == "suv")
        body_h = 0.65 if is_suv else 0.50
        roof_h = 0.70 if is_suv else 0.55
        glass_color = Vec4(0.18, 0.22, 0.28, 1.0)

        # Main Chassis
        chassis = create_box(dx=1.80, dy=4.20, dz=body_h, color=color)
        chassis.setPos(0, 0, 0.48)
        chassis.reparentTo(self.root)

        # Cabin / Greenhouse
        cabin = create_box(dx=1.55, dy=2.10, dz=roof_h, color=glass_color)
        cabin.setPos(0, -0.20, 0.98 if is_suv else 0.92)
        cabin.reparentTo(self.root)

        # Headlights (Warm White)
        hl = create_box(dx=0.32, dy=0.12, dz=0.14, color=Vec4(1.0, 1.0, 0.9, 1.0))
        hl.setPos(-0.62, 2.12, 0.52)
        hl.reparentTo(self.root)

        hr = create_box(dx=0.32, dy=0.12, dz=0.14, color=Vec4(1.0, 1.0, 0.9, 1.0))
        hr.setPos(0.62, 2.12, 0.52)
        hr.reparentTo(self.root)

        # Taillights (Red)
        tl = create_box(dx=0.32, dy=0.12, dz=0.12, color=Vec4(1.0, 0.05, 0.05, 1.0))
        tl.setPos(-0.62, -2.12, 0.54)
        tl.reparentTo(self.root)

        tr = create_box(dx=0.32, dy=0.12, dz=0.12, color=Vec4(1.0, 0.05, 0.05, 1.0))
        tr.setPos(0.62, -2.12, 0.54)
        tr.reparentTo(self.root)

        # 4 Wheels
        rubber = Vec4(0.14, 0.14, 0.15, 1.0)
        rim = Vec4(0.70, 0.70, 0.72, 1.0)
        wheel_positions = [(-0.90, 1.25), (0.90, 1.25), (-0.90, -1.25), (0.90, -1.25)]
        for wx, wy in wheel_positions:
            w_node = NodePath("w")
            t = create_cylinder(radius=0.34, height=0.26, num_segments=12, color=rubber, axis="x")
            t.reparentTo(w_node)
            r = create_cylinder(radius=0.22, height=0.28, num_segments=10, color=rim, axis="x")
            r.reparentTo(w_node)
            w_node.setPos(wx, wy, 0.34)
            w_node.reparentTo(self.root)
            self.wheels.append(w_node)

    def on_crash(self, impact_intensity: float):
        """Called when vehicle crashes into an obstacle or car."""
        self.crashed = True

    def get_pos(self) -> Vec3:
        return Vec3(self.pos_x, self.pos_y, self.pos_z)

    def get_speed_kmh(self) -> float:
        return abs(self.speed) * 3.6

    def update(self, dt: float, traffic_signals: List[TrafficLightSignal], other_vehicles: List):
        """
        Executes AI behavior: obeys traffic signals and preserves headway behind other cars.
        """
        # Determine desire to stop (False = cruise, True = brake to zero)
        must_stop = False

        # 1. Traffic Signal Obedience
        for signal in traffic_signals:
            # Check if this signal is ahead along current lane
            should_stop_for_signal = self._evaluate_signal(signal)
            if should_stop_for_signal:
                must_stop = True
                break

        # 2. Car-Following Safety Buffer (Adaptive Cruise)
        if not must_stop:
            for other in other_vehicles:
                if other is self:
                    continue
                other_pos = other.get_pos()
                dist_ahead = self._get_distance_ahead_in_lane(other_pos.x, other_pos.y)
                if dist_ahead is not None and 0.0 < dist_ahead < 6.5:
                    # Car in front is close; stop or match speed
                    must_stop = True
                    break

        # Apply Speed Adjustments
        if must_stop:
            # Smoothly decelerate to a complete stop
            self.speed = max(0.0, self.speed - self.brake_decel_rate * dt)
        else:
            # Accelerate up to target cruising speed
            if self.speed < self.target_speed:
                self.speed = min(self.target_speed, self.speed + self.accel_rate * dt)

        # Translate Position along lane
        move_dist = self.speed * dt
        if self.direction == '+Y':
            self.pos_y += move_dist
            if self.pos_y > 170.0:  # Wrap around world bounds
                self.pos_y = -170.0
        elif self.direction == '-Y':
            self.pos_y -= move_dist
            if self.pos_y < -170.0:
                self.pos_y = 170.0
        elif self.direction == '+X':
            self.pos_x += move_dist
            if self.pos_x > 170.0:
                self.pos_x = -170.0
        elif self.direction == '-X':
            self.pos_x -= move_dist
            if self.pos_x < -170.0:
                self.pos_x = 170.0

        # Update Scenegraph Position
        self.root.setX(self.pos_x)
        self.root.setY(self.pos_y)

        # Spin Wheels
        spin_delta = math.degrees((self.speed * dt) / 0.34)
        self.wheel_spin = (self.wheel_spin + spin_delta) % 360.0
        for w in self.wheels:
            w.setP(self.wheel_spin)

    def _evaluate_signal(self, signal: TrafficLightSignal) -> bool:
        """
        Checks if the upcoming traffic light is within stopping range and is RED or YELLOW.
        """
        lane_tolerance = 4.0
        stop_line_margin = signal.stop_dist

        if self.direction == '+Y':
            # Approaching from South
            if abs(self.pos_x - signal.cx) < lane_tolerance:
                stop_y = signal.cy - stop_line_margin
                dist_to_stop = stop_y - self.pos_y
                if 0.5 < dist_to_stop < 18.0:
                    state = signal.get_state_for_approach("S")
                    return state in ("RED", "YELLOW")

        elif self.direction == '-Y':
            # Approaching from North
            if abs(self.pos_x - signal.cx) < lane_tolerance:
                stop_y = signal.cy + stop_line_margin
                dist_to_stop = self.pos_y - stop_y
                if 0.5 < dist_to_stop < 18.0:
                    state = signal.get_state_for_approach("N")
                    return state in ("RED", "YELLOW")

        elif self.direction == '+X':
            # Approaching from West
            if abs(self.pos_y - signal.cy) < lane_tolerance:
                stop_x = signal.cx - stop_line_margin
                dist_to_stop = stop_x - self.pos_x
                if 0.5 < dist_to_stop < 18.0:
                    state = signal.get_state_for_approach("W")
                    return state in ("RED", "YELLOW")

        elif self.direction == '-X':
            # Approaching from East
            if abs(self.pos_y - signal.cy) < lane_tolerance:
                stop_x = signal.cx + stop_line_margin
                dist_to_stop = self.pos_x - stop_x
                if 0.5 < dist_to_stop < 18.0:
                    state = signal.get_state_for_approach("E")
                    return state in ("RED", "YELLOW")

        return False

    def _get_distance_ahead_in_lane(self, ox: float, oy: float) -> Optional[float]:
        """Returns distance to another vehicle if it is ahead in the same road lane."""
        lateral_threshold = 2.4  # Within current lane width

        if self.direction == '+Y':
            if abs(ox - self.pos_x) < lateral_threshold and oy > self.pos_y:
                return oy - self.pos_y
        elif self.direction == '-Y':
            if abs(ox - self.pos_x) < lateral_threshold and oy < self.pos_y:
                return self.pos_y - oy
        elif self.direction == '+X':
            if abs(oy - self.pos_y) < lateral_threshold and ox > self.pos_x:
                return ox - self.pos_x
        elif self.direction == '-X':
            if abs(oy - self.pos_y) < lateral_threshold and ox < self.pos_x:
                return self.pos_x - ox
        return None


class TrafficSystem:
    """Manages all urban traffic signals and autonomous NPC fleet."""

    def __init__(self, render: NodePath, grid_stride: float = 70.0, num_blocks: int = 4):
        self.render = render
        self.grid_stride = grid_stride
        self.num_blocks = num_blocks

        self.signals: List[TrafficLightSignal] = []
        self.npc_cars: List[NPCVehicle] = []

        self._spawn_traffic_signals()
        self._spawn_npc_fleet()

    def _spawn_traffic_signals(self):
        """Places traffic light gantries at each 4-way street intersection."""
        half_span = (self.num_blocks * self.grid_stride) * 0.5
        coords = [-half_span + i * self.grid_stride for i in range(self.num_blocks + 1)]

        for cx in coords:
            for cy in coords:
                signal = TrafficLightSignal(self.render, cx, cy, road_width=14.0)
                self.signals.append(signal)

    def _spawn_npc_fleet(self):
        """Spawns an active fleet of varied NPC cars cruising the road corridors."""
        half_span = (self.num_blocks * self.grid_stride) * 0.5
        corridors = [-half_span + i * self.grid_stride for i in range(self.num_blocks + 1)]

        # Lane offsets for right-hand traffic (3.5m offset from yellow center stripe)
        lane_offset = 3.5

        # 1. North-South corridor cars (+Y and -Y)
        for i, cx in enumerate(corridors):
            # +Y Lane (driving North, X = cx + 3.5)
            # Offset main starting corridor (cx == 0) so player has a clear runway at spawn
            y_start_1 = 30.0 if abs(cx) < 0.1 else (-120.0 + (i * 42.0))
            car1 = NPCVehicle(self.render, cx + lane_offset, y_start_1, direction='+Y',
                              model_type='sedan')
            self.npc_cars.append(car1)

            # -Y Lane (driving South, X = cx - 3.5)
            y_start_2 = 120.0 - (i * 42.0)
            car2 = NPCVehicle(self.render, cx - lane_offset, y_start_2, direction='-Y',
                              model_type='suv')
            self.npc_cars.append(car2)

        # 2. East-West corridor cars (+X and -X)
        for j, cy in enumerate(corridors):
            # +X Lane (driving East, Y = cy - 3.5)
            x_start_1 = -110.0 + (j * 42.0)
            car3 = NPCVehicle(self.render, x_start_1, cy - lane_offset, direction='+X',
                              model_type='sedan')
            self.npc_cars.append(car3)

            # -X Lane (driving West, Y = cy + 3.5)
            x_start_2 = 110.0 - (j * 42.0)
            car4 = NPCVehicle(self.render, x_start_2, cy + lane_offset, direction='-X',
                              model_type='suv')
            self.npc_cars.append(car4)

    def update(self, dt: float, player_car):
        """Updates traffic signal timings and NPC vehicle decisions."""
        # 1. Update Signals
        for sig in self.signals:
            sig.update(dt)

        # 2. Update NPC Vehicles (passing player car and fellow NPCs for collision/headway checks)
        all_tracked_vehicles = [player_car] + self.npc_cars
        for npc in self.npc_cars:
            npc.update(dt, self.signals, all_tracked_vehicles)

    def get_upcoming_signal_for_car(self, car_pos: Vec3, car_heading: float) -> Optional[str]:
        """
        Determines the state of the traffic light ahead of a vehicle (e.g. Player).
        Returns 'GREEN', 'YELLOW', 'RED', or None if not approaching an intersection.
        """
        # Determine dominant travel direction from heading (Panda3D: 0 = +Y, 90 = -X, 180 = -Y, 270 = +X)
        h = car_heading % 360.0
        if 315 <= h or h < 45:
            direction = '+Y'
            approach_key = 'S'
        elif 45 <= h < 135:
            direction = '-X'
            approach_key = 'E'
        elif 135 <= h < 225:
            direction = '-Y'
            approach_key = 'N'
        else:
            direction = '+X'
            approach_key = 'W'

        # Look for signal directly ahead (within 35m)
        for sig in self.signals:
            if direction == '+Y':
                if abs(car_pos.x - sig.cx) < 5.0 and 0.0 < (sig.cy - car_pos.y) < 35.0:
                    return sig.get_state_for_approach(approach_key)
            elif direction == '-Y':
                if abs(car_pos.x - sig.cx) < 5.0 and 0.0 < (car_pos.y - sig.cy) < 35.0:
                    return sig.get_state_for_approach(approach_key)
            elif direction == '+X':
                if abs(car_pos.y - sig.cy) < 5.0 and 0.0 < (sig.cx - car_pos.x) < 35.0:
                    return sig.get_state_for_approach(approach_key)
            elif direction == '-X':
                if abs(car_pos.y - sig.cy) < 5.0 and 0.0 < (car_pos.x - sig.cx) < 35.0:
                    return sig.get_state_for_approach(approach_key)

        return None
