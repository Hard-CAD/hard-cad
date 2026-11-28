"""Render photorealistic CNC-machined metallic studio views for Hard-CAD.

Reads the repository's ground-truth display STL meshes and declared contract
regions (`contracts/*.json`) and renders them in Blender Cycles with:
  - True metallic PBR shaders (brushed steel / aluminum / titanium)
  - Shader-level micro-bevel glints (ShaderNodeBevel) without modifying mesh geometry
  - Subtle Ambient Occlusion for bore and pocket depth
  - High-contrast studio light-tent reflections (overhead softbox + key + rim + negative fill)
  - Optional y=0 cutaway renders exposing internal bores and voids

Usage (from repository root):
  # Render high-res metallic renders to assets/renders/
  blender -b --python tools/render_metallic_studio.py -- --samples 128

  # Render dark-petrol studio backdrop matching the homepage Hero & replace Hero/README images
  blender -b --python tools/render_metallic_studio.py -- --backdrop dark --overwrite-readme --cutaway

  # Validate STL parsing & contract geometry without Blender:
  python tools/render_metallic_studio.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DEFAULT_OUTPUT = ASSETS / "renders"

RESOLUTION = (1600, 1080)

FINISH_PRESETS = {
    "steel": {
        "base_color": (0.72, 0.75, 0.78),
        "metallic": 0.96,
        "rough_min": 0.16,
        "rough_max": 0.27,
        "anisotropic": 0.42,
        "bump_strength": 0.03,
        "ao_darken": 0.78,
    },
    "aluminum": {
        "base_color": (0.81, 0.83, 0.85),
        "metallic": 0.95,
        "rough_min": 0.20,
        "rough_max": 0.31,
        "anisotropic": 0.30,
        "bump_strength": 0.025,
        "ao_darken": 0.82,
    },
    "titanium": {
        "base_color": (0.56, 0.59, 0.63),
        "metallic": 0.97,
        "rough_min": 0.18,
        "rough_max": 0.29,
        "anisotropic": 0.48,
        "bump_strength": 0.035,
        "ao_darken": 0.76,
    },
    "anodized-teal": {
        "base_color": (0.28, 0.46, 0.46),
        "metallic": 0.88,
        "rough_min": 0.22,
        "rough_max": 0.32,
        "anisotropic": 0.35,
        "bump_strength": 0.02,
        "ao_darken": 0.80,
    },
}

BACKDROP_PRESETS = {
    "light": {
        "floor_color": (0.76, 0.78, 0.80),
        "floor_roughness": 0.42,
        "world_color": (0.14, 0.17, 0.20),
        "world_strength": 0.35,
        "bg_camera_color": (0.86, 0.88, 0.90),
    },
    "dark": {
        "floor_color": (0.075, 0.115, 0.138),
        "floor_roughness": 0.34,
        "world_color": (0.06, 0.09, 0.11),
        "world_strength": 0.28,
        "bg_camera_color": (0.082, 0.135, 0.165),
    },
}

CASE_SPECS = {
    "cad15": {
        "requirement": "part-0-cut-1",
        "view": (-2.45, -1.65, 1.75),
        "scale": 0.1,
        "cutaway_y": 0.0,
        "states": {
            "initial": ("assets/cad15_initial.stl", "PASS"),
            "feedback": ("assets/cad15_feedback.stl", "FAIL"),
        },
        "readme_map": {
            "initial": "cad15-initial.jpg",
            "feedback": "cad15-feedback.jpg",
        },
    },
    "cad30": {
        "requirement": "part-0-cut-0",
        "view": (-1.80, -2.40, 1.65),
        "scale": 0.1,
        "cutaway_y": None,
        "states": {
            "initial": ("assets/cad30_initial.stl", "FAIL"),
            "feedback": ("assets/cad30_feedback.stl", "PASS"),
        },
        "readme_map": {
            "initial": "cad30-initial.jpg",
            "feedback": "cad30-feedback.jpg",
        },
    },
    "pump": {
        "requirement": "shaft-core-required",
        "view": (1.10, -2.15, 0.92),
        "scale": 0.01,
        "cutaway_y": 0.0,
        "states": {
            "initial": ("pump-shaft/initial.stl", "FAIL"),
            "revision": ("pump-shaft/revision.stl", "PASS"),
        },
        "readme_map": {},
    },
}


def read_stl_mesh(path: Path, scale: float) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Load either ASCII or binary STL into indexed (vertices, faces) lists."""
    raw = path.read_bytes()
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    index_map: dict[tuple[float, float, float], int] = {}

    def add_vertex(x: float, y: float, z: float) -> int:
        # Round to 1e-6 after scaling to weld coincident STL triangle vertices cleanly
        key = (round(x * scale, 6), round(y * scale, 6), round(z * scale, 6))
        idx = index_map.get(key)
        if idx is None:
            idx = len(vertices)
            index_map[key] = idx
            vertices.append(key)
        return idx

    is_ascii = raw[:5] == b"solid" and b"vertex" in raw[:1024]
    if is_ascii:
        tri: list[int] = []
        for line in raw.decode("ascii", errors="ignore").splitlines():
            parts = line.split()
            if len(parts) == 4 and parts[0] == "vertex":
                tri.append(add_vertex(float(parts[1]), float(parts[2]), float(parts[3])))
                if len(tri) == 3:
                    if len(set(tri)) == 3:
                        faces.append((tri[0], tri[1], tri[2]))
                    tri.clear()
    else:
        if len(raw) < 84:
            raise ValueError(f"Binary STL too short: {path}")
        tri_count = struct.unpack("<I", raw[80:84])[0]
        expected = 84 + tri_count * 50
        if len(raw) < expected:
            raise ValueError(f"Binary STL truncated ({len(raw)} < {expected}): {path}")
        for i in range(tri_count):
            offset = 84 + i * 50 + 12  # skip 3-float normal
            v0 = struct.unpack("<3f", raw[offset : offset + 12])
            v1 = struct.unpack("<3f", raw[offset + 12 : offset + 24])
            v2 = struct.unpack("<3f", raw[offset + 24 : offset + 36])
            i0, i1, i2 = add_vertex(*v0), add_vertex(*v1), add_vertex(*v2)
            if i0 != i1 and i1 != i2 and i2 != i0:
                faces.append((i0, i1, i2))

    if not faces:
        raise ValueError(f"No valid faces found in {path}")
    return vertices, faces


def load_contract_region(case: str, requirement_id: str) -> dict:
    contract_path = ROOT / "contracts" / f"{case}.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    for row in contract["requirements"]:
        if row["id"] == requirement_id:
            return row["region"]
    raise KeyError(f"Requirement {requirement_id!r} not found in {contract_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hard-CAD metallic Cycles renderer")
    parser.add_argument("--cases", nargs="+", choices=list(CASE_SPECS.keys()), default=list(CASE_SPECS.keys()))
    parser.add_argument("--finish", choices=list(FINISH_PRESETS.keys()), default="steel")
    parser.add_argument("--backdrop", choices=list(BACKDROP_PRESETS.keys()), default="light")
    parser.add_argument("--samples", type=int, default=96)
    parser.add_argument("--width", type=int, default=RESOLUTION[0])
    parser.add_argument("--height", type=int, default=RESOLUTION[1])
    parser.add_argument("--device", choices=["AUTO", "CPU", "CUDA", "OPTIX", "METAL"], default="AUTO")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cutaway", action="store_true", help="Also render y=0 cutaway views for cad15 & pump")
    parser.add_argument(
        "--overwrite-readme",
        action="store_true",
        help="Also copy cad15/cad30 standard renders into assets/readme/*.jpg for the homepage Hero",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate STLs and contracts without Blender")
    return parser.parse_args(argv)


def run_dry_check(args: argparse.Namespace) -> None:
    print(f"[dry-run] Validating cases={args.cases}, finish={args.finish}, backdrop={args.backdrop}")
    for case in args.cases:
        spec = CASE_SPECS[case]
        region = load_contract_region(case, spec["requirement"])
        print(f"  case={case} req={spec['requirement']} region={region}")
        for state, (rel_path, status) in spec["states"].items():
            stl_path = ROOT / rel_path
            verts, faces = read_stl_mesh(stl_path, spec["scale"])
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            zs = [v[2] for v in verts]
            print(
                f"    {state:8s} ({status}): {len(verts):4d} verts, {len(faces):4d} faces | "
                f"bounds=([{min(xs):.2f},{max(xs):.2f}], [{min(ys):.2f},{max(ys):.2f}], [{min(zs):.2f},{max(zs):.2f}])"
            )
    print("[dry-run] OK - all meshes and contracts loaded cleanly.")


def run_blender_render(args: argparse.Namespace) -> None:
    import bpy
    from mathutils import Matrix, Vector

    def set_bsdf_input(bsdf, names: tuple[str, ...], value) -> None:
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = value
                return

    def ensure_nodes(datablock) -> None:
        if hasattr(datablock, "use_nodes") and not datablock.use_nodes:
            datablock.use_nodes = True

    def make_cnc_metal_material(name: str, preset: dict, extent: float):
        mat = bpy.data.materials.new(name)
        ensure_nodes(mat)
        nt = mat.node_tree
        nt.nodes.clear()

        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

        # Base color modulated subtly by Ambient Occlusion for crisp bore/pocket depth
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = 16
        ao.inputs["Distance"].default_value = max(extent * 0.14, 0.25)

        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs["Color"].default_value = (*preset["base_color"], 1.0)

        dark_rgb = nt.nodes.new("ShaderNodeRGB")
        d = preset["ao_darken"]
        dark_rgb.outputs["Color"].default_value = (
            preset["base_color"][0] * d,
            preset["base_color"][1] * d,
            preset["base_color"][2] * d,
            1.0,
        )

        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(ao.outputs["AO"], mix.inputs["Factor"])
        nt.links.new(dark_rgb.outputs["Color"], mix.inputs[6])
        nt.links.new(rgb.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])

        set_bsdf_input(bsdf, ("Metallic",), preset["metallic"])
        set_bsdf_input(bsdf, ("Anisotropic",), preset["anisotropic"])
        set_bsdf_input(bsdf, ("Specular IOR Level", "Specular"), 0.55)
        set_bsdf_input(bsdf, ("Coat Weight", "Clearcoat"), 0.08)
        set_bsdf_input(bsdf, ("Coat Roughness", "Clearcoat Roughness"), 0.18)

        # Procedural brushed CNC grain (anisotropically stretched noise)
        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (4.0, 48.0, 4.0)
        nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = max(18.0 / max(extent, 0.5), 3.0)
        noise.inputs["Detail"].default_value = 8.0
        noise.inputs["Roughness"].default_value = 0.65
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

        rough_range = nt.nodes.new("ShaderNodeMapRange")
        rough_range.inputs["From Min"].default_value = 0.25
        rough_range.inputs["From Max"].default_value = 0.75
        rough_range.inputs["To Min"].default_value = preset["rough_min"]
        rough_range.inputs["To Max"].default_value = preset["rough_max"]
        nt.links.new(noise.outputs["Fac"], rough_range.inputs["Value"])
        nt.links.new(rough_range.outputs["Result"], bsdf.inputs["Roughness"])

        # Micro-bevel shader catches sharp CNC edge highlights without changing STL geometry
        bevel = nt.nodes.new("ShaderNodeBevel")
        bevel.samples = 8
        bevel.inputs["Radius"].default_value = max(extent * 0.0045, 0.012)

        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = preset["bump_strength"]
        bump.inputs["Distance"].default_value = max(extent * 0.001, 0.002)
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bevel.outputs["Normal"], bump.inputs["Normal"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

        return mat

    def make_cut_face_material(name: str):
        """Slightly darker satin-milled cross-section face for cutaway renders."""
        mat = bpy.data.materials.new(name)
        ensure_nodes(mat)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.48, 0.53, 0.58, 1.0)
        set_bsdf_input(bsdf, ("Metallic",), 0.90)
        set_bsdf_input(bsdf, ("Roughness",), 0.28)
        return mat

    def make_indicator_material(name: str, color: tuple[float, float, float], alpha: float, emit: float):
        mat = bpy.data.materials.new(name)
        ensure_nodes(mat)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        set_bsdf_input(bsdf, ("Metallic",), 0.15)
        set_bsdf_input(bsdf, ("Roughness",), 0.24)
        set_bsdf_input(bsdf, ("Alpha",), alpha)
        set_bsdf_input(bsdf, ("Emission Color", "Emission"), (*color, 1.0))
        set_bsdf_input(bsdf, ("Emission Strength",), emit)
        return mat

    def make_studio_floor_material(preset: dict):
        mat = bpy.data.materials.new("Studio Floor")
        ensure_nodes(mat)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*preset["floor_color"], 1.0)
        set_bsdf_input(bsdf, ("Metallic",), 0.04)
        set_bsdf_input(bsdf, ("Roughness",), preset["floor_roughness"])
        set_bsdf_input(bsdf, ("Specular IOR Level", "Specular"), 0.35)
        return mat

    def setup_world_light_tent(scene, preset: dict):
        world = bpy.data.worlds.new("Metallic Studio World")
        scene.world = world
        ensure_nodes(world)
        nt = world.node_tree
        nt.nodes.clear()

        out = nt.nodes.new("ShaderNodeOutputWorld")
        mix = nt.nodes.new("ShaderNodeMixShader")
        lp = nt.nodes.new("ShaderNodeLightPath")

        bg_env = nt.nodes.new("ShaderNodeBackground")
        bg_env.inputs["Color"].default_value = (*preset["world_color"], 1.0)
        bg_env.inputs["Strength"].default_value = preset["world_strength"]

        bg_cam = nt.nodes.new("ShaderNodeBackground")
        bg_cam.inputs["Color"].default_value = (*preset["bg_camera_color"], 1.0)
        bg_cam.inputs["Strength"].default_value = 1.0

        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
        nt.links.new(bg_env.outputs["Background"], mix.inputs[1])
        nt.links.new(bg_cam.outputs["Background"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    def add_studio_lights(center: Vector, extent: float):
        # Balanced studio softboxes: angled overhead strip preserves brushed metal grain
        # across horizontal top plates without blowing out highlights to flat white.
        lights = [
            # (offset_multiplier, size_x, size_y, energy_base, color)
            ((0.35, 0.30, 1.85), 1.65, 0.45, 760, (1.0, 0.99, 0.97)),
            # Warm-neutral front-left key softbox
            ((-1.40, -1.10, 1.15), 1.15, 0.85, 840, (1.0, 0.96, 0.91)),
            # Cool cyan-white rim kicker to crisp up machined edges and bore walls
            ((1.35, 1.00, 1.05), 0.90, 1.20, 780, (0.85, 0.93, 1.0)),
            # Gentle low fill card on front-right
            ((1.15, -1.15, 0.50), 1.20, 0.65, 340, (0.93, 0.96, 1.0)),
        ]
        scale_sq = (extent / 5.0) ** 2
        for offset, sx, sy, energy, color in lights:
            bpy.ops.object.light_add(type="AREA", location=center + Vector(offset) * extent)
            obj = bpy.context.object
            obj.data.shape = "RECTANGLE"
            obj.data.size = sx * extent
            obj.data.size_y = sy * extent
            obj.data.energy = energy * scale_sq
            obj.data.color = color
            obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()

        # Negative-fill black reflection flags (invisible to camera, visible to glossy rays)
        # create dark-to-light bands across metallic cylinders and bevels.
        black_mat = bpy.data.materials.new("Negative Fill Flag")
        ensure_nodes(black_mat)
        bsdf = black_mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.015, 0.018, 0.022, 1.0)
        set_bsdf_input(bsdf, ("Roughness",), 0.95)
        for offset in ((-1.5, 0.85, 0.35), (1.45, -0.35, 0.35), (-0.4, -0.5, 1.9)):
            bpy.ops.mesh.primitive_plane_add(size=extent * 1.1, location=center + Vector(offset) * extent)
            flag = bpy.context.object
            flag.rotation_euler = (center - flag.location).to_track_quat("-Z", "Y").to_euler()
            flag.data.materials.append(black_mat)
            flag.visible_camera = False
            flag.visible_shadow = False

    def add_contract_indicator(region: dict, case: str, scale: float, status: str, cutaway: bool, cutter=None):
        is_fail = status == "FAIL"
        accent = (0.78, 0.14, 0.09) if is_fail else (0.06, 0.52, 0.38)
        ring_mat = make_indicator_material("Contract Collar", accent, alpha=1.0, emit=0.35 if is_fail else 0.18)
        vol_mat = make_indicator_material("Contract Volume", accent, alpha=0.36 if is_fail else 0.16, emit=0.25 if is_fail else 0.08)

        if region["kind"] == "cylinder":
            origin = Vector(region["origin"]) * scale
            axis = Vector(region["axis"]).normalized()
            radius = region["radius"] * scale
            height = region["height"] * scale
            rot = Vector((0, 0, 1)).rotation_difference(axis)

            # Translucent volume plug (especially informative in cutaway or FAIL views)
            if is_fail or cutaway:
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=64,
                    radius=radius * 0.995,
                    depth=height,
                    location=origin + axis * (height * 0.5),
                )
                vol = bpy.context.object
                vol.rotation_euler = rot.to_euler()
                vol.data.materials.append(vol_mat)
                vol.visible_shadow = False
                if cutaway and cutter is not None:
                    b = vol.modifiers.new("CutIndicator", "BOOLEAN")
                    b.operation = "DIFFERENCE"
                    b.solver = "EXACT"
                    b.object = cutter

            # Precision collar just proud of the entry face (omit full ring in cutaway so section stays razor-clean)
            if not cutaway:
                offset_mm = -0.16 if case == "cad15" else region["height"] + 0.16
                ring_center = origin + axis * (offset_mm * scale)
                u = axis.cross(Vector((0, 1, 0)))
                if u.length < 1e-5:
                    u = axis.cross(Vector((1, 0, 0)))
                u.normalize()
                v = axis.cross(u).normalized()

                curve = bpy.data.curves.new("Contract Ring", "CURVE")
                curve.dimensions = "3D"
                curve.bevel_depth = max(radius * 0.065, 0.018)
                curve.bevel_resolution = 6
                spline = curve.splines.new("POLY")
                steps = 96
                spline.points.add(steps - 1)
                for i, pt in enumerate(spline.points):
                    ang = math.tau * i / steps
                    pt.co = (*(ring_center + radius * (math.cos(ang) * u + math.sin(ang) * v)), 1.0)
                spline.use_cyclic_u = True
                ring_obj = bpy.data.objects.new("Contract Ring", curve)
                bpy.context.collection.objects.link(ring_obj)
                ring_obj.data.materials.append(ring_mat)
        else:
            origin = Vector(region["origin"]) * scale
            size = Vector(region["size"]) * scale
            center = origin + size * 0.5
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
            box = bpy.context.object
            box.scale = size
            box.data.materials.append(vol_mat)
            box.visible_shadow = False

            # Crisp wireframe cage around keep-in box
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
            cage = bpy.context.object
            cage.scale = size * 1.02
            wf = cage.modifiers.new("Wireframe", "WIREFRAME")
            wf.thickness = max(size.length * 0.045, 0.008)
            cage.data.materials.append(ring_mat)
            cage.visible_shadow = False

    def compute_camera_frame(all_verts: list[Vector], view: tuple[float, float, float], res: tuple[int, int]):
        direction = Vector(view).normalized()
        rotation = (-direction).to_track_quat("-Z", "Y")
        axes = [rotation @ Vector(a) for a in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        limits = []
        for axis in axes:
            proj = [v.dot(axis) for v in all_verts]
            limits.append((min(proj), max(proj)))
        center = sum((axis * ((lo + hi) * 0.5) for axis, (lo, hi) in zip(axes, limits)), Vector())
        width, height, depth = (hi - lo for lo, hi in limits)
        extent = max(width, height, depth, 1e-3)
        ortho_scale = max(width * 1.20, height * (res[0] / res[1]) * 1.24)
        min_z = min(v.z for v in all_verts)
        return center, direction, rotation, ortho_scale, extent, min_z

    def configure_cycles(scene, device_choice: str, samples: int, width: int, height: int):
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.015
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 8
        scene.cycles.glossy_bounces = 6
        scene.cycles.transmission_bounces = 6

        scene.cycles.device = "CPU"
        if device_choice != "CPU":
            prefs = bpy.context.preferences.addons.get("cycles")
            if prefs is not None:
                c_prefs = prefs.preferences
                candidates = ["OPTIX", "CUDA", "METAL", "HIP"] if device_choice == "AUTO" else [device_choice]
                for backend in candidates:
                    try:
                        c_prefs.compute_device_type = backend
                        c_prefs.get_devices()
                        gpu_found = False
                        for dev in c_prefs.devices:
                            if dev.type != "CPU":
                                dev.use = True
                                gpu_found = True
                        if gpu_found:
                            scene.cycles.device = "GPU"
                            break
                    except Exception:
                        continue

        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "JPEG"
        scene.render.image_settings.quality = 95
        try:
            scene.view_settings.view_transform = "AgX"
            scene.view_settings.look = "AgX - Punchy"
        except Exception:
            scene.view_settings.view_transform = "Filmic"
            try:
                scene.view_settings.look = "Medium High Contrast"
            except Exception:
                pass
        scene.view_settings.exposure = 0.05

    def render_single(
        case: str,
        state: str,
        mesh_data: tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]],
        region: dict,
        status: str,
        scale: float,
        frame,
        output_path: Path,
        cutaway_y: float | None = None,
    ):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        center, direction, rotation, ortho_scale, extent, min_z = frame
        verts, faces = mesh_data

        mesh = bpy.data.meshes.new(f"{case}_{state}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        # Keep planar faces crisp while smoothing cylindrical bore walls
        for poly in mesh.polygons:
            poly.use_smooth = False

        obj = bpy.data.objects.new(f"{case}_{state}", mesh)
        bpy.context.collection.objects.link(obj)
        metal_mat = make_cnc_metal_material("CNC Metal", FINISH_PRESETS[args.finish], extent)
        obj.data.materials.append(metal_mat)

        cutter = None
        if cutaway_y is not None:
            cut_mat = make_cut_face_material("Machined Cut Face")
            obj.data.materials.append(cut_mat)
            # Cut away the front half (y < cutaway_y) cleanly using an exact boolean box
            cut_size = extent * 4.0
            bpy.ops.mesh.primitive_cube_add(
                size=cut_size,
                location=(center.x, cutaway_y * scale - cut_size * 0.5, center.z),
            )
            cutter = bpy.context.object
            cutter.data.materials.append(cut_mat)
            cutter.display_type = "WIRE"
            cutter.hide_render = True
            cutter.hide_viewport = True

            boolean = obj.modifiers.new("SectionCut", "BOOLEAN")
            boolean.operation = "DIFFERENCE"
            boolean.solver = "EXACT"
            boolean.object = cutter

        add_contract_indicator(region, case, scale, status, cutaway=cutaway_y is not None, cutter=cutter)

        backdrop = BACKDROP_PRESETS[args.backdrop]
        bpy.ops.mesh.primitive_plane_add(
            size=extent * 36.0,
            location=(center.x, center.y, min_z - extent * 0.004),
        )
        floor = bpy.context.object
        floor.data.materials.append(make_studio_floor_material(backdrop))

        scene = bpy.context.scene
        setup_world_light_tent(scene, backdrop)
        add_studio_lights(center, extent)

        # Mild perspective (85mm telephoto lens) gives realistic industrial CAD presence
        # without wide-angle distortion.
        cam_dist = extent * 3.1
        bpy.ops.object.camera_add(location=center + direction * cam_dist)
        cam = bpy.context.object
        cam.rotation_euler = rotation.to_euler()
        cam.data.type = "PERSP"
        cam.data.lens = 85.0
        cam.data.sensor_width = 36.0
        cam.data.clip_start = max(extent * 0.01, 0.005)
        cam.data.clip_end = extent * 100.0
        # Auto-adjust distance from orthographic extent so framing stays exact
        half_fov_x = math.atan(cam.data.sensor_width / (2.0 * cam.data.lens))
        cam.location = center + direction * (ortho_scale * 0.52 / math.tan(half_fov_x))
        scene.camera = cam

        configure_cycles(scene, args.device, args.samples, args.width, args.height)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        print(f"[rendered] {output_path}")

    args.output.mkdir(parents=True, exist_ok=True)
    for case in args.cases:
        spec = CASE_SPECS[case]
        region = load_contract_region(case, spec["requirement"])
        loaded = {}
        all_verts: list[Vector] = []
        for state, (rel_path, status) in spec["states"].items():
            mesh_data = read_stl_mesh(ROOT / rel_path, spec["scale"])
            loaded[state] = (mesh_data, status)
            all_verts.extend(Vector(v) for v in mesh_data[0])

        frame = compute_camera_frame(all_verts, spec["view"], (args.width, args.height))
        for state, (mesh_data, status) in loaded.items():
            out_file = args.output / f"{case}-{state}-{args.finish}-{args.backdrop}.jpg"
            render_single(case, state, mesh_data, region, status, spec["scale"], frame, out_file)

            if args.overwrite_readme and state in spec["readme_map"]:
                readme_target = ASSETS / "readme" / spec["readme_map"][state]
                readme_target.parent.mkdir(parents=True, exist_ok=True)
                readme_target.write_bytes(out_file.read_bytes())
                print(f"[updated]  {readme_target}")

            if args.cutaway and spec["cutaway_y"] is not None:
                cut_file = args.output / f"{case}-{state}-cutaway-{args.finish}-{args.backdrop}.jpg"
                render_single(
                    case,
                    state,
                    mesh_data,
                    region,
                    status,
                    spec["scale"],
                    frame,
                    cut_file,
                    cutaway_y=spec["cutaway_y"],
                )


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parse_args(argv)
    if args.dry_run:
        run_dry_check(args)
        return
    try:
        import bpy  # noqa: F401
    except ImportError:
        print(
            "Error: 'bpy' is not available in standard Python. Run with Blender:\n"
            "  blender -b --python tools/render_metallic_studio.py -- --samples 96\n"
            "Or validate meshes without Blender using:\n"
            "  python tools/render_metallic_studio.py --dry-run",
            file=sys.stderr,
        )
        sys.exit(1)
    run_blender_render(args)


if __name__ == "__main__":
    main()
