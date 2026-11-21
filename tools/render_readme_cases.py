"""Render the public case-study display meshes for the README.

Run from the repository root with Blender:
  blender -b --python tools/render_readme_cases.py

The colored rings mark contract regions. Measurements remain in the case
reports, which were produced with the CAD kernel.
"""

import json
from math import cos, sin, tau
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "readme"
SCALE = 0.1
RESOLUTION = (1200, 820)
CASES = (
    ("cad15", "part-0-cut-1", (-2.5, -1.6, 1.8)),
    ("cad30", "part-0-cut-0", (-1.8, -2.4, 1.65)),
)


def read_mesh(path):
    """Index the ASCII STL triangles shared with the web inspector."""
    vertices, faces, indices, triangle = [], [], {}, []
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if not fields or fields[0] != "vertex":
            continue
        vertex = tuple(float(value) * SCALE for value in fields[1:])
        if vertex not in indices:
            indices[vertex] = len(vertices)
            vertices.append(vertex)
        triangle.append(indices[vertex])
        if len(triangle) == 3:
            faces.append(tuple(triangle))
            triangle.clear()
    if triangle or not faces:
        raise ValueError(f"Incomplete STL triangle data in {path.name}")
    return vertices, faces


def material(name, color, metal=0, roughness=0.38):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = roughness
    return mat


def marker(region, case, material_slot):
    center = Vector(region["origin"]) * SCALE
    axis = Vector(region["axis"]).normalized()
    # Make the outline visible just in front of the cut face or above the
    # upper opening. The marked radius comes from the published contract.
    offset = -0.18 if case == "cad15" else region["height"] + 0.18
    center += axis * (offset * SCALE)
    u = axis.cross(Vector((0, 1, 0))).normalized()
    v = axis.cross(u)
    radius = region["radius"] * SCALE
    curve = bpy.data.curves.new("Declared region outline", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.021
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    steps = 96
    spline.points.add(steps - 1)
    for i, point in enumerate(spline.points):
        angle = tau * i / steps
        point.co = (*(center + radius * (cos(angle) * u + sin(angle) * v)), 1)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new("Declared region outline", curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_slot)


def camera_frame(all_vertices, view):
    direction = Vector(view).normalized()
    rotation = (-direction).to_track_quat("-Z", "Y")
    axes = [rotation @ Vector(axis) for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    limits = []
    for axis in axes:
        projected = [vertex.dot(axis) for vertex in all_vertices]
        limits.append((min(projected), max(projected)))
    center = sum((axis * ((lo + hi) / 2) for axis, (lo, hi) in zip(axes, limits)), Vector())
    width, height, depth = (hi - lo for lo, hi in limits)
    scale = max(width * 1.16, height * RESOLUTION[0] / RESOLUTION[1] * 1.20)
    return center, direction, rotation, scale, max(width, height, depth)


def render(case, state, mesh, region, status, frame):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    center, direction, rotation, scale, extent = frame
    vertices, faces = mesh
    data = bpy.data.meshes.new("Published display mesh")
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new("Candidate", data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material("Satin teal metal", (0.24, 0.49, 0.46), 0.58))

    color = (0.62, 0.12, 0.077) if status == "FAIL" else (0.035, 0.38, 0.27)
    marker(region, case, material("Declared region status", color, 0.05, 0.28))

    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, -0.025))
    bpy.context.object.data.materials.append(material("Neutral gray studio floor", (0.55, 0.57, 0.58)))
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new("Neutral studio fill")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.67, 0.69, 0.72, 1)
    background.inputs["Strength"].default_value = 0.36
    for delta, energy in (((-1, -1, 1.6), 980), ((1.1, -0.45, 1.3), 620),
                          ((0.15, 1.2, 1.6), 1050)):
        bpy.ops.object.light_add(type="AREA", location=center + Vector(delta) * extent)
        light = bpy.context.object
        light.data.shape = "DISK"
        light.data.size = extent
        light.data.energy = energy * (extent / 5) ** 2
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(location=center + direction * (4 * extent))
    camera = bpy.context.object
    camera.rotation_euler = rotation.to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    scene.camera = camera
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 94
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = str(OUTPUT / f"{case}-{state}.jpg")
    bpy.ops.render.render(write_still=True)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for case, requirement, view in CASES:
        contract = json.loads((ROOT / "contracts" / f"{case}.json").read_text(encoding="utf8"))
        region = next(row["region"] for row in contract["requirements"] if row["id"] == requirement)
        bundle = next((ROOT / "examples").glob(f"{case}_*"))
        report = json.loads((bundle / "difference.json").read_text(encoding="utf8"))
        pair = next(row for row in report["requirements"] if row["id"] == requirement)
        states = ("initial", "feedback")
        meshes = [read_mesh(ASSETS / f"{case}_{state}.stl") for state in states]
        frame = camera_frame([Vector(v) for vertices, _ in meshes for v in vertices], view)
        for state, mesh, status in zip(states, meshes, (pair["before_status"], pair["after_status"])):
            render(case, state, mesh, region, status, frame)


if __name__ == "__main__":
    main()
