"""
test_simulation.py - Automated Headless Simulation Test for RealDrive
---------------------------------------------------------------------
Tests RealDrive subsystems:
1. Vehicle Kinematics (acceleration, steering, reverse).
2. Traffic Light System (signal cycling: Green -> Yellow -> Red).
3. NPC Traffic Fleet (lane movement and following rules).
4. Collision & Crash Engine (solid obstacle penetration prevention & crash detection).
5. Camera Controller & DirectGUI HUD.
"""

import sys
from panda3d.core import loadPrcFileData

# Configure Panda3D to run headlessly for automated verification
loadPrcFileData("", "window-type none")
loadPrcFileData("", "audio-library-name null")

from panda3d.core import ClockObject, Vec3
from main import RealDriveApp


def run_tests():
    print("--- Starting RealDrive Automated Headless Verification ---")
    clock = ClockObject.getGlobalClock()
    clock.setMode(ClockObject.MNonRealTime)
    clock.setDt(1.0 / 60.0)
    app = RealDriveApp()

    v = app.vehicle
    cam = app.camera_controller
    hud = app.hud
    traffic = app.traffic_system
    collision = app.collision_system

    # Step 1: Initial state check
    print(f"Initial Vehicle Pos: {v.get_pos()}, Speed: {v.get_speed_kmh()} km/h, Gear: {v.get_gear()}")
    assert v.get_speed_kmh() == 0.0, "Initial speed should be 0"
    assert cam.get_mode_name() == "Chase View", f"Expected Chase View, got {cam.get_mode_name()}"
    assert len(traffic.signals) > 0, "Traffic signals should be spawned across intersections"
    assert len(traffic.npc_cars) > 0, "NPC cars should be spawned in traffic fleet"

    # Step 2: Simulate forward acceleration for 2.0s
    print("\nSimulating forward acceleration for 2.0s...")
    app.keys["forward"] = True
    for _ in range(120):
        app.taskMgr.step()
    app.keys["forward"] = False

    speed_after_accel = v.get_speed_kmh()
    pos_after_accel = v.get_pos()
    print(f"After Accel -> Pos: {pos_after_accel}, Speed: {speed_after_accel:.2f} km/h, Gear: {v.get_gear()}")
    assert speed_after_accel > 10.0, "Porsche 911 should have accelerated forward"
    assert v.get_gear() == "D", "Gear should be Drive ('D')"
    assert pos_after_accel.y > -60.0, "Car Y coordinate should have advanced forward"

    # Step 3: Simulate steering left
    print("\nSimulating steering left for 1.5s...")
    app.keys["forward"] = True
    app.keys["left"] = True
    for _ in range(90):
        app.taskMgr.step()
    app.keys["forward"] = False
    app.keys["left"] = False

    heading_after_steer = v.get_heading()
    print(f"After Steer -> Heading: {heading_after_steer:.2f} deg, Pos: {v.get_pos()}")
    assert heading_after_steer > 0.0, "Heading should have increased counter-clockwise (turned left)"

    # Step 4: Simulate braking to a stop and transitioning into reverse
    print("\nSimulating braking and reversing for 3.0s...")
    app.keys["backward"] = True
    for _ in range(180):
        app.taskMgr.step()
    app.keys["backward"] = False

    print(f"After Brake/Rev -> Speed: {v.get_speed_kmh():.2f} km/h, Gear: {v.get_gear()}")
    assert v.get_gear() == "R", "Gear should transition to Reverse ('R')"

    # Step 5: Test Collision & Crash Detection (Car into Solid Obstacle)
    print("\nTesting Solid Collision & Crash Engine...")
    # Teleport car right in front of a registered building obstacle and drive into it
    first_box = collision.static_boxes[0]
    obstacle_front_x = (first_box.min_x + first_box.max_x) * 0.5
    obstacle_front_y = first_box.min_y - 2.0  # Just in front of building

    v.reset(pos=Vec3(obstacle_front_x, obstacle_front_y, 0), heading=0.0)
    v.speed = 15.0  # Driving directly toward +Y into building face
    print(f"Driving toward building at {obstacle_front_x}, {first_box.min_y}...")

    # Step simulation: vehicle should impact, rebound, and be blocked from entering building
    for _ in range(10):
        app.taskMgr.step()

    print(f"After impact -> Pos: {v.get_pos()}, Speed: {v.get_speed_kmh():.2f} km/h, Crashed: {v.is_crashed()}")
    assert v.pos_y <= first_box.min_y, "Vehicle must not penetrate inside building boundary!"
    assert v.is_crashed() is True, "Crash flag should be triggered on high-speed impact"

    # Step 6: Test Traffic Signal Light State Machine Cycling
    print("\nTesting Traffic Signal Light cycle...")
    test_sig = traffic.signals[0]
    initial_timer = test_sig.timer
    ns_state_1, ew_state_1 = test_sig.get_current_states()
    print(f"Signal Phase 1 -> NS: {ns_state_1}, EW: {ew_state_1}")

    # Advance time by 10 seconds (600 frames)
    for _ in range(600):
        app.taskMgr.step()

    ns_state_2, ew_state_2 = test_sig.get_current_states()
    print(f"Signal Phase 2 (after 10s) -> NS: {ns_state_2}, EW: {ew_state_2}")
    assert (ns_state_1, ew_state_1) != (ns_state_2, ew_state_2), "Signal states must cycle over time"

    # Step 7: Test NPC Traffic Fleet Movement
    print("\nTesting NPC Traffic Fleet movement...")
    first_npc = traffic.npc_cars[0]
    npc_initial_pos = first_npc.get_pos()
    print(f"NPC Initial Pos: {npc_initial_pos}, Speed: {first_npc.get_speed_kmh():.1f} km/h")

    # Step simulation for 2 seconds
    for _ in range(120):
        app.taskMgr.step()

    npc_updated_pos = first_npc.get_pos()
    print(f"NPC Updated Pos: {npc_updated_pos}, Speed: {first_npc.get_speed_kmh():.1f} km/h")
    assert npc_updated_pos != npc_initial_pos, "NPC vehicles must navigate and move along lanes"

    # Step 8: Test Camera Mode Cycling
    print("\nTesting Camera Controller toggling...")
    initial_cam = cam.get_mode_name()
    app._toggle_camera()
    second_cam = cam.get_mode_name()
    app._toggle_camera()
    third_cam = cam.get_mode_name()
    app._toggle_camera()
    cycled_cam = cam.get_mode_name()

    print(f"Camera Cycle: {initial_cam} -> {second_cam} -> {third_cam} -> {cycled_cam}")
    assert initial_cam == "Chase View"
    assert second_cam == "Cockpit View"
    assert third_cam == "Top-Down View"
    assert cycled_cam == "Chase View"

    # Step 9: Test Vehicle Reset
    print("\nTesting Vehicle Reset...")
    app._reset_vehicle()
    print(f"After Reset -> Pos: {v.get_pos()}, Speed: {v.get_speed_kmh()} km/h, Crashed: {v.is_crashed()}")
    assert v.get_speed_kmh() == 0.0, "Speed should reset to 0"
    assert v.is_crashed() is False, "Crash flag should clear on reset"

    # Step 10: Test DirectGUI button input handling
    print("\nTesting HUD On-Screen button input queries...")
    hud._set_action_state("gas", True)
    assert hud.get_throttle_input() == 1.0, "Throttle input should be 1.0 when gas button active"
    hud._set_action_state("gas", False)
    assert hud.get_throttle_input() == 0.0, "Throttle input should be 0.0 when released"

    hud._set_action_state("steer_left", True)
    assert hud.get_steer_left_input() is True, "Steer left should be True"
    hud._set_action_state("steer_left", False)

    print("\n--- ALL TESTS PASSED SUCCESSFULLY! ---")
    sys.exit(0)


if __name__ == "__main__":
    run_tests()
