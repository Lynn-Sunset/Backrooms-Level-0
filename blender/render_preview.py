"""
Backrooms GLB 模型预览渲染脚本（Blender 5.2 headless）
运行: blender --background --factory-startup --python render_preview.py
把 models/*.glb 逐个导入，用 Cycles(CPU) 渲染 1024×768 PNG 到 artifacts/model-quality/
用于视觉检查建模质量。
"""
import bpy
import os
import math
from mathutils import Vector

try:
    import addon_utils
    addon_utils.enable('io_scene_gltf2', default_set=True)
except Exception as e:
    print('  ⚠️ 启用 glTF 插件失败:', e)

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE, '..', 'models')
OUT_DIR = os.path.join(BASE, '..', 'artifacts', 'model-quality')
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NAMES = ['pillar', 'light_panel', 'exit_door', 'door_industrial', 'almond_water', 'pavilion']


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes): bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials): bpy.data.materials.remove(block)
    for block in list(bpy.data.curves): bpy.data.curves.remove(block)
    for block in list(bpy.data.lights): bpy.data.lights.remove(block)
    for block in list(bpy.data.cameras): bpy.data.cameras.remove(block)
    for block in list(bpy.data.images): bpy.data.images.remove(block)
    for block in list(bpy.data.worlds): bpy.data.worlds.remove(block)


def scene_bounds():
    minc = [1e9] * 3
    maxc = [-1e9] * 3
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for c in obj.bound_box:
            w = obj.matrix_world @ Vector(c)
            for i in range(3):
                minc[i] = min(minc[i], w[i])
                maxc[i] = max(maxc[i], w[i])
    return Vector(minc), Vector(maxc)


def setup_stage(center, size, ground_z, ground=True):
    # 世界：暖灰渐变感（纯色即可）
    world = bpy.data.worlds.new('W')
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.055, 0.052, 0.048, 1.0)
    bg.inputs['Strength'].default_value = 1.0

    # 主光：太阳
    sun_data = bpy.data.lights.new('sun', 'SUN')
    sun_data.energy = 3.2
    sun_data.angle = math.radians(2)
    sun = bpy.data.objects.new('sun', sun_data)
    sun.rotation_euler = (math.radians(52), 0, math.radians(38))
    bpy.context.collection.objects.link(sun)

    # 补光：大面光
    fill_data = bpy.data.lights.new('fill', 'AREA')
    fill_data.energy = 60
    fill_data.size = max(size * 1.2, 1.5)
    fill = bpy.data.objects.new('fill', fill_data)
    fill.location = (center.x + size * 0.5, center.y - size * 0.6, center.z + size * 0.7)
    fill.rotation_euler = (math.radians(60), 0, math.radians(-35))
    bpy.context.collection.objects.link(fill)

    # 地面：阴影接收（shadow catcher）
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=size * 12, location=(center.x, center.y, ground_z - 0.01))
        floor = bpy.context.active_object
        floor.name = 'ground'
        floor.is_shadow_catcher = True


def setup_camera(center, size, name):
    cam_data = bpy.data.cameras.new('cam')
    cam_data.lens = 50
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = size * 1.66
    cam = bpy.data.objects.new('cam', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    # v2：更近的机位（1.6× 而非 2.3×），细节像素更多，便于视觉管线精确取证
    dist = max(size * 1.6, 0.9)
    cam.location = (
        center.x + dist * (0.30 if name != 'pavilion' else .58),
        center.y - dist * 0.95,
        center.z + dist * (-0.80 if name == 'light_panel' else .30),
    )
    look = Vector(center)
    direction = look - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def render_model(name, detail=False):
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS_DIR, name + '.glb'))
    bpy.context.view_layer.update()

    minc, maxc = scene_bounds()
    center = (minc + maxc) / 2
    size = max(maxc - minc)
    print(f'  {name}: center={tuple(round(v,2) for v in center)} size={size:.2f}')

    setup_stage(center, size, minc.z, name != 'light_panel')
    setup_camera(center, size, name)
    if detail and name == 'pavilion':
        camera = bpy.context.scene.camera
        camera.data.ortho_scale = 5.0
        camera.location = (2.5, -8.5, 4.0)
        camera.rotation_euler = (Vector((0, -1.2, 2.2)) - camera.location).to_track_quat('-Z', 'Y').to_euler()

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.filepath = os.path.join(OUT_DIR, name + ('-detail' if detail else '') + '.png')
    scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print(f'  ✅ 渲染完成: {scene.render.filepath}')


if __name__ == '__main__':
    import sys
    if '--' in sys.argv:
        MODEL_NAMES = sys.argv[sys.argv.index('--') + 1:]
    detail = '--detail' in MODEL_NAMES
    MODEL_NAMES = [name for name in MODEL_NAMES if name != '--detail']
    print('\n🎥 Backrooms 模型预览渲染开始')
    failures = []
    for name in MODEL_NAMES:
        try:
            render_model(name, detail)
        except Exception as e:
            print(f'  ❌ {name} 渲染失败: {e}')
            failures.append(name)
    print('\n🎉 全部渲染完成，输出到:', OUT_DIR)
    if failures:
        raise RuntimeError('Preview render failed: ' + ', '.join(failures))
