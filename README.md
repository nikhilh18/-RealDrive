# RealDrive - 3D Driving Simulator in Python & Panda3D

**RealDrive** is an interactive, modular 3D driving simulator built using Python, Panda3D, and trigonometric vehicle mechanics. This edition features a procedural **Porsche 911**, an autonomous **NPC Traffic Fleet**, cycling **Traffic Signals** at 4-way intersections, and a **Solid Collision & Crash Engine**.

---

## What's New in this Version

1. **Porsche 911 Carrera (Guards Red)**:
   - Iconic low-slung sports car profile with curved fastback teardrop flyline.
   - Raised front fender humps with oval xenon headlights.
   - Flared widebody rear haunches and modern full-width slim rear LED lightbar.
   - Rear engine deck louvers, ducktail aerodynamic lip, dual chrome sports exhausts, and 20-inch staggered alloy wheels with red brake calipers.

2. **Moving NPC Traffic**:
   - Fleet of autonomous AI vehicles (sedans, SUVs, coupes) actively cruising the city grid in proper right-hand lanes.
   - Adaptive headway following: automatically maintains safe buffer distances behind other cars.

3. **4-Way Intersection Traffic Signals**:
   - Signal gantries with 3-lens housings at every intersection.
   - State machine cycling through **GREEN** $\rightarrow$ **YELLOW** $\rightarrow$ **RED**.
   - **Rules of the Road**: NPC cars strictly obey signals (stop before the white stop line on Red/Yellow). **You (the player) have total freedom** to obey signals or run red lights and navigate traffic as you wish!

4. **Solid Collision & Crash Engine**:
   - Vehicles cannot pass through buildings, trees, curbs, or other cars.
   - Physical penetration projection prevents ghosting through walls.
   - High-speed impacts impart elastic rebound impulses and trigger the on-screen **CRASH DETECTED** warning banner.

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.8+
- Panda3D:
  ```bash
  pip install panda3d
  ```

### 2. Running in VS Code or Terminal
Open VS Code in the project folder (`C:\Users\Nikhil\.gemini\antigravity\scratch\realdrive`):

```bash
cd C:\Users\Nikhil\.gemini\antigravity\scratch\realdrive
python main.py
```

To run the automated headless test suite:
```bash
python test_simulation.py
```

---

## Controls

| Action | Keyboard | DirectGUI On-Screen Control |
| :--- | :--- | :--- |
| **Accelerate** | `W` or `Up Arrow` | `[ GAS ^ ]` button (hold) |
| **Brake / Reverse** | `S` or `Down Arrow` | `[ BRAKE v ]` button (hold) |
| **Steer Left** | `A` or `Left Arrow` | `[ < LEFT ]` button (hold) |
| **Steer Right** | `D` or `Right Arrow` | `[ RIGHT > ]` button (hold) |
| **Switch Camera** | `C` | `[ CAM MODE (C) ]` button |
| **Reset Car** | `R` | `[ RESET CAR (R) ]` button |
| **Exit** | `Escape` | Window Close |

---

## Project Structure & Architecture

```
realdrive/
├── main.py                 # Application coordinator & main simulation loop
├── vehicle.py              # Porsche 911 procedural model, kinematics & crash state
├── traffic_system.py       # 4-way traffic signals & autonomous rule-following NPC fleet
├── collision_system.py     # Solid physical obstacle detection, rebound & crash mechanics
├── camera_controller.py    # Multi-mode camera (Chase, Cockpit, Top-down) with smooth follow
├── environment.py          # Procedural 3D city (roads, stop lines, sidewalks, buildings, trees)
├── hud.py                  # DirectGUI cockpit dashboard (speed, gear, signal badge, crash banner)
├── utils.py                # Procedural 3D geometry builders (boxes, cylinders, planes)
├── test_simulation.py      # Automated headless test suite
└── README.md               # Documentation and reference guide
```
