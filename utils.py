"""
utils.py - Procedural 3D Geometry Utilities for RealDrive
---------------------------------------------------------
This module provides helper functions to procedurally generate 3D meshes
(boxes, cylinders, planes, and compound shapes) using Panda3D's low-level
GeomVertexData and GeomTriangles classes.

Generating geometry procedurally allows the simulator to run immediately
upon installing Panda3D without requiring external 3D model files (.egg / .bam).
"""

import math
from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    GeomTriangles,
    Geom,
    GeomNode,
    NodePath,
    Vec3,
    Vec4,
)


def create_box(dx: float, dy: float, dz: float, color: Vec4 = Vec4(0.8, 0.8, 0.8, 1.0)) -> NodePath:
    """
    Creates a centered 3D box with proper face normals and vertex colors.
    
    Dimensions:
        dx: width along X axis (-dx/2 to +dx/2)
        dy: length along Y axis (-dy/2 to +dy/2)
        dz: height along Z axis (-dz/2 to +dz/2)
        color: RGBA vertex color (Vec4)
        
    Returns:
        NodePath containing the box geometry.
    """
    format_v3n3c4 = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("box_data", format_v3n3c4, Geom.UHStatic)
    
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    
    hx = dx * 0.5
    hy = dy * 0.5
    hz = dz * 0.5
    
    # 6 faces definition: (normal_vec, 4 corners in CCW order)
    faces = [
        # Front (+Y)
        (Vec3(0, 1, 0), [(-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]),
        # Back (-Y)
        (Vec3(0, -1, 0), [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, -hy, hz), (hx, -hy, hz)]),
        # Left (-X)
        (Vec3(-1, 0, 0), [(-hx, -hy, -hz), (-hx, hy, -hz), (-hx, hy, hz), (-hx, -hy, hz)]),
        # Right (+X)
        (Vec3(1, 0, 0), [(hx, hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (hx, -hy, hz)]),
        # Top (+Z)
        (Vec3(0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        # Bottom (-Z)
        (Vec3(0, 0, -1), [(-hx, hy, -hz), (hx, hy, -hz), (hx, -hy, -hz), (-hx, -hy, -hz)]),
    ]
    
    triangles = GeomTriangles(Geom.UHStatic)
    v_idx = 0
    
    for norm, corners in faces:
        for corner in corners:
            vertex.addData3(corner[0], corner[1], corner[2])
            normal.addData3(norm)
            color_w.addData4(color)
            
        # Two triangles per quad (0, 1, 2) and (0, 2, 3)
        triangles.addVertices(v_idx, v_idx + 1, v_idx + 2)
        triangles.addVertices(v_idx, v_idx + 2, v_idx + 3)
        v_idx += 4
        
    geom = Geom(vdata)
    geom.addPrimitive(triangles)
    
    node = GeomNode("procedural_box")
    node.addGeom(geom)
    return NodePath(node)


def create_cylinder(radius: float, height: float, num_segments: int = 16,
                    color: Vec4 = Vec4(0.2, 0.2, 0.2, 1.0), axis: str = "z") -> NodePath:
    """
    Creates a cylinder centered at the origin, useful for vehicle wheels and tree trunks.
    
    Args:
        radius: Radius of circular cross section.
        height: Total height along specified axis.
        num_segments: Number of angular slices.
        color: RGBA vertex color.
        axis: Cylinder alignment axis ('x', 'y', or 'z').
        
    Returns:
        NodePath containing the cylinder geometry.
    """
    format_v3n3c4 = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("cylinder_data", format_v3n3c4, Geom.UHStatic)
    
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    
    half_h = height * 0.5
    triangles = GeomTriangles(Geom.UHStatic)
    
    # Generate points around perimeter
    step = 2.0 * math.pi / num_segments
    
    # Helper to map standard (u, v, h) to target orientation axis
    def map_pos(u, v, h):
        if axis == "x":
            return Vec3(h, u, v)
        elif axis == "y":
            return Vec3(u, h, v)
        else:  # 'z'
            return Vec3(u, v, h)
            
    def map_norm(nu, nv, nh):
        if axis == "x":
            return Vec3(nh, nu, nv)
        elif axis == "y":
            return Vec3(nu, nh, nv)
        else:
            return Vec3(nu, nv, nh)

    v_idx = 0
    # Side quads
    for i in range(num_segments):
        a1 = i * step
        a2 = (i + 1) * step
        
        u1, v1 = math.cos(a1) * radius, math.sin(a1) * radius
        u2, v2 = math.cos(a2) * radius, math.sin(a2) * radius
        
        nu1, nv1 = math.cos(a1), math.sin(a1)
        nu2, nv2 = math.cos(a2), math.sin(a2)
        
        # 4 vertices for side quad
        p1 = map_pos(u1, v1, -half_h)
        p2 = map_pos(u2, v2, -half_h)
        p3 = map_pos(u2, v2, half_h)
        p4 = map_pos(u1, v1, half_h)
        
        n1 = map_norm(nu1, nv1, 0)
        n2 = map_norm(nu2, nv2, 0)
        n3 = map_norm(nu2, nv2, 0)
        n4 = map_norm(nu1, nv1, 0)
        
        vertex.addData3(p1)
        normal.addData3(n1)
        color_w.addData4(color)
        
        vertex.addData3(p2)
        normal.addData3(n2)
        color_w.addData4(color)
        
        vertex.addData3(p3)
        normal.addData3(n3)
        color_w.addData4(color)
        
        vertex.addData3(p4)
        normal.addData3(n4)
        color_w.addData4(color)
        
        triangles.addVertices(v_idx, v_idx + 1, v_idx + 2)
        triangles.addVertices(v_idx, v_idx + 2, v_idx + 3)
        v_idx += 4
        
    # Cap 1 (+half_h)
    cap1_center_idx = v_idx
    vertex.addData3(map_pos(0, 0, half_h))
    normal.addData3(map_norm(0, 0, 1))
    color_w.addData4(color)
    v_idx += 1
    
    for i in range(num_segments):
        a = i * step
        u, v = math.cos(a) * radius, math.sin(a) * radius
        vertex.addData3(map_pos(u, v, half_h))
        normal.addData3(map_norm(0, 0, 1))
        color_w.addData4(color)
        v_idx += 1
        
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        triangles.addVertices(cap1_center_idx, cap1_center_idx + 1 + i, cap1_center_idx + 1 + next_i)
        
    # Cap 2 (-half_h)
    cap2_center_idx = v_idx
    vertex.addData3(map_pos(0, 0, -half_h))
    normal.addData3(map_norm(0, 0, -1))
    color_w.addData4(color)
    v_idx += 1
    
    for i in range(num_segments):
        a = i * step
        u, v = math.cos(a) * radius, math.sin(a) * radius
        vertex.addData3(map_pos(u, v, -half_h))
        normal.addData3(map_norm(0, 0, -1))
        color_w.addData4(color)
        v_idx += 1
        
    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        triangles.addVertices(cap2_center_idx, cap2_center_idx + 1 + next_i, cap2_center_idx + 1 + i)
        
    geom = Geom(vdata)
    geom.addPrimitive(triangles)
    
    node = GeomNode("procedural_cylinder")
    node.addGeom(geom)
    return NodePath(node)


def create_plane(width: float, length: float, color: Vec4 = Vec4(0.3, 0.3, 0.3, 1.0)) -> NodePath:
    """
    Creates a horizontal flat plane centered at the origin on the XY plane with normal facing +Z.
    
    Args:
        width: Size along X axis.
        length: Size along Y axis.
        color: RGBA vertex color.
        
    Returns:
        NodePath containing the plane geometry.
    """
    format_v3n3c4 = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("plane_data", format_v3n3c4, Geom.UHStatic)
    
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    
    hw = width * 0.5
    hl = length * 0.5
    
    # 4 vertices
    corners = [(-hw, -hl, 0), (hw, -hl, 0), (hw, hl, 0), (-hw, hl, 0)]
    for c in corners:
        vertex.addData3(c[0], c[1], c[2])
        normal.addData3(0, 0, 1)
        color_w.addData4(color)
        
    triangles = GeomTriangles(Geom.UHStatic)
    triangles.addVertices(0, 1, 2)
    triangles.addVertices(0, 2, 3)
    
    geom = Geom(vdata)
    geom.addPrimitive(triangles)
    
    node = GeomNode("procedural_plane")
    node.addGeom(geom)
    return NodePath(node)
