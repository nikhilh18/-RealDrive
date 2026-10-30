"""
environment.py - Procedural City Environment for RealDrive
-----------------------------------------------------------
This module generates an interactive 3D city scene featuring:
- An asphalt road grid network with yellow lane markings and white crosswalk/stop lines
- Raised concrete sidewalks with curbs along street perimeters
- A variety of commercial and residential buildings with collision boundaries
- Foliage trees lining the sidewalks with solid trunk colliders
- Ambient and directional sun lighting for realistic scene illumination
"""

import random
from panda3d.core import (
    NodePath,
    Vec3,
    Vec4,
    AmbientLight,
    DirectionalLight,
)
from utils import create_box, create_cylinder, create_plane


class CityEnvironment:
    """Manages procedural generation of the 3D city scene and registers solid obstacles."""

    def __init__(self, render: NodePath, collision_system=None):
        """
        Initializes and builds the city scene attached to render.
        
        Args:
            render: Root Panda3D render NodePath.
            collision_system: Optional CollisionSystem to register static obstacles.
        """
        self.root = NodePath("city_root")
        self.root.reparentTo(render)
        self.collision_system = collision_system

        # City Grid Configuration
        self.grid_blocks_x = 4      # Number of city blocks along X
        self.grid_blocks_y = 4      # Number of city blocks along Y
        self.block_size = 56.0      # Size of each city block (meters)
        self.road_width = 14.0      # Street asphalt width (meters)
        self.sidewalk_width = 2.5   # Sidewalk width on each side of the road
        self.stride = self.block_size + self.road_width  # Total distance between block centers (70m)

        # Seed random number generator for reproducible procedural city generation
        self.rng = random.Random(42)

        # Build environment components
        self._setup_lighting(render)
        self._build_ground_plane()
        self._build_road_network()
        self._build_sidewalks_and_blocks()

    # -------------------------------------------------------------------------
    # Lighting Setup
    # -------------------------------------------------------------------------
    def _setup_lighting(self, render: NodePath):
        """Sets up a two-source lighting model (Sunlight + Sky Ambient)."""
        dlight = DirectionalLight("sun_light")
        dlight.setColor(Vec4(0.92, 0.90, 0.85, 1.0))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(-45, -50, 0)
        render.setLight(dlnp)

        alight = AmbientLight("ambient_light")
        alight.setColor(Vec4(0.48, 0.50, 0.56, 1.0))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)

    # -------------------------------------------------------------------------
    # Ground & Road Grid Network
    # -------------------------------------------------------------------------
    def _build_ground_plane(self):
        """Builds an expansive green suburban terrain plane beneath the city."""
        grass_color = Vec4(0.24, 0.44, 0.22, 1.0)
        ground = create_plane(width=650.0, length=650.0, color=grass_color)
        ground.setPos(0, 0, -0.05)
        ground.reparentTo(self.root)

    def _build_road_network(self):
        """Constructs asphalt road corridors, lane dividers, and intersection stop lines."""
        road_color = Vec4(0.18, 0.19, 0.21, 1.0)
        stripe_color = Vec4(0.95, 0.82, 0.15, 1.0)   # Yellow center line
        stop_line_color = Vec4(0.92, 0.92, 0.95, 1.0) # White stop line

        half_span_x = (self.grid_blocks_x * self.stride) * 0.5
        half_span_y = (self.grid_blocks_y * self.stride) * 0.5
        total_road_len_x = self.grid_blocks_x * self.stride + 40.0
        total_road_len_y = self.grid_blocks_y * self.stride + 40.0

        corridor_coords = [-half_span_x + i * self.stride for i in range(self.grid_blocks_x + 1)]

        # North-South road corridors
        for rx in corridor_coords:
            road_surface = create_box(dx=self.road_width, dy=total_road_len_y, dz=0.06, color=road_color)
            road_surface.setPos(rx, 0, 0.02)
            road_surface.reparentTo(self.root)

            # Center dividing dashed stripe
            stripe_count = int(total_road_len_y / 8.0)
            for s in range(-stripe_count // 2, stripe_count // 2):
                dash = create_box(dx=0.25, dy=3.5, dz=0.08, color=stripe_color)
                dash.setPos(rx, s * 8.0, 0.035)
                dash.reparentTo(self.root)

        # East-West road corridors
        for ry in corridor_coords:
            road_surface = create_box(dx=total_road_len_x, dy=self.road_width, dz=0.05, color=road_color)
            road_surface.setPos(0, ry, 0.015)
            road_surface.reparentTo(self.root)

            stripe_count = int(total_road_len_x / 8.0)
            for s in range(-stripe_count // 2, stripe_count // 2):
                dash = create_box(dx=3.5, dy=0.25, dz=0.08, color=stripe_color)
                dash.setPos(s * 8.0, ry, 0.035)
                dash.reparentTo(self.root)

        # Paint White Stop Lines at all 4 approaches to every intersection
        stop_offset = (self.road_width * 0.5) + 1.2
        for cx in corridor_coords:
            for cy in corridor_coords:
                # Northbound (+Y) stop line on right side (x > cx)
                s_line = create_box(dx=5.5, dy=0.45, dz=0.08, color=stop_line_color)
                s_line.setPos(cx + 3.5, cy - stop_offset, 0.04)
                s_line.reparentTo(self.root)

                # Southbound (-Y) stop line on right side (x < cx)
                n_line = create_box(dx=5.5, dy=0.45, dz=0.08, color=stop_line_color)
                n_line.setPos(cx - 3.5, cy + stop_offset, 0.04)
                n_line.reparentTo(self.root)

                # Eastbound (+X) stop line on right side (y < cy)
                w_line = create_box(dx=0.45, dy=5.5, dz=0.08, color=stop_line_color)
                w_line.setPos(cx - stop_offset, cy - 3.5, 0.04)
                w_line.reparentTo(self.root)

                # Westbound (-X) stop line on right side (y > cy)
                e_line = create_box(dx=0.45, dy=5.5, dz=0.08, color=stop_line_color)
                e_line.setPos(cx + stop_offset, cy + 3.5, 0.04)
                e_line.reparentTo(self.root)

    # -------------------------------------------------------------------------
    # Sidewalks, Buildings, and Trees
    # -------------------------------------------------------------------------
    def _build_sidewalks_and_blocks(self):
        """Populates city blocks with sidewalks, buildings, and perimeter trees."""
        sidewalk_color = Vec4(0.68, 0.69, 0.70, 1.0)
        curb_height = 0.22

        building_palettes = [
            Vec4(0.25, 0.38, 0.52, 1.0),  # Steel Blue Glass Office
            Vec4(0.32, 0.34, 0.38, 1.0),  # Dark Granite Tower
            Vec4(0.62, 0.36, 0.28, 1.0),  # Terracotta Brick Residential
            Vec4(0.72, 0.68, 0.60, 1.0),  # Warm Sandstone Commercial
            Vec4(0.42, 0.46, 0.50, 1.0),  # Slate Concrete Skyscraper
            Vec4(0.22, 0.45, 0.48, 1.0),  # Emerald Glass High-Rise
        ]

        half_span_x = (self.grid_blocks_x * self.stride) * 0.5
        half_span_y = (self.grid_blocks_y * self.stride) * 0.5

        for i in range(self.grid_blocks_x):
            for j in range(self.grid_blocks_y):
                bx = -half_span_x + (i + 0.5) * self.stride
                by = -half_span_y + (j + 0.5) * self.stride

                # Raised Concrete Sidewalk Base
                block_pad = create_box(dx=self.block_size, dy=self.block_size, dz=curb_height,
                                       color=sidewalk_color)
                block_pad.setPos(bx, by, curb_height * 0.5)
                block_pad.reparentTo(self.root)

                # Buildings
                self._populate_block_buildings(bx, by, building_palettes)

                # Trees
                self._populate_block_trees(bx, by)

    def _populate_block_buildings(self, bx: float, by: float, palettes: list):
        """Generates 1 to 4 buildings per block and registers solid colliders."""
        inner_size = self.block_size - (self.sidewalk_width * 2.0) - 2.0
        half_inner = inner_size * 0.5

        layout_type = self.rng.choice(["single_tower", "multi_building"])

        if layout_type == "single_tower":
            w = self.rng.uniform(22.0, 32.0)
            d = self.rng.uniform(22.0, 32.0)
            h = self.rng.uniform(35.0, 75.0)
            color = self.rng.choice(palettes)

            bldg = create_box(dx=w, dy=d, dz=h, color=color)
            bldg.setPos(bx, by, h * 0.5 + 0.22)
            bldg.reparentTo(self.root)

            # Roof spire
            roof_accent = create_box(dx=w * 0.5, dy=d * 0.5, dz=4.0, color=Vec4(0.2, 0.2, 0.22, 1.0))
            roof_accent.setPos(bx, by, h + 2.0 + 0.22)
            roof_accent.reparentTo(self.root)

            # Register solid obstacle
            if self.collision_system:
                self.collision_system.add_building_box(bx, by, w, d)

        else:
            offsets = [
                (-half_inner * 0.5, -half_inner * 0.5),
                (half_inner * 0.5, -half_inner * 0.5),
                (-half_inner * 0.5, half_inner * 0.5),
                (half_inner * 0.5, half_inner * 0.5),
            ]

            num_bldgs = self.rng.randint(2, 4)
            chosen_offsets = self.rng.sample(offsets, num_bldgs)

            for ox, oy in chosen_offsets:
                w = self.rng.uniform(14.0, 19.0)
                d = self.rng.uniform(14.0, 19.0)
                h = self.rng.uniform(16.0, 48.0)
                color = self.rng.choice(palettes)

                bldg = create_box(dx=w, dy=d, dz=h, color=color)
                bldg.setPos(bx + ox, by + oy, h * 0.5 + 0.22)
                bldg.reparentTo(self.root)

                # Register solid obstacle
                if self.collision_system:
                    self.collision_system.add_building_box(bx + ox, by + oy, w, d)

    def _populate_block_trees(self, bx: float, by: float):
        """Plants ornamental trees along sidewalk borders and registers solid colliders."""
        half_block = self.block_size * 0.5
        tree_inset = half_block - 1.2

        tree_positions = [
            (bx - 16.0, by - tree_inset), (bx, by - tree_inset), (bx + 16.0, by - tree_inset),
            (bx - 16.0, by + tree_inset), (bx, by + tree_inset), (bx + 16.0, by + tree_inset),
            (bx - tree_inset, by - 16.0), (bx - tree_inset, by), (bx - tree_inset, by + 16.0),
            (bx + tree_inset, by - 16.0), (bx + tree_inset, by), (bx + tree_inset, by + 16.0),
        ]

        for tx, ty in tree_positions:
            self._create_tree(tx, ty)

    def _create_tree(self, x: float, y: float):
        """Builds a procedural tree with a wooden trunk and layered foliage."""
        trunk_height = 2.4
        trunk_radius = 0.22
        trunk_color = Vec4(0.38, 0.25, 0.16, 1.0)
        foliage_color = Vec4(0.18, 0.58, 0.24, 1.0)
        foliage_accent = Vec4(0.22, 0.65, 0.28, 1.0)

        tree_node = NodePath("tree")
        tree_node.setPos(x, y, 0.22)
        tree_node.reparentTo(self.root)

        # Trunk
        trunk = create_cylinder(radius=trunk_radius, height=trunk_height, num_segments=8,
                                color=trunk_color, axis="z")
        trunk.setPos(0, 0, trunk_height * 0.5)
        trunk.reparentTo(tree_node)

        # Canopies
        foliage_lower = create_box(dx=2.4, dy=2.4, dz=1.8, color=foliage_color)
        foliage_lower.setPos(0, 0, trunk_height + 0.9)
        foliage_lower.setH(45)
        foliage_lower.reparentTo(tree_node)

        foliage_upper = create_box(dx=1.6, dy=1.6, dz=1.4, color=foliage_accent)
        foliage_upper.setPos(0, 0, trunk_height + 2.2)
        foliage_upper.reparentTo(tree_node)

        # Register tree trunk obstacle
        if self.collision_system:
            self.collision_system.add_tree(x, y, radius=0.65)
