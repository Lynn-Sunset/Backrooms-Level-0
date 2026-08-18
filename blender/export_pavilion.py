"""
苏式园林六角亭 GLB 导出脚本（Blender 5.2 LTS）
运行: blender --background --python blender/export_pavilion.py
导出到 ../models/pavilion.glb

尺寸：直径约 7.2m，高约 6.5m，原点=地面中心。
"""
import bpy
import os
import math
from mathutils import Vector, Euler

try:
    import addon_utils
    addon_utils.enable('io_scene_gltf2', default_set=True)
except Exception as e:
    print('  ⚠️ 启用 glTF 插件失败:', e)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes): bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials): bpy.data.materials.remove(block)
    for block in list(bpy.data.curves): bpy.data.curves.remove(block)
    for block in list(bpy.data.images): bpy.data.images.remove(block)


def make_material(name, base=(0.8, 0.8, 0.8, 1.0), rough=0.5, metal=0.0,
                  emission=None, emiss=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None:
        out = nodes.new('ShaderNodeOutputMaterial')
    if not any(l.to_node == out and l.to_socket.name == 'Surface' for l in nt.links):
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = base
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emiss
    return mat


def add_cylinder(name, radius, depth, location, vertices=12, rotation=None, material=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    if rotation is not None:
        obj.rotation_euler = Euler(rotation, 'XYZ')
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_cone(name, radius1, radius2, depth, location, vertices=6, rotation=None, material=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    if rotation is not None:
        obj.rotation_euler = Euler(rotation, 'XYZ')
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_box(name, size, location, rotation=None, material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    if rotation is not None:
        obj.rotation_euler = Euler(rotation, 'XYZ')
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_sphere(name, radius, location, material=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=10, ring_count=6)
    obj = bpy.context.active_object
    obj.name = name
    if material is not None:
        obj.data.materials.append(material)
    return obj


def build_pavilion():
    clear_scene()
    stone = make_material('pav_stone', base=(0.78, 0.78, 0.74, 1), rough=0.85, metal=0.0)
    wood = make_material('pav_wood', base=(0.52, 0.25, 0.12, 1), rough=0.55, metal=0.0)
    wood_dark = make_material('pav_wood_dark', base=(0.35, 0.17, 0.08, 1), rough=0.6, metal=0.0)
    roof = make_material('pav_roof', base=(0.22, 0.22, 0.20, 1), rough=0.5, metal=0.05)
    gold = make_material('pav_gold', base=(0.72, 0.55, 0.10, 1), rough=0.25, metal=0.8)

    R = 2.55  # 柱心半径
    # 1) 六角石台基 + 台阶
    add_cylinder('base_lower', 3.05, 0.45, (0, 0, 0.225), vertices=6, material=stone)
    add_cylinder('base_upper', 2.80, 0.28, (0, 0, 0.56), vertices=6, material=stone)
    add_box('step_1', (2.4, 0.14, 0.85), (0, -3.28, 0.66), material=stone)
    add_box('step_2', (2.2, 0.12, 0.75), (0, -3.52, 0.53), material=stone)
    add_box('step_side_l', (0.16, 0.35, 0.90), (-1.26, -3.30, 0.48), material=stone)
    add_box('step_side_r', (0.16, 0.35, 0.90), (1.26, -3.30, 0.48), material=stone)

    # 2) 六根柱 + 柱础 + 柱头
    for i in range(6):
        a = i / 6 * math.pi * 2
        x = math.cos(a) * R
        y = math.sin(a) * R
        add_cylinder('column_base', 0.20, 0.22, (x, y, 0.70), vertices=10, material=stone)
        add_cylinder('column', 0.105, 2.95, (x, y, 2.30), vertices=12, material=wood)
        add_box('capital', (0.40, 0.40, 0.12), (x, y, 3.82), material=wood_dark)

    # 3) 柱间美人靠（座凳 + 靠背 + 栏杆柱）
    for i in range(6):
        a0 = i / 6 * math.pi * 2
        a1 = (i + 1) / 6 * math.pi * 2
        ca = (a0 + a1) / 2
        mx = math.cos(ca) * R * math.cos(math.pi / 6)
        my = math.sin(ca) * R * math.cos(math.pi / 6)
        yaw = ca + math.pi / 2
        add_box('bench', (2.15, 0.08, 0.35), (mx, my, 0.58), rotation=(0, 0, yaw), material=wood)
        add_box('back_rail', (2.15, 0.08, 0.08), (mx, my, 0.95), rotation=(0, 0, yaw), material=wood)
        for k in range(1, 5):
            t = k / 5
            bx = math.cos(a0) * R * (1 - t) + math.cos(a1) * R * t
            by = math.sin(a0) * R * (1 - t) + math.sin(a1) * R * t
            add_cylinder('baluster', 0.035, 0.62, (bx, by, 0.75), vertices=6, material=wood)

    # 4) 檐枋（六面围合梁） + 挂落
    for i in range(6):
        a0 = i / 6 * math.pi * 2
        a1 = (i + 1) / 6 * math.pi * 2
        ca = (a0 + a1) / 2
        mx = math.cos(ca) * R * math.cos(math.pi / 6)
        my = math.sin(ca) * R * math.cos(math.pi / 6)
        yaw = ca + math.pi / 2
        add_box('beam', (2.30, 0.14, 0.16), (mx, my, 3.86), rotation=(0, 0, yaw), material=wood_dark)
        for k in (-0.18, 0, 0.18):
            add_box('lattice', (1.55, 0.05, 0.05), (mx + k * math.cos(yaw), my + k * math.sin(yaw), 3.62), rotation=(0, 0, yaw), material=wood_dark)

    # 5) 斗拱（柱头小木块）
    for i in range(6):
        a = i / 6 * math.pi * 2
        x = math.cos(a) * R
        y = math.sin(a) * R
        add_box('dougong_1', (0.52, 0.10, 0.18), (x + 0.18, y, 3.94), rotation=(0, 0, a), material=wood)
        add_box('dougong_2', (0.18, 0.10, 0.52), (x, y + 0.18, 3.94), rotation=(0, 0, a), material=wood)

    # 6) 藻井天花
    add_cylinder('ceiling', 2.05, 0.10, (0, 0, 4.04), vertices=6, material=wood_dark)

    # 7) 下层六角飞檐屋面（上收下放锥台）
    add_cone('roof_lower', 3.35, 0.85, 1.30, (0, 0, 4.95), vertices=6, material=roof)
    # 屋脊线
    for i in range(6):
        a = i / 6 * math.pi * 2
        x1, y1 = math.cos(a) * 0.9, math.sin(a) * 0.9
        x2, y2 = math.cos(a) * 3.35, math.sin(a) * 3.35
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        yaw = a + math.pi / 2
        pitch = math.atan2(0.62, 2.45)
        add_box('ridge_lower', (0.07, 0.07, 2.55), (cx, cy, 4.92), rotation=(pitch, 0, yaw), material=roof)
    # 飞檐翘角 + 风铃
    for i in range(6):
        a = i / 6 * math.pi * 2
        ex, ey = math.cos(a) * 3.42, math.sin(a) * 3.42
        add_cylinder('eave_horn', 0.045, 0.75, (ex, ey, 4.30), vertices=6, rotation=(0, 0, a + math.pi / 2), material=roof)
        add_sphere('wind_bell', 0.06, (ex, ey, 4.05), material=gold)

    # 8) 上层六角攒尖屋面 + 宝顶
    add_cone('roof_upper', 1.75, 0.45, 0.85, (0, 0, 5.75), vertices=6, material=roof)
    add_sphere('finial_ball', 0.18, (0, 0, 6.20), material=gold)
    add_cylinder('finial_neck', 0.08, 0.18, (0, 0, 6.38), vertices=8, material=gold)
    add_cone('finial_tip', 0.07, 0.0, 0.24, (0, 0, 6.56), vertices=8, material=gold)

    # 9) 底部台基外围栏杆（可选，简单处理为六根矮柱）
    for i in range(6):
        a = i / 6 * math.pi * 2
        x = math.cos(a) * 3.05
        y = math.sin(a) * 3.05
        add_cylinder('base_post', 0.09, 0.5, (x, y, 0.48), vertices=8, material=stone)


def export_pavilion():
    path = os.path.join(OUTPUT_DIR, 'pavilion.glb')
    

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB',
        export_apply=True, export_texcoords=True, export_normals=True,
    )
    print('  ✅ 导出:', path)


def report_box():
    minc = [1e9] * 3
    maxc = [-1e9] * 3
    for obj in bpy.data.objects:
        for c in obj.bound_box:
            w = obj.matrix_world @ Vector(c)
            for i in range(3):
                minc[i] = min(minc[i], w[i])
                maxc[i] = max(maxc[i], w[i])
    size = [maxc[i] - minc[i] for i in range(3)]
    print(f'  📐 pavilion: X={size[0]:.3f}  Y(深)={size[1]:.3f}  Z(高)={size[2]:.3f}')
    print(f'  📐 pavilion: X[{minc[0]:.3f},{maxc[0]:.3f}] Y[{minc[1]:.3f},{maxc[1]:.3f}] Z[{minc[2]:.3f},{maxc[2]:.3f}]')


if __name__ == '__main__':
    print('\n🎨 苏式园林六角亭建模开始')
    build_pavilion()
    report_box()
    export_pavilion()
    print('\n🎉 亭子导出完成')
