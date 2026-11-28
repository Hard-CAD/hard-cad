"""Render a photorealistic CNC-metallic Blender Cycles visual for the Carriage / stop travel case.

Matches the controlled geometry in assets/carriage_travel.png (two parallel
steel guide rails on a machined base plate, gunmetal sliding carriage, fixed
left bronze end-stop, adjustable right bronze end-stop, and translucent swept
working-travel volume showing 16 -> 18 mm repair).

Usage:
  blender --factory-startup -b --python tools/render_carriage_travel.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "renders" / "carriage-travel-steel-light.jpg"
SCALE = 0.05


def main() -> None:
    import bpy
    from mathutils import Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    def ensure_nodes(db):
        if hasattr(db, "use_nodes") and not db.use_nodes:
            db.use_nodes = True

    def set_input(bsdf, names, val):
        for n in names:
            if n in bsdf.inputs:
                bsdf.inputs[n].default_value = val
                return

    def make_metal(name, color, rough_lo=0.17, rough_hi=0.27, metal=0.96, aniso=0.38, bevel_r=0.010):
        mat = bpy.data.materials.new(name)
        ensure_nodes(mat)
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = 12
        ao.inputs["Distance"].default_value = 0.45
        c_hi = nt.nodes.new("ShaderNodeRGB")
        c_hi.outputs["Color"].default_value = (*color, 1.0)
        c_lo = nt.nodes.new("ShaderNodeRGB")
        c_lo.outputs["Color"].default_value = (color[0] * 0.72, color[1] * 0.72, color[2] * 0.72, 1.0)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(ao.outputs["AO"], mix.inputs["Factor"])
        nt.links.new(c_lo.outputs["Color"], mix.inputs[6])
        nt.links.new(c_hi.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])

        set_input(bsdf, ("Metallic",), metal)
        set_input(bsdf, ("Anisotropic",), aniso)
        set_input(bsdf, ("Specular IOR Level", "Specular"), 0.55)

        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (4.0, 40.0, 4.0)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 14.0
        noise.inputs["Detail"].default_value = 6.0
        nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.25
        mr.inputs["From Max"].default_value = 0.75
        mr.inputs["To Min"].default_value = rough_lo
        mr.inputs["To Max"].default_value = rough_hi
        nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

        bevel = nt.nodes.new("ShaderNodeBevel")
        bevel.samples = 6
        bevel.inputs["Radius"].default_value = bevel_r
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.025
        bump.inputs["Distance"].default_value = 0.003
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bevel.outputs["Normal"], bump.inputs["Normal"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        return mat

    def make_translucent(name, color, alpha, emit):
        mat = bpy.data.materials.new(name)
        ensure_nodes(mat)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        set_input(bsdf, ("Metallic",), 0.1)
        set_input(bsdf, ("Roughness",), 0.22)
        set_input(bsdf, ("Alpha",), alpha)
        set_input(bsdf, ("Emission Color", "Emission"), (*color, 1.0))
        set_input(bsdf, ("Emission Strength",), emit)
        return mat

    def add_box(name, size_mm, loc_mm, mat):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v * SCALE for v in loc_mm))
        obj = bpy.context.object
        obj.name = name
        obj.scale = tuple(v * SCALE for v in size_mm)
        bpy.ops.object.transform_apply(scale=True)
        obj.data.materials.append(mat)
        return obj

    mat_steel = make_metal("Steel", (0.76, 0.79, 0.82), 0.17, 0.27, 0.96, 0.40, 0.009)
    mat_rail = make_metal("RailSteel", (0.64, 0.69, 0.73), 0.16, 0.25, 0.96, 0.45, 0.009)
    mat_carriage = make_metal("CarriageGunmetal", (0.34, 0.45, 0.52), 0.18, 0.28, 0.92, 0.35, 0.009)
    mat_bronze = make_metal("StopBronze", (0.76, 0.48, 0.34), 0.18, 0.27, 0.95, 0.35, 0.008)
    mat_travel = make_translucent("TravelEnvelope", (0.10, 0.54, 0.44), 0.18, 0.14)
    mat_conflict = make_translucent("StopConflict", (0.84, 0.18, 0.13), 0.52, 0.38)

    # Base bed: 74 x 34 x 6 mm (z: 0..6)
    add_box("BaseBed", (74, 34, 6), (0, 0, 3), mat_steel)
    # Two parallel linear guide rails along X (z: 6..18)
    add_box("RailFront", (74, 5, 12), (0, -11.5, 12), mat_rail)
    add_box("RailBack", (74, 5, 12), (0, 11.5, 12), mat_rail)
    # 4 corner rail fasteners
    for sx in (-31, 31):
        for sy in (-11.5, 11.5):
            bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=1.5 * SCALE, depth=1.2 * SCALE, location=(sx * SCALE, sy * SCALE, 18.6 * SCALE))
            bpy.context.object.data.materials.append(mat_steel)

    # Fixed left bronze end-stop (x = -26..-23)
    add_box("LeftStop", (3, 17.6, 11), (-24.5, 0, 11.5), mat_bronze)
    # Sliding gunmetal carriage (length 15 mm, x = -22.5..-7.5, sits flush between rails)
    add_box("Carriage", (15, 17.4, 11.5), (-15.0, 0, 11.75), mat_carriage)
    # Translucent required 18 mm travel sweep ahead of carriage (x = -7.5..+10.5)
    sweep = add_box("RequiredTravel", (18.0, 17.0, 10.6), (1.5, 0, 11.5), mat_travel)
    sweep.visible_shadow = False
    # Right movable stop placed inward by 2 mm (x = +8.5..+11.5 -> 16 mm travel, intersecting final 2 mm!)
    add_box("RightStop", (3, 17.6, 11), (10.0, 0, 11.5), mat_bronze)
    # Highlighted 2 mm conflict slice where required 18 mm stroke hits the inward stop
    hit = add_box("StrokeConflict", (2.1, 17.8, 11.2), (9.5, 0, 11.6), mat_conflict)
    hit.visible_shadow = False

    # Studio environment & tabletop
    world = bpy.data.worlds.new("Studio")
    scene.world = world
    ensure_nodes(world)
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    bg_env = nt.nodes.new("ShaderNodeBackground")
    bg_env.inputs["Color"].default_value = (0.18, 0.21, 0.25, 1.0)
    bg_env.inputs["Strength"].default_value = 0.40
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_cam.inputs["Color"].default_value = (0.93, 0.94, 0.95, 1.0)
    bg_cam.inputs["Strength"].default_value = 1.0
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(bg_env.outputs["Background"], mix.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    floor_mat = bpy.data.materials.new("Tabletop")
    ensure_nodes(floor_mat)
    fb = floor_mat.node_tree.nodes.get("Principled BSDF")
    fb.inputs["Base Color"].default_value = (0.85, 0.87, 0.88, 1.0)
    set_input(fb, ("Roughness",), 0.45)
    bpy.ops.mesh.primitive_plane_add(size=120.0, location=(0, 0, -0.005))
    bpy.context.object.data.materials.append(floor_mat)

    target = Vector((0.0, 0.0, 10.0 * SCALE))
    extent = 3.8
    scale_sq = (extent / 5.0) ** 2
    for off, sx, sy, energy, col in (
        ((0.30, 0.25, 1.85), 1.65, 0.50, 740, (1.0, 0.99, 0.97)),
        ((-1.40, -1.10, 1.25), 1.15, 0.85, 820, (1.0, 0.96, 0.92)),
        ((1.35, 1.00, 1.10), 0.90, 1.20, 760, (0.86, 0.93, 1.0)),
        ((1.10, -1.20, 0.55), 1.10, 0.65, 360, (0.94, 0.97, 1.0)),
    ):
        bpy.ops.object.light_add(type="AREA", location=target + Vector(off) * extent)
        lt = bpy.context.object
        lt.data.shape = "RECTANGLE"
        lt.data.size = sx * extent
        lt.data.size_y = sy * extent
        lt.data.energy = energy * scale_sq
        lt.data.color = col
        lt.rotation_euler = (target - lt.location).to_track_quat("-Z", "Y").to_euler()

    cam_dir = Vector((-1.15, -2.05, 1.65)).normalized()
    bpy.ops.object.camera_add(location=target + cam_dir * 10.8)
    cam = bpy.context.object
    cam.rotation_euler = (-cam_dir).to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "PERSP"
    cam.data.lens = 74.0
    scene.camera = cam

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    prefs = bpy.context.preferences.addons.get("cycles")
    scene.cycles.device = "CPU"
    if prefs is not None:
        cp = prefs.preferences
        for backend in ("OPTIX", "CUDA", "METAL", "HIP"):
            try:
                cp.compute_device_type = backend
                cp.get_devices()
                if any(d.type != "CPU" for d in cp.devices):
                    for d in cp.devices:
                        if d.type != "CPU":
                            d.use = True
                    scene.cycles.device = "GPU"
                    break
            except Exception:
                continue

    scene.render.resolution_x = 960
    scene.render.resolution_y = 560
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Punchy"
    except Exception:
        scene.view_settings.view_transform = "Filmic"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(OUT)
    bpy.ops.render.render(write_still=True)
    print(f"[rendered] {OUT}")


if __name__ == "__main__":
    main()
