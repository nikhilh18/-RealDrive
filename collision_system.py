"""
collision_system.py - Collision Detection & Crash Physics Engine for RealDrive
-----------------------------------------------------------------------------
Manages solid physical obstacle boundaries and dynamic vehicle-to-vehicle,
vehicle-to-building, and vehicle-to-tree collisions:

- Prevents vehicles from passing through solid objects (walls, curbs, trees, other cars)
  by calculating penetration vectors and projecting positions out along contact normals.
- Imparts elastic/inelastic crash impulses and velocity rebound.
- Detects high-speed impacts to trigger crash events and damage alerts.
"""

import math
from typing import List, Tuple, Optional


class BoxCollider:
    """Axis-Aligned or Oriented 2D Box Collider (X, Y plane)."""

    def __init__(self, min_x: float, max_x: float, min_y: float, max_y: float, tag: str = "building"):
        self.min_x = min(min_x, max_x)
        self.max_x = max(min_x, max_x)
        self.min_y = min(min_y, max_y)
        self.max_y = max(min_y, max_y)
        self.tag = tag

    def test_circle(self, cx: float, cy: float, radius: float) -> Optional[Tuple[float, float, float]]:
        """
        Tests intersection against a circle (used for rapid broadphase/curbs).
        Returns (normal_x, normal_y, penetration_depth) or None.
        """
        # Find closest point on AABB to circle center
        closest_x = max(self.min_x, min(cx, self.max_x))
        closest_y = max(self.min_y, min(cy, self.max_y))

        diff_x = cx - closest_x
        diff_y = cy - closest_y
        dist_sq = diff_x * diff_x + diff_y * diff_y

        if dist_sq < (radius * radius):
            dist = math.sqrt(dist_sq)
            if dist > 0.0001:
                nx = diff_x / dist
                ny = diff_y / dist
                pen = radius - dist
            else:
                # Center is inside box; push toward closest box face
                d_left = abs(cx - self.min_x)
                d_right = abs(self.max_x - cx)
                d_bottom = abs(cy - self.min_y)
                d_top = abs(self.max_y - cy)
                min_d = min(d_left, d_right, d_bottom, d_top)
                if min_d == d_left:
                    nx, ny, pen = -1.0, 0.0, radius + d_left
                elif min_d == d_right:
                    nx, ny, pen = 1.0, 0.0, radius + d_right
                elif min_d == d_bottom:
                    nx, ny, pen = 0.0, -1.0, radius + d_bottom
                else:
                    nx, ny, pen = 0.0, 1.0, radius + d_top
            return nx, ny, pen
        return None


class TreeCollider:
    """Circular cylinder collider for street trees and lamp poles."""

    def __init__(self, x: float, y: float, radius: float = 0.65):
        self.x = x
        self.y = y
        self.radius = radius

    def test_circle(self, cx: float, cy: float, radius: float) -> Optional[Tuple[float, float, float]]:
        """Returns (normal_x, normal_y, penetration_depth) or None."""
        dx = cx - self.x
        dy = cy - self.y
        dist_sq = dx * dx + dy * dy
        min_dist = self.radius + radius

        if dist_sq < (min_dist * min_dist):
            dist = math.sqrt(dist_sq)
            if dist > 0.0001:
                return dx / dist, dy / dist, min_dist - dist
            else:
                return 1.0, 0.0, min_dist
        return None


class CollisionSystem:
    """World-wide collision manager coordinating static and dynamic bodies."""

    def __init__(self):
        self.static_boxes: List[BoxCollider] = []
        self.static_trees: List[TreeCollider] = []

    def add_building_box(self, cx: float, cy: float, width: float, depth: float):
        """Registers a rectangular building boundary."""
        hw = width * 0.5
        hd = depth * 0.5
        self.static_boxes.append(BoxCollider(cx - hw, cx + hw, cy - hd, cy + hd, tag="building"))

    def add_tree(self, x: float, y: float, radius: float = 0.65):
        """Registers a tree obstacle."""
        self.static_trees.append(TreeCollider(x, y, radius))

    def resolve_vehicle_world(self, car) -> Optional[dict]:
        """
        Tests and resolves vehicle collisions against static buildings and trees.
        Pushes vehicle out of penetration and applies bounce/crash impulse.
        
        Returns crash event dict if high-speed impact occurred, else None.
        """
        pos = car.get_pos()
        car_radius = 1.35  # Effective physical bounding radius
        crash_event = None

        # 1. Test against Buildings
        for box in self.static_boxes:
            result = box.test_circle(pos.x, pos.y, car_radius)
            if result:
                nx, ny, pen = result
                # Project car completely out of obstacle
                car.pos_x += nx * pen
                car.pos_y += ny * pen
                car.root.setX(car.pos_x)
                car.root.setY(car.pos_y)

                # Calculate impact severity
                speed = car.speed
                if abs(speed) > 1.4:  # > ~5 km/h
                    car.on_crash(impact_intensity=abs(speed))
                    crash_event = {
                        "type": "building",
                        "speed_kmh": car.get_speed_kmh(),
                    }

                # Elastic rebound / stop forward penetration
                car.speed = -car.speed * 0.28
                break

        # 2. Test against Trees
        pos = car.get_pos()
        for tree in self.static_trees:
            result = tree.test_circle(pos.x, pos.y, car_radius)
            if result:
                nx, ny, pen = result
                car.pos_x += nx * pen
                car.pos_y += ny * pen
                car.root.setX(car.pos_x)
                car.root.setY(car.pos_y)

                speed = car.speed
                if abs(speed) > 1.4:
                    car.on_crash(impact_intensity=abs(speed))
                    crash_event = {
                        "type": "tree",
                        "speed_kmh": car.get_speed_kmh(),
                    }

                car.speed = -car.speed * 0.25
                break

        return crash_event

    def resolve_vehicle_vehicle(self, car_a, car_b) -> Optional[dict]:
        """
        Tests and resolves vehicle-to-vehicle collision between two cars.
        Pushes both cars apart and applies momentum transfer.
        """
        pos_a = car_a.get_pos()
        pos_b = car_b.get_pos()

        dx = pos_a.x - pos_b.x
        dy = pos_a.y - pos_b.y
        dist_sq = dx * dx + dy * dy
        min_dist = 2.45  # Sum of vehicle physical collision radii

        if dist_sq < (min_dist * min_dist):
            dist = math.sqrt(dist_sq)
            if dist > 0.0001:
                nx = dx / dist
                ny = dy / dist
                pen = min_dist - dist
            else:
                nx, ny, pen = 1.0, 0.0, min_dist

            # Push cars apart equally
            half_pen = pen * 0.5
            car_a.pos_x += nx * half_pen
            car_a.pos_y += ny * half_pen
            car_b.pos_x -= nx * half_pen
            car_b.pos_y -= ny * half_pen

            car_a.root.setX(car_a.pos_x)
            car_a.root.setY(car_a.pos_y)
            car_b.root.setX(car_b.pos_x)
            car_b.root.setY(car_b.pos_y)

            # Impact recoil and crash trigger
            rel_speed = abs(car_a.speed - car_b.speed)
            car_a.speed = -car_a.speed * 0.3
            car_b.speed = -car_b.speed * 0.3

            if rel_speed > 1.4 or abs(car_a.speed) > 1.4 or abs(car_b.speed) > 1.4:
                car_a.on_crash(impact_intensity=max(abs(car_a.speed), rel_speed))
                car_b.on_crash(impact_intensity=max(abs(car_b.speed), rel_speed))
                return {
                    "type": "vehicle",
                    "speed_kmh": max(car_a.get_speed_kmh(), car_b.get_speed_kmh()),
                }

        return None
