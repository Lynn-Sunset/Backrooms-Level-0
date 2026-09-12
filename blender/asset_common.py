"""Shared, deterministic modeling helpers. Blender coordinates: Z up, front -Y."""
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from surface_materials import apply_surface, project_uv

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'models'
CACHE = OUTPUT / '_tex_cache'
OUTPUT.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.images):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def texture(name, pixels, data=False):
    h, w = pixels.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    img.pixels.foreach_set(pixels.astype(np.float32).ravel())
    img.filepath_raw = str(CACHE / (name + '.png'))
    img.file_format = 'PNG'
    img.save()
    path = img.filepath_raw
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path, check_existing=True)
    img.name = name
    img.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    return img


def material(name, color, rough=.6, metal=0., emission=None, alpha=1., grain=None, seed=17):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*color, alpha)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        mat.surface_render_method = 'DITHERED'
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    if grain:
        apply_surface(mat, color, rough, metal, grain, seed, texture)
    return mat


def bevel(obj, width=.006, segments=3):
    active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = obj.modifiers.new('Manufactured edges', 'BEVEL')
    mod.width = width
    mod.segments = segments
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    normal = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    normal.keep_sharp = True
    bpy.ops.object.modifier_apply(modifier=normal.name)
    return obj


def box(name, size, pos, mat, rotation=None, edge=.004):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    if rotation:
        obj.rotation_euler = rotation
    if mat:
        obj.data.materials.append(mat)
    active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if edge:
        bevel(obj, min(edge, min(size) * .24), 2)
    project_uv(obj)
    return obj


def cylinder(name, radius, depth, pos, mat, vertices=32, rotation=None, edge=.003):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=pos)
    obj = bpy.context.object
    obj.name = name
    if rotation:
        obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    if edge:
        bevel(obj, min(edge, depth * .24, radius * .24), 2)
    project_uv(obj)
    return obj


def beam(name, a, b, width, depth, mat, edge=.004):
    a, b = Vector(a), Vector(b)
    obj = box(name, (width, depth, (b - a).length), (a + b) / 2, mat, edge=edge)
    obj.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return obj


def rod(name, points, radius, mat, resolution=2):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    curve.use_fill_caps = True
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, xyz in zip(spline.points, points):
        p.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    active(obj)
    bpy.ops.object.convert(target='MESH')
    for p in obj.data.polygons:
        p.use_smooth = True
    project_uv(obj)
    return obj


def lathe(name, profile, mat, segments=64, pos=(0, 0, 0)):
    # Seam vertices are duplicated deliberately for clean cylindrical UVs.
    verts, faces, uvs = [], [], []
    height = max(p[1] for p in profile) - min(p[1] for p in profile)
    for r, z in profile:
        for j in range(segments + 1):
            a = j / segments * math.tau
            verts.append((r * math.cos(a), r * math.sin(a), z))
            uvs.append((j / segments, (z - profile[0][1]) / max(height, .001)))
    for i in range(len(profile) - 1):
        for j in range(segments):
            a = i * (segments + 1) + j
            b = a + segments + 1
            if profile[i][0] == 0:
                faces.append((a, b + 1, b))
            elif profile[i + 1][0] == 0:
                faces.append((a, a + 1, b))
            else:
                faces.append((a, a + 1, b + 1, b))
    obj = mesh(name, verts, faces, mat)
    obj.location = pos
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
    for poly in obj.data.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            vertex = obj.data.loops[li].vertex_index
            if abs(poly.normal.z) > .98:
                co = obj.data.vertices[vertex].co
                uv.data[li].uv = (co.x / .65, co.y / .65)
            else:
                uv.data[li].uv = uvs[vertex]
    if mat.get('surface_kind') == 'stone':
        # Cylindrical UVs collapse a platform's top face into radial streaks.
        # Dressed stone needs planar projection at a consistent physical scale.
        project_uv(obj)
    return obj


def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    project_uv(obj)
    return obj


def text(name, body, pos, size, mat):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.align_x = 'CENTER'
    curve.size = size
    curve.extrude = .0003
    curve.resolution_u = 4
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (math.pi / 2, 0, 0)
    obj.data.materials.append(mat)
    active(obj)
    bpy.ops.object.convert(target='MESH')
    project_uv(obj)
    return obj


def profile_frame(name, width, height, pos, profile, mat):
    """Continuous, mitered frame in the X/Z plane, facing -Y."""
    x, y, z = pos
    vertices, faces = [], []
    for inset, relief in profile:
        w, h = width / 2 - inset, height / 2 - inset
        vertices.extend([(x - w, y - relief, z - h), (x + w, y - relief, z - h),
                         (x + w, y - relief, z + h), (x - w, y - relief, z + h)])
    for ring in range(len(profile) - 1):
        for side in range(4):
            a, b = ring * 4 + side, ring * 4 + (side + 1) % 4
            faces.append((a, b, b + 4, a + 4))
    return mesh(name, vertices, faces, mat)


def screw(name, pos, radius, metal, slot, axis='Y'):
    x, y, z = pos
    rotation = (math.pi / 2, 0, 0) if axis == 'Y' else None
    cylinder(name + '_head', radius, radius * .3, pos, metal, 16, rotation, .0006)
    if axis == 'Y':
        box(name + '_drive', (radius * 1.28, .0007, radius * .19),
            (x, y - radius * .15 - .0004, z), slot, edge=0)
    else:
        box(name + '_drive', (radius * 1.28, radius * .19, .0007),
            (x, y, z - radius * .15 - .0004), slot, edge=0)


def export(name):
    # One mesh per material keeps detailed hardware affordable in both engines.
    groups = {}
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH':
            groups.setdefault(obj.data.materials[0], []).append(obj)
    for mat, objects in groups.items():
        active(objects[0])
        for obj in objects:
            obj.select_set(True)
        bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = 'diffuser' if mat.name == 'diffuser' else name + '_' + mat.name
        # Joined meshes may inherit an arbitrarily rotated part's axes. Bake
        # those transforms so runtime bounds reflect the actual geometry.
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    bounds = [obj.matrix_world @ Vector(c) for obj in bpy.context.scene.objects if obj.type == 'MESH' for c in obj.bound_box]
    lo = [min(v[i] for v in bounds) for i in range(3)]
    hi = [max(v[i] for v in bounds) for i in range(3)]
    path = OUTPUT / (name + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', export_apply=True, export_yup=True,
                              export_texcoords=True, export_normals=True, export_cameras=False, export_lights=False)
    print('ASSET', name, 'dimensions XYZ:', [round(hi[i] - lo[i], 4) for i in range(3)], 'bytes:', path.stat().st_size)
