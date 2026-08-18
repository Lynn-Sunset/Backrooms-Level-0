"""
Backrooms Level 0 — GLB 模型导出脚本（Blender 5.2 LTS 兼容）
运行: blender --background --python export_models.py
导出到 ../models/

统一规范化尺寸（游戏 index.html 按此 1:1 / 近 1:1 放置，createModelInstance 按轴缩放兜底纠正）：
  pillar        0.32 × 3.0 × 0.32   原点=竖直中心
  light_panel   1.3  × 0.08 × 3.3   原点=外壳中心，发射面板朝下(-Z)
  exit_door     2.0  × 2.4 × 0.2    原点=底部(y=0)，宽沿 X、深沿 Z
  almond_water  0.3  × 0.8 × 0.3    原点=底部(y=0)
每个模型导出后打印世界包围盒，便于自检。
"""
import bpy
import os
import math
from mathutils import Vector

# headless 保险：确保 glTF 插件加载
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
                  emission=None, emiss=0.0, transmission=0.0, ior=1.45, texture=None):
    """Principled BSDF 材质。emission 输出到 glTF emissive(+KHR_materials_emissive_strength)。

    用节点 type 定位（跨版本稳定，Blender 5.x 节点名已本地化）。"""
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
    if transmission > 0:
        trans_in = bsdf.inputs.get('Transmission Weight') or bsdf.inputs.get('Transmission')
        trans_in.default_value = transmission
        bsdf.inputs['IOR'].default_value = ior
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emiss
    if texture is not None:
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = texture
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def gen_grain(name, base, strength, seed, horizontal=0.0):
    """numpy 生成噪点纹理（0 或 horizontal 行向条纹），供 Image Texture 节点使用。"""
    import numpy as np
    size = 256
    rng = np.random.default_rng(seed)
    n = rng.normal(0, strength, (size, size))
    if horizontal:
        row = rng.normal(0, strength * 2.0, (size, 1))
        n = n + np.tile(row, (1, size))
    arr = np.empty((size, size, 4), dtype=np.float32)
    for c in range(3):
        arr[:, :, c] = np.clip(base[c] + n, 0, 1)
    arr[:, :, 3] = 1.0
    img = bpy.data.images.new(name, size, size, alpha=True)
    img.pixels[:] = arr.reshape(-1)
    img.update()
    return img


def export_obj(name):
    path = os.path.join(OUTPUT_DIR, name + '.glb')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB',
        export_apply=True, export_texcoords=True, export_normals=True,
    )
    print(f'  ✅ 导出: {path}')


def report_box(name):
    minc = [1e9] * 3
    maxc = [-1e9] * 3
    for obj in bpy.data.objects:
        for c in obj.bound_box:
            w = obj.matrix_world @ Vector(c)
            for i in range(3):
                minc[i] = min(minc[i], w[i])
                maxc[i] = max(maxc[i], w[i])
    size = [maxc[i] - minc[i] for i in range(3)]
    # Blender Z-up: (X 宽, Y 深, Z 高) -> 提示 three.js Y-up 的高度
    print(f'  📐 {name}: X={size[0]:.3f}  Y(深)={size[1]:.3f}  Z(高)={size[2]:.3f}')


def make_screw(name, pts, steps=32):
    """按 (r, z) 轮廓生成绕 Z 轴的旋转体（Screw modifier 后转 mesh）。"""
    curve = bpy.data.curves.new(name + '_profile', 'CURVE')
    curve.dimensions = '2D'
    spline = curve.splines.new('POLY')
    spline.points.add(len(pts) - 1)
    for i, (r, z) in enumerate(pts):
        spline.points[i].co = (r, 0.0, z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('screw', 'SCREW')
    mod.angle = math.pi * 2
    mod.steps = steps
    mod.render_steps = steps
    bpy.ops.object.convert(target='MESH')
    return obj


# ============================================================
# 1. 柱子 — 混凝土方柱，顶/底收边（装饰件收在 0.32×3.0×0.32 盒内）
# ============================================================
def build_pillar():
    clear_scene()
    conc_tex = gen_grain('conc_grain', base=(0.62, 0.60, 0.52), strength=0.045, seed=7)
    mat = make_material('concrete', base=(0.62, 0.60, 0.52, 1), rough=0.8, texture=conc_tex)
    dark = make_material('concrete_dark', base=(0.55, 0.53, 0.46, 1), rough=0.85, texture=conc_tex)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    body = bpy.context.active_object
    body.name = 'pillar'
    body.scale = (0.30, 0.30, 3.0)          # 柱身略窄，为帽留边
    body.data.materials.append(mat)

    for z in (1.47, -1.47):                 # 顶/底帽，正好嵌到 ±1.5
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z))
        cap = bpy.context.active_object
        cap.name = 'pillar_cap'
        cap.scale = (0.32, 0.32, 0.06)
        cap.data.materials.append(dark)

    export_obj('pillar')
    report_box('pillar')


# ============================================================
# 2. 嵌入式荧光灯面板 — 金属外壳 + 朝下发射面板 + 分隔条
# ============================================================
def build_light_panel():
    clear_scene()
    housing = make_material('housing', base=(0.88, 0.87, 0.84, 1), rough=0.35, metal=0.6)
    diff = make_material('diffuser', base=(1.0, 1.0, 0.96, 1), rough=0.1,
                         emission=(1.0, 0.97, 0.88), emiss=0.5)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    h = bpy.context.active_object
    h.name = 'housing'
    h.scale = (1.3, 3.3, 0.08)               # X=1.3, 深=3.3, Z(高)=0.08
    h.data.materials.append(housing)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.035))   # 内凹边框（收在盒内）
    rim = bpy.context.active_object
    rim.name = 'rim'
    rim.scale = (1.2, 3.2, 0.012)
    rim.data.materials.append(housing)

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.039))   # 发射面板，朝下
    d = bpy.context.active_object
    d.name = 'diffuser'
    d.scale = (1.12, 3.08, 1)
    d.rotation_euler = (math.pi, 0, 0)
    d.data.materials.append(diff)

    for x in (-0.3, 0.3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, -0.038))
        dv = bpy.context.active_object
        dv.name = 'divider'
        dv.scale = (0.03, 3.0, 0.01)
        dv.data.materials.append(housing)

    export_obj('light_panel')
    report_box('light_panel')


# ============================================================
# 3. 出口门 — 红门板 + 深色门框 + 金把手 + 发光 EXIT 牌
# ============================================================
def build_exit_door():
    clear_scene()
    wood_tex = gen_grain('door_grain', base=(0.55, 0.10, 0.08), strength=0.05, seed=11, horizontal=1.0)
    wood = make_material('door_wood', base=(0.55, 0.10, 0.08, 1), rough=0.6, texture=wood_tex)
    frame = make_material('frame_wood', base=(0.20, 0.12, 0.06, 1), rough=0.5)
    metal = make_material('knob_metal', base=(0.85, 0.75, 0.20, 1), rough=0.2, metal=1.0)
    exitmat = make_material('exit_sign', base=(0.05, 0.5, 0.1, 1), rough=0.4,
                            emission=(0.1, 1.0, 0.3), emiss=1.2)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.15))
    p = bpy.context.active_object
    p.name = 'door'
    p.scale = (1.9, 0.1, 2.3)
    p.data.materials.append(wood)

    for loc, sc in [                      # 门框：上 + 左右
        ((0, 0, 2.33), (2.0, 0.12, 0.12)),
        ((-0.95, 0, 1.15), (0.1, 0.12, 2.3)),
        ((0.95, 0, 1.15), (0.1, 0.12, 2.3)),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        f = bpy.context.active_object
        f.name = 'frame'
        f.scale = sc
        f.data.materials.append(frame)

    for z in (0.5, 1.0, 1.7, 2.05):        # 门板横饰条（正面 -Y 侧）
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.1, z))
        s = bpy.context.active_object
        s.name = 'panel_strip'
        s.scale = (1.65, 0.02, 0.05)
        s.data.materials.append(frame)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.1,
                                        location=(0.75, -0.16, 1.1),
                                        rotation=(math.pi / 2, 0, 0))
    k = bpy.context.active_object
    k.name = 'knob'
    k.data.materials.append(metal)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.115, 2.02))
    e = bpy.context.active_object
    e.name = 'exit_sign'
    e.scale = (0.55, 0.03, 0.2)
    e.data.materials.append(exitmat)

    export_obj('exit_door')
    report_box('exit_door')


# ============================================================
# 5. 工业钢门（Level 1 出口）— 双开门 + 铆钉 + 黄黑警示带 + 发光 EXIT
#    2.0 宽(X) × ~2.34 高(Z) × ~0.15 深(Y)，原点=底部(y=0)，正面朝 -Y
# ============================================================
def build_industrial_door():
    clear_scene()
    steel = make_material('ind_steel', base=(0.42, 0.44, 0.47, 1), rough=0.35, metal=0.7)
    frame = make_material('ind_frame', base=(0.24, 0.26, 0.28, 1), rough=0.4, metal=0.65)
    rivet = make_material('ind_rivet', base=(0.55, 0.57, 0.60, 1), rough=0.3, metal=0.8)
    hazard = make_material('ind_hazard', base=(0.72, 0.60, 0.05, 1), rough=0.5, metal=0.1)
    hazdark = make_material('ind_hazard_dark', base=(0.10, 0.10, 0.10, 1), rough=0.5, metal=0.1)
    exitmat = make_material('ind_exit', base=(0.05, 0.6, 0.15, 1), rough=0.4,
                            emission=(0.1, 1.0, 0.3), emiss=1.5)

    # 门框：上 + 左 + 右（开口 ~1.8×2.2，框厚 0.14）
    for loc, sc in [((0, 0, 2.27), (2.0, 0.14, 0.14)),
                    ((-0.93, 0, 1.1), (0.14, 0.14, 2.2)),
                    ((0.93, 0, 1.1), (0.14, 0.14, 2.2))]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = bpy.context.active_object
        o.name = 'ind_frame'
        o.scale = sc
        o.data.materials.append(frame)

    for side in (-1, 1):   # 两扇门板
        bpy.ops.mesh.primitive_cube_add(size=1, location=(side * 0.44, 0, 1.08))
        leaf = bpy.context.active_object
        leaf.name = 'ind_leaf'
        leaf.scale = (0.88, 0.05, 2.16)
        leaf.data.materials.append(steel)

        # 底部黄黑警示带
        bpy.ops.mesh.primitive_cube_add(size=1, location=(side * 0.44, -0.03, 0.13))
        hz = bpy.context.active_object
        hz.name = 'ind_hazard'
        hz.scale = (0.86, 0.06, 0.26)
        hz.data.materials.append(hazard)
        for k in (-0.2, 0.0, 0.2):   # 黑色斜条（绕 Y 转 ~37°，成斜纹）
            bpy.ops.mesh.primitive_cube_add(size=1, location=(side * 0.44 + k, -0.06, 0.13))
            strip = bpy.context.active_object
            strip.name = 'ind_hazstrip'
            strip.scale = (0.10, 0.02, 0.30)
            strip.rotation_euler = (0, 0.65, 0)
            strip.data.materials.append(hazdark)

        # 铆钉（四角）
        for rx, rz in ((-0.38, 0.16), (0.38, 0.16), (-0.38, 2.0), (0.38, 2.0)):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.028, location=(side * 0.44 + rx, -0.03, rz))
            rv = bpy.context.active_object
            rv.name = 'ind_rivet'
            rv.data.materials.append(rivet)

    # 横向推杆
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.06, 1.15))
    bar = bpy.context.active_object
    bar.name = 'ind_pushbar'
    bar.scale = (1.7, 0.03, 0.08)
    bar.data.materials.append(frame)

    # 发光 EXIT 牌
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.08, 2.16))
    e = bpy.context.active_object
    e.name = 'ind_exit'
    e.scale = (0.5, 0.04, 0.16)
    e.data.materials.append(exitmat)

    export_obj('door_industrial')
    report_box('door_industrial')


# ============================================================
# 4. 杏仁水瓶 — 玻璃瓶 + 发光内液 + 瓶盖 + 标签环
# ============================================================
def build_almond_water():
    clear_scene()
    glass = make_material('glass', base=(0.75, 0.88, 1.0, 1), rough=0.05,
                          transmission=1.0, ior=1.45)
    liq = make_material('liquid', base=(0.25, 0.6, 1.0, 1), rough=0.1,
                        emission=(0.2, 0.5, 1.0), emiss=1.6)
    capmat = make_material('cap', base=(0.9, 0.9, 0.9, 1), rough=0.3, metal=0.4,
                           emission=(0.6, 0.7, 0.85), emiss=0.8)

    bottle = make_screw('bottle', [
        (0.15, 0.0), (0.155, 0.04), (0.155, 0.50), (0.13, 0.56),
        (0.06, 0.66), (0.055, 0.70), (0.0, 0.72),
    ], steps=32)
    bottle.data.materials.append(glass)

    liquid = make_screw('liquid', [
        (0.13, 0.03), (0.13, 0.45), (0.10, 0.52), (0.05, 0.58), (0.0, 0.59),
    ], steps=24)
    liquid.data.materials.append(liq)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.062, depth=0.07, location=(0, 0, 0.75))
    c = bpy.context.active_object
    c.name = 'cap'
    c.data.materials.append(capmat)

    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.008, location=(0, 0, 0.30))
    lb = bpy.context.active_object
    lb.name = 'label'
    lb.data.materials.append(capmat)

    export_obj('almond_water')
    report_box('almond_water')


if __name__ == '__main__':
    print('\n🎨 Backrooms 模型导出开始')
    build_pillar()
    build_light_panel()
    build_exit_door()
    build_industrial_door()
    build_almond_water()
    print('\n🎉 全部完成，输出到:', OUTPUT_DIR)
