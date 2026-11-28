"""Render photorealistic CNC-metallic Cycles visuals for the controlled studies.

Generates:
  1. assets/renders/assembly/cover_00.jpg .. cover_08.jpg
     9-frame sequence for the Cover-first insertion order (exact swept
     intersection = pi * (5^2 - 3^2) * 4 = 201.06 mm^3).
  2. assets/renders/assembly/shaft_00.jpg .. shaft_08.jpg
     9-frame sequence for the Shaft-first insertion order (0.00 mm^3).
  3. assets/renders/clearance-section-steel-light.jpg
     Half-section cutaway of the brushed-steel guide bushing (R_b = 5.15 mm)
     and satin-copper shaft (R_s = 5.00 mm) showing eccentric clearance.

Usage (from repository root):
  blender --factory-startup -b --python tools/render_controlled_studies.py
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ASSEMBLY = ROOT / "assets" / "renders" / "assembly"
OUT_CLEARANCE = ROOT / "assets" / "renders" / "clearance-section-steel-light.jpg"
OUT_FIG4A = ROOT / "assets" / "renders" / "fig4a-clearance-repaired-steel-light.jpg"
OUT_FIG4B = ROOT / "assets" / "renders" / "fig4b-assembly-repaired-steel-light.jpg"

SCALE = 0.05  # 1 mm -> 0.05 Blender units


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--frames", type=int, default=9)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=560)
    parser.add_argument("--only", choices=("all", "fig4"), default="all")
    return parser.parse_args(argv)


def run_blender(args: argparse.Namespace) -> None:
    import bpy
    from mathutils import Vector

    def ensure_nodes(db) -> None:
        if hasattr(db, "use_nodes") and not db.use_nodes:
            db.use_nodes = True

    def set_input(bsdf, names: tuple[str, ...], val) -> None:
        for n in names:
            if n in bsdf.inputs:
                bsdf.inputs[n].default_value = val
                return

    def make_metal(name: str, color: tuple[float, float, float], rough_lo=0.18, rough_hi=0.28, metal=0.95, aniso=0.35, bevel_r=0.012):
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
        set_input(bsdf, ("Coat Weight", "Clearcoat"), 0.06)

        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (4.0, 42.0, 4.0)
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

    def make_translucent(name: str, color: tuple[float, float, float], alpha: float, emit: float):
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

    def setup_cycles(scene, width: int, height: int, samples: int):
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.02
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 8
        scene.cycles.glossy_bounces = 6
        scene.cycles.transmission_bounces = 6

        scene.cycles.device = "CPU"
        prefs = bpy.context.preferences.addons.get("cycles")
        if prefs is not None:
            cp = prefs.preferences
            for backend in ("OPTIX", "CUDA", "METAL", "HIP"):
                try:
                    cp.compute_device_type = backend
                    cp.get_devices()
                    found = False
                    for dev in cp.devices:
                        if dev.type != "CPU":
                            dev.use = True
                            found = True
                    if found:
                        scene.cycles.device = "GPU"
                        break
                except Exception:
                    continue

        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "JPEG"
        scene.render.image_settings.quality = 90
        try:
            scene.view_settings.view_transform = "AgX"
            scene.view_settings.look = "AgX - Punchy"
        except Exception:
            scene.view_settings.view_transform = "Filmic"
        scene.view_settings.exposure = 0.08

    def setup_light_studio(scene, target: Vector, extent: float):
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

        # Matte light-gray studio tabletop
        floor_mat = bpy.data.materials.new("Tabletop")
        ensure_nodes(floor_mat)
        fb = floor_mat.node_tree.nodes.get("Principled BSDF")
        fb.inputs["Base Color"].default_value = (0.85, 0.87, 0.88, 1.0)
        set_input(fb, ("Roughness",), 0.45)
        set_input(fb, ("Specular IOR Level", "Specular"), 0.28)
        bpy.ops.mesh.primitive_plane_add(size=extent * 32.0, location=(0, 0, -0.005))
        bpy.context.object.data.materials.append(floor_mat)

        # Studio softboxes
        scale_sq = (extent / 5.0) ** 2
        lights = [
            ((0.30, 0.25, 1.85), 1.65, 0.50, 740, (1.0, 0.99, 0.97)),
            ((-1.40, -1.10, 1.25), 1.15, 0.85, 820, (1.0, 0.96, 0.92)),
            ((1.35, 1.00, 1.10), 0.90, 1.20, 760, (0.86, 0.93, 1.0)),
            ((1.10, -1.20, 0.55), 1.10, 0.65, 360, (0.94, 0.97, 1.0)),
        ]
        for off, sx, sy, energy, col in lights:
            bpy.ops.object.light_add(type="AREA", location=target + Vector(off) * extent)
            lt = bpy.context.object
            lt.data.shape = "RECTANGLE"
            lt.data.size = sx * extent
            lt.data.size_y = sy * extent
            lt.data.energy = energy * scale_sq
            lt.data.color = col
            lt.rotation_euler = (target - lt.location).to_track_quat("-Z", "Y").to_euler()

        # Negative-fill flags for crisp metallic contrast
        black_mat = bpy.data.materials.new("NegFlag")
        ensure_nodes(black_mat)
        bb = black_mat.node_tree.nodes.get("Principled BSDF")
        bb.inputs["Base Color"].default_value = (0.015, 0.018, 0.022, 1.0)
        set_input(bb, ("Roughness",), 0.95)
        for off in ((-1.55, 0.80, 0.40), (1.50, -0.35, 0.40)):
            bpy.ops.mesh.primitive_plane_add(size=extent * 1.2, location=target + Vector(off) * extent)
            fl = bpy.context.object
            fl.rotation_euler = (target - fl.location).to_track_quat("-Z", "Y").to_euler()
            fl.data.materials.append(black_mat)
            fl.visible_camera = False
            fl.visible_shadow = False

    def assign_single_material(obj, mat):
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            poly.material_index = 0

    def make_holed_cylinder(name: str, r_outer: float, r_inner: float, height: float, loc: tuple[float, float, float], mat, segments=72):
        bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=r_outer, depth=height, location=loc)
        outer = bpy.context.object
        outer.name = name
        bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=r_inner, depth=height * 1.4, location=loc)
        hole = bpy.context.object
        mod = outer.modifiers.new("Bore", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = hole
        bpy.context.view_layer.objects.active = outer
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(hole, do_unlink=True)
        assign_single_material(outer, mat)
        return outer

    def make_half_bushing(name: str, r_outer: float, r_inner: float, height: float, z_bot: float, mat_body, mat_cut, segments=64):
        """Clean analytical 180-degree half-bushing (y >= 0) with zero boolean artifacts."""
        import bmesh
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        z0, z1 = z_bot, z_bot + height
        ring_out_bot, ring_out_top = [], []
        ring_in_bot, ring_in_top = [], []
        for i in range(segments + 1):
            ang = math.pi * i / segments  # 0 .. pi (y >= 0)
            ca, sa = math.cos(ang), math.sin(ang)
            ring_out_bot.append(bm.verts.new((r_outer * ca, r_outer * sa, z0)))
            ring_out_top.append(bm.verts.new((r_outer * ca, r_outer * sa, z1)))
            ring_in_bot.append(bm.verts.new((r_inner * ca, r_inner * sa, z0)))
            ring_in_top.append(bm.verts.new((r_inner * ca, r_inner * sa, z1)))

        body_faces = []
        for i in range(segments):
            # Outer cylindrical wall
            body_faces.append(bm.faces.new((ring_out_bot[i], ring_out_bot[i + 1], ring_out_top[i + 1], ring_out_top[i])))
            # Inner bore wall
            body_faces.append(bm.faces.new((ring_in_bot[i + 1], ring_in_bot[i], ring_in_top[i], ring_in_top[i + 1])))
            # Top annular face
            body_faces.append(bm.faces.new((ring_out_top[i], ring_out_top[i + 1], ring_in_top[i + 1], ring_in_top[i])))
            # Bottom annular face
            body_faces.append(bm.faces.new((ring_in_bot[i], ring_in_bot[i + 1], ring_out_bot[i + 1], ring_out_bot[i])))

        # Two crisp flat cut faces at y = 0 (i = 0 on +X, i = segments on -X)
        cut_face_pos = bm.faces.new((ring_in_bot[0], ring_out_bot[0], ring_out_top[0], ring_in_top[0]))
        cut_face_neg = bm.faces.new((ring_out_bot[segments], ring_in_bot[segments], ring_in_top[segments], ring_out_top[segments]))
        for f in body_faces:
            f.material_index = 0
        cut_face_pos.material_index = 1
        cut_face_neg.material_index = 1
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat_body)
        obj.data.materials.append(mat_cut)
        return obj

    def build_base_and_bushing(mat_steel, mat_gunmetal, mat_dark_steel, include_posts=True, include_bushing=True):
        # Base plate: 76 x 56 x 14 mm (z: 0..14)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 7.0 * SCALE))
        base = bpy.context.object
        base.scale = (76.0 * SCALE, 56.0 * SCALE, 14.0 * SCALE)
        bpy.ops.object.transform_apply(scale=True)
        # Central clearance hole in base plate for shaft seating down to z = 8 mm
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=5.15 * SCALE, depth=16.0 * SCALE, location=(0, 0, 14.0 * SCALE))
        bore = bpy.context.object
        mod = base.modifiers.new("BaseBore", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = bore
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(bore, do_unlink=True)
        assign_single_material(base, mat_steel)

        # 4 corner M6 socket cap bolts + washers
        for sx in (-29.0, 29.0):
            for sy in (-19.0, 19.0):
                bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=4.2 * SCALE, depth=1.6 * SCALE, location=(sx * SCALE, sy * SCALE, 14.8 * SCALE))
                bpy.context.object.data.materials.append(mat_dark_steel)
                bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=3.0 * SCALE, depth=2.8 * SCALE, location=(sx * SCALE, sy * SCALE, 16.4 * SCALE))
                head = bpy.context.object
                head.data.materials.append(mat_steel)

        bushing = None
        if include_bushing:
            # Central machined guide bushing: R_outer = 10.5 mm, R_inner = 5.15 mm, h = 20 mm (z: 14..34)
            bushing = make_holed_cylinder(
                "GuideBushing",
                r_outer=10.5 * SCALE,
                r_inner=5.15 * SCALE,
                height=20.0 * SCALE,
                loc=(0, 0, 24.0 * SCALE),
                mat=mat_gunmetal,
            )

        # Two cylindrical standoffs supporting the cover bridge (z: 14..46)
        if include_posts:
            for px in (-21.0, 21.0):
                bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=3.2 * SCALE, depth=32.0 * SCALE, location=(px * SCALE, 0, 30.0 * SCALE))
                post = bpy.context.object
                post.data.materials.append(mat_steel)

        return base, bushing

    def build_cover_plate(z_bottom_mm: float, mat_steel):
        # Cover bridge plate: 58 x 24 x 4.0 mm with Ø6 mm (r = 3.00 mm) central hole
        z_center = (z_bottom_mm + 2.0) * SCALE
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, z_center))
        cover = bpy.context.object
        cover.name = "CoverPlate"
        cover.scale = (58.0 * SCALE, 24.0 * SCALE, 4.0 * SCALE)
        bpy.ops.object.transform_apply(scale=True)

        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=3.0 * SCALE, depth=8.0 * SCALE, location=(0, 0, z_center))
        hole = bpy.context.object
        mod = cover.modifiers.new("PilotHole", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = hole
        bpy.context.view_layer.objects.active = cover
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(hole, do_unlink=True)
        assign_single_material(cover, mat_steel)
        return cover

    def render_assembly_sequence():
        OUT_ASSEMBLY.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene

        mat_steel = make_metal("BrushedSteel", (0.76, 0.79, 0.82), 0.17, 0.27, 0.96, 0.40, 0.011)
        mat_gunmetal = make_metal("GunmetalGuide", (0.42, 0.50, 0.55), 0.22, 0.31, 0.90, 0.35, 0.011)
        mat_dark_steel = make_metal("DarkBolt", (0.28, 0.31, 0.35), 0.25, 0.36, 0.92, 0.25, 0.008)
        mat_copper = make_metal("MachinedCopper", (0.80, 0.48, 0.36), 0.16, 0.24, 0.96, 0.45, 0.011)
        mat_sweep = make_translucent("SweepTrail", (0.84, 0.22, 0.16), alpha=0.16, emit=0.12)
        mat_conflict = make_translucent("ConflictAnnulus", (0.86, 0.15, 0.10), alpha=0.62, emit=0.55)

        build_base_and_bushing(mat_steel, mat_gunmetal, mat_dark_steel, include_posts=True)

        # Cover plate at z = 46..50 mm (movable for shaft-first order)
        cover = build_cover_plate(46.0, mat_steel)

        # Shaft: R_s = 5.00 mm, length = 36 mm (final bottom z = 8 mm -> top z = 44 mm, clears cover at 46 mm!)
        shaft_len = 36.0
        bpy.ops.mesh.primitive_cylinder_add(vertices=72, radius=5.0 * SCALE, depth=shaft_len * SCALE, location=(0, 0, (70.0 + shaft_len * 0.5) * SCALE))
        shaft = bpy.context.object
        shaft.name = "Shaft"
        shaft.data.materials.append(mat_copper)

        # Translucent crimson conflict annulus: exact swept intersection inside cover plate
        # R_outer = 5.00 mm, R_inner = 3.00 mm, h = 4.2 mm (slightly proud for crisp visibility)
        conflict = make_holed_cylinder(
            "ConflictAnnulus",
            r_outer=5.08 * SCALE,
            r_inner=2.96 * SCALE,
            height=4.35 * SCALE,
            loc=(0, 0, 48.0 * SCALE),
            mat=mat_conflict,
        )
        conflict.visible_shadow = False

        # Subtle swept-path envelope from top to current shaft position during Cover-first
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=5.02 * SCALE, depth=1.0, location=(0, 0, 60.0 * SCALE))
        sweep = bpy.context.object
        sweep.name = "SweepEnvelope"
        sweep.data.materials.append(mat_sweep)
        sweep.visible_shadow = False

        target = Vector((0.0, 0.0, 38.0 * SCALE))
        extent = 4.6
        setup_light_studio(scene, target, extent)

        cam_dir = Vector((-1.65, -2.25, 1.32)).normalized()
        bpy.ops.object.camera_add(location=target + cam_dir * 16.5)
        cam = bpy.context.object
        cam.rotation_euler = (-cam_dir).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "PERSP"
        cam.data.lens = 68.0
        scene.camera = cam

        setup_cycles(scene, args.width, args.height, args.samples)

        n = args.frames
        # 1. Cover-first: cover fixed at z=46 mm, shaft descends from bottom z=70 mm -> 8 mm
        cover.location.z = 0.0  # relative to initial build at z=46..50
        for idx in range(n):
            t = idx / (n - 1)
            shaft_bottom = 70.0 - 62.0 * t
            shaft.location.z = (shaft_bottom + shaft_len * 0.5) * SCALE

            # Show swept envelope & conflict annulus once shaft reaches/crosses the cover (z <= 50)
            crossing = shaft_bottom <= 51.0
            conflict.hide_render = not crossing
            if crossing:
                top_z = 70.0 + shaft_len
                bot_z = max(shaft_bottom, 8.0)
                h_mm = max(top_z - bot_z, 1.0)
                sweep.hide_render = False
                sweep.scale.z = h_mm * SCALE
                sweep.location.z = (bot_z + h_mm * 0.5) * SCALE
            else:
                sweep.hide_render = True

            out_path = OUT_ASSEMBLY / f"cover_{idx:02d}.jpg"
            scene.render.filepath = str(out_path)
            bpy.ops.render.render(write_still=True)
            print(f"[rendered] {out_path.name}")

        # 2. Shaft-first: first half inserts shaft (70 -> 8 mm) with cover lifted away;
        # second half lowers cover cleanly onto standoffs (z=78 -> 46 mm) with 0 mm^3 conflict.
        conflict.hide_render = True
        sweep.hide_render = True
        for idx in range(n):
            t = idx / (n - 1)
            if t <= 0.55:
                s = t / 0.55
                shaft_bottom = 70.0 - 62.0 * s
                cover_offset_mm = 38.0  # lifted high out of frame / above path
                cover.hide_render = s < 0.85
            else:
                s = (t - 0.55) / 0.45
                shaft_bottom = 8.0
                cover_offset_mm = 32.0 * (1.0 - s)
                cover.hide_render = False

            shaft.location.z = (shaft_bottom + shaft_len * 0.5) * SCALE
            cover.location.z = cover_offset_mm * SCALE
            out_path = OUT_ASSEMBLY / f"shaft_{idx:02d}.jpg"
            scene.render.filepath = str(out_path)
            bpy.ops.render.render(write_still=True)
            print(f"[rendered] {out_path.name}")

    def render_clearance_cutaway():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene

        mat_steel = make_metal("BrushedSteel", (0.76, 0.79, 0.82), 0.17, 0.27, 0.96, 0.40, 0.010)
        mat_gunmetal = make_metal("GunmetalGuide", (0.43, 0.52, 0.57), 0.20, 0.29, 0.92, 0.36, 0.010)
        mat_cut = make_metal("CutFace", (0.52, 0.58, 0.62), 0.26, 0.34, 0.90, 0.20, 0.006)
        mat_dark_steel = make_metal("DarkBolt", (0.28, 0.31, 0.35), 0.25, 0.36, 0.92, 0.25, 0.008)
        mat_copper = make_metal("MachinedCopper", (0.82, 0.49, 0.36), 0.15, 0.23, 0.96, 0.45, 0.010)

        build_base_and_bushing(mat_steel, mat_gunmetal, mat_dark_steel, include_posts=False, include_bushing=False)
        make_half_bushing(
            "HalfGuideBushing",
            r_outer=10.5 * SCALE,
            r_inner=5.15 * SCALE,
            height=20.0 * SCALE,
            z_bot=14.0 * SCALE,
            mat_body=mat_gunmetal,
            mat_cut=mat_cut,
        )

        # Shaft R_s = 5.00 mm shifted along +X (e = 0.12 mm)
        bpy.ops.mesh.primitive_cylinder_add(vertices=72, radius=5.0 * SCALE, depth=34.0 * SCALE, location=(0.12 * SCALE, 0, 26.0 * SCALE))
        shaft = bpy.context.object
        shaft.data.materials.append(mat_copper)

        # Thin crimson clearance highlight along the tight +X clearance gap
        mat_gap = make_translucent("TightGap", (0.86, 0.16, 0.11), alpha=0.88, emit=0.55)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.14 * SCALE, 0.02 * SCALE, 24.0 * SCALE))
        gap_bar = bpy.context.object
        gap_bar.scale = (0.14 * SCALE, 0.22 * SCALE, 20.1 * SCALE)
        gap_bar.data.materials.append(mat_gap)
        gap_bar.visible_shadow = False

        target = Vector((0.0, 0.0, 23.0 * SCALE))
        extent = 3.8
        setup_light_studio(scene, target, extent)

        cam_dir = Vector((-0.85, -2.45, 1.18)).normalized()
        bpy.ops.object.camera_add(location=target + cam_dir * 9.8)
        cam = bpy.context.object
        cam.rotation_euler = (-cam_dir).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "PERSP"
        cam.data.lens = 82.0
        scene.camera = cam

        setup_cycles(scene, 960, 560, max(args.samples, 96))
        OUT_CLEARANCE.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(OUT_CLEARANCE)
        bpy.ops.render.render(write_still=True)
        print(f"[rendered] {OUT_CLEARANCE}")

    def render_fig4_repaired():
        # Figure 4(a): Elevated right-3/4 cutaway of REPAIRED guide/shaft clearance (e = 0.03 mm -> 0.12 mm PASS)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        mat_steel = make_metal("BrushedSteel", (0.76, 0.79, 0.82), 0.17, 0.27, 0.96, 0.40, 0.010)
        mat_gunmetal = make_metal("GunmetalGuide", (0.43, 0.52, 0.57), 0.20, 0.29, 0.92, 0.36, 0.010)
        mat_cut = make_metal("CutFace", (0.52, 0.58, 0.62), 0.26, 0.34, 0.90, 0.20, 0.006)
        mat_dark_steel = make_metal("DarkBolt", (0.28, 0.31, 0.35), 0.25, 0.36, 0.92, 0.25, 0.008)
        mat_copper = make_metal("MachinedCopper", (0.82, 0.49, 0.36), 0.15, 0.23, 0.96, 0.45, 0.010)
        mat_pass = make_translucent("ClearancePass", (0.12, 0.62, 0.50), alpha=0.68, emit=0.42)

        build_base_and_bushing(mat_steel, mat_gunmetal, mat_dark_steel, include_posts=False, include_bushing=False)
        make_half_bushing(
            "HalfGuideBushing",
            r_outer=10.5 * SCALE,
            r_inner=5.15 * SCALE,
            height=20.0 * SCALE,
            z_bot=14.0 * SCALE,
            mat_body=mat_gunmetal,
            mat_cut=mat_cut,
        )
        bpy.ops.mesh.primitive_cylinder_add(vertices=72, radius=5.0 * SCALE, depth=34.0 * SCALE, location=(0.03 * SCALE, 0, 26.0 * SCALE))
        shaft = bpy.context.object
        shaft.data.materials.append(mat_copper)

        # Glowing teal radial clearance collar at top lip of guide bore
        ring = make_holed_cylinder(
            "PassClearanceRing",
            r_outer=5.32 * SCALE,
            r_inner=4.98 * SCALE,
            height=1.1 * SCALE,
            loc=(0.0, 0.0, 34.15 * SCALE),
            mat=mat_pass,
        )
        ring.visible_shadow = False

        target = Vector((0.0, 0.0, 23.0 * SCALE))
        setup_light_studio(scene, target, 3.8)
        cam_dir = Vector((1.55, -2.05, 1.75)).normalized()
        bpy.ops.object.camera_add(location=target + cam_dir * 9.8)
        cam = bpy.context.object
        cam.rotation_euler = (-cam_dir).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "PERSP"
        cam.data.lens = 78.0
        scene.camera = cam
        setup_cycles(scene, 960, 560, max(args.samples, 80))
        OUT_FIG4A.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(OUT_FIG4A)
        bpy.ops.render.render(write_still=True)
        print(f"[rendered] {OUT_FIG4A}")

        # Figure 4(b): Opposite elevated 3/4 view of REPAIRED Shaft-first installation (0.00 mm^3 PASS)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        mat_steel = make_metal("BrushedSteel", (0.76, 0.79, 0.82), 0.17, 0.27, 0.96, 0.40, 0.011)
        mat_gunmetal = make_metal("GunmetalGuide", (0.42, 0.50, 0.55), 0.22, 0.31, 0.90, 0.35, 0.011)
        mat_dark_steel = make_metal("DarkBolt", (0.28, 0.31, 0.35), 0.25, 0.36, 0.92, 0.25, 0.008)
        mat_copper = make_metal("MachinedCopper", (0.80, 0.48, 0.36), 0.16, 0.24, 0.96, 0.45, 0.011)
        mat_pass = make_translucent("OrderPass", (0.12, 0.62, 0.50), alpha=0.58, emit=0.45)

        build_base_and_bushing(mat_steel, mat_gunmetal, mat_dark_steel, include_posts=True)
        cover = build_cover_plate(46.0, mat_steel)
        cover.location.z = 9.5 * SCALE  # gliding cleanly down onto standoffs after shaft is seated
        shaft_len = 36.0
        bpy.ops.mesh.primitive_cylinder_add(vertices=72, radius=5.0 * SCALE, depth=shaft_len * SCALE, location=(0, 0, (8.0 + shaft_len * 0.5) * SCALE))
        shaft = bpy.context.object
        shaft.data.materials.append(mat_copper)

        # Teal pilot-hole clearance ring inside the descending cover plate
        pilot_ring = make_holed_cylinder(
            "PilotClearRing",
            r_outer=3.35 * SCALE,
            r_inner=2.94 * SCALE,
            height=4.35 * SCALE,
            loc=(0, 0, (48.0 + 9.5) * SCALE),
            mat=mat_pass,
        )
        pilot_ring.visible_shadow = False

        target = Vector((0.0, 0.0, 35.0 * SCALE))
        setup_light_studio(scene, target, 4.6)
        cam_dir = Vector((1.85, -2.05, 1.55)).normalized()
        bpy.ops.object.camera_add(location=target + cam_dir * 16.0)
        cam = bpy.context.object
        cam.rotation_euler = (-cam_dir).to_track_quat("-Z", "Y").to_euler()
        cam.data.type = "PERSP"
        cam.data.lens = 68.0
        scene.camera = cam
        setup_cycles(scene, 960, 560, max(args.samples, 80))
        scene.render.filepath = str(OUT_FIG4B)
        bpy.ops.render.render(write_still=True)
        print(f"[rendered] {OUT_FIG4B}")

    if args.only == "fig4":
        render_fig4_repaired()
    else:
        render_assembly_sequence()
        render_clearance_cutaway()
        render_fig4_repaired()


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parse_args(argv)
    run_blender(args)


if __name__ == "__main__":
    main()
