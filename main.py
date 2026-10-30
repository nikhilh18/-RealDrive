"""
===============================================================================
RealDrive - 3D Driving Simulator in Python & Panda3D
===============================================================================

FEATURES IN THIS VERSION:
-------------------------
- Player Vehicle: Realistic procedural Porsche 911 (Guards Red) with authentic
  curved teardrop fastback roofline ("flyline"), raised front fender humps with
  xenon headlights, flared rear haunches, and a modern slim LED rear lightbar.
- Moving NPC Traffic: Autonomous AI fleet cruising the grid in legal lanes,
  maintaining safe headway, and obeying all traffic signals.
- Traffic Light System: 4-way intersection signal gantries cycling through
  Green, Yellow, and Red phases.
- Traffic Law Freedom: NPC cars strictly stop at red/yellow lights, but the player
  has total freedom to obey or run red lights!
- Solid Collision & Crash Engine: Strict physical collision detection against
  buildings, trees, and other cars. Vehicles cannot pass through objects.
  High-speed impacts trigger crash recoil, damage states, and HUD alerts.
- Multi-Camera Views: Chase View (3rd person), Cockpit View (1st person), and
  Top-Down View (tactical grid).
- Dual Controls: Works seamlessly via keyboard and on-screen DirectGUI buttons.

HOW TO RUN:
-----------
1. Install Panda3D if not already installed:
       pip install panda3d
2. Run from the project directory in VS Code or Terminal:
       python main.py

CONTROLS:
---------
- W or Up Arrow       : Accelerate forward (Drive gear)
- S or Down Arrow     : Brake / Hold to reverse (Reverse gear)
- A or Left Arrow     : Steer left
- D or Right Arrow    : Steer right
- C                   : Cycle camera view (Chase -> Cockpit -> Top-Down)
- R                   : Reset car to initial position (recovers from crashes)
- Escape              : Exit simulator
- Mouse Left-Click    : Interact with on-screen dashboard buttons
===============================================================================
"""

import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    WindowProperties,
    Vec3,
    Vec4,
)

from vehicle import Vehicle
from environment import CityEnvironment
from camera_controller import CameraController
from hud import HUD
from collision_system import CollisionSystem
from traffic_system import TrafficSystem


class RealDriveApp(ShowBase):
    """Main application coordinator managing vehicle, traffic, collisions, and HUD."""

    def __init__(self):
        super().__init__()

        # 1. Configure Window Properties (if running with graphical window)
        if self.win:
            props = WindowProperties()
            props.setTitle("RealDrive - 3D Driving Simulator (Porsche 911 & Traffic)")
            props.setSize(1280, 720)
            self.win.requestProperties(props)
            self.win.setClearColor(Vec4(0.53, 0.81, 0.98, 1.0))
            self.disableMouse()
            self.setFrameRateMeter(True)

        # 2. Collision System
        print("[RealDrive] Initializing collision physics engine...")
        self.collision_system = CollisionSystem()

        # 3. Environment & Obstacles
        print("[RealDrive] Generating procedural 3D city environment...")
        self.environment = CityEnvironment(self.render, collision_system=self.collision_system)

        # 4. Traffic System (Signals & Autonomous NPC Fleet)
        print("[RealDrive] Initializing traffic signals & NPC traffic fleet...")
        self.traffic_system = TrafficSystem(self.render, grid_stride=70.0, num_blocks=4)

        # 5. Player Vehicle (Porsche 911)
        print("[RealDrive] Spawning Porsche 911 player vehicle...")
        # Start vehicle on right side of avenue facing +Y
        self.initial_pos = Vec3(3.5, -60.0, 0.0)
        self.initial_heading = 0.0
        self.vehicle = Vehicle(self.render, init_pos=self.initial_pos, init_heading=self.initial_heading)

        # 6. Camera Controller
        print("[RealDrive] Initializing dynamic camera controller...")
        self.camera_controller = CameraController(self.camera)

        # 7. DirectGUI Dashboard HUD
        print("[RealDrive] Initializing DirectGUI cockpit dashboard...")
        self.hud = HUD(
            on_camera_toggle_callback=self._toggle_camera,
            on_reset_callback=self._reset_vehicle,
        )

        # 8. Input Event Tracking
        self.keys = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
        }
        self._setup_input_bindings()

        # 9. Attach Main Game Loop
        self.taskMgr.add(self.update_simulation, "simulation_loop")
        print("[RealDrive] RealDrive is live! Drive your Porsche 911 with WASD or GUI.")

    # -------------------------------------------------------------------------
    # Input Event Bindings
    # -------------------------------------------------------------------------
    def _setup_input_bindings(self):
        """Binds keyboard inputs for throttle, steering, camera, and reset."""
        # Throttle (Forward)
        self.accept("w", self._set_key, ["forward", True])
        self.accept("w-up", self._set_key, ["forward", False])
        self.accept("arrow_up", self._set_key, ["forward", True])
        self.accept("arrow_up-up", self._set_key, ["forward", False])

        # Brake / Reverse
        self.accept("s", self._set_key, ["backward", True])
        self.accept("s-up", self._set_key, ["backward", False])
        self.accept("arrow_down", self._set_key, ["backward", True])
        self.accept("arrow_down-up", self._set_key, ["backward", False])

        # Steer Left
        self.accept("a", self._set_key, ["left", True])
        self.accept("a-up", self._set_key, ["left", False])
        self.accept("arrow_left", self._set_key, ["left", True])
        self.accept("arrow_left-up", self._set_key, ["left", False])

        # Steer Right
        self.accept("d", self._set_key, ["right", True])
        self.accept("d-up", self._set_key, ["right", False])
        self.accept("arrow_right", self._set_key, ["right", True])
        self.accept("arrow_right-up", self._set_key, ["right", False])

        # Camera Mode Toggle
        self.accept("c", self._toggle_camera)

        # Reset Car
        self.accept("r", self._reset_vehicle)

        # Exit
        self.accept("escape", sys.exit)

    def _set_key(self, key_name: str, state: bool):
        self.keys[key_name] = state

    def _toggle_camera(self):
        self.camera_controller.toggle_mode()

    def _reset_vehicle(self):
        self.vehicle.reset(self.initial_pos, self.initial_heading)
        self.camera_controller.snap_next_frame = True

    # -------------------------------------------------------------------------
    # Main Simulation Loop
    # -------------------------------------------------------------------------
    def update_simulation(self, task):
        dt = globalClock.getDt()

        # 1. Combine Keyboard + DirectGUI On-Screen Inputs
        throttle = 1.0 if (self.keys["forward"] or self.hud.get_throttle_input() > 0.0) else 0.0
        brake = 1.0 if (self.keys["backward"] or self.hud.get_brake_input() > 0.0) else 0.0
        steer_left = self.keys["left"] or self.hud.get_steer_left_input()
        steer_right = self.keys["right"] or self.hud.get_steer_right_input()

        # 2. Update Player Vehicle Kinematics
        self.vehicle.update(dt, throttle, brake, steer_left, steer_right)

        # 3. Update Traffic Signals & Autonomous NPC Fleet
        self.traffic_system.update(dt, self.vehicle)

        # 4. Resolve Physical Collisions (Prevents Passing Through Objects)
        # Player vs Buildings & Trees
        self.collision_system.resolve_vehicle_world(self.vehicle)

        # Player vs NPC Vehicles
        for npc in self.traffic_system.npc_cars:
            self.collision_system.resolve_vehicle_vehicle(self.vehicle, npc)

        # NPCs vs Buildings & Trees
        for npc in self.traffic_system.npc_cars:
            self.collision_system.resolve_vehicle_world(npc)

        # 5. Update Camera Controller
        self.camera_controller.update(dt, self.vehicle)

        # 6. Query Upcoming Traffic Light Ahead of Player
        signal_ahead = self.traffic_system.get_upcoming_signal_for_car(
            self.vehicle.get_pos(), self.vehicle.get_heading()
        )

        # 7. Update Dashboard Telemetry & Crash Alert Banner
        speed_kmh = self.vehicle.get_speed_kmh()
        gear = self.vehicle.get_gear()
        cam_mode = self.camera_controller.get_mode_name()
        is_crashed = self.vehicle.is_crashed()

        self.hud.update(
            speed_kmh=speed_kmh,
            gear=gear,
            camera_mode_name=cam_mode,
            signal_state=signal_ahead,
            is_crashed=is_crashed,
        )

        return task.cont


if __name__ == "__main__":
    app = RealDriveApp()
    app.run()
