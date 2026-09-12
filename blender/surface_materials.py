"""Deterministic, tileable PBR surfaces with grain, pores and restrained wear."""
import math
from functools import lru_cache

import bpy
import numpy as np


def noise(rng, size, cells):
    grid = rng.random((cells, cells)).astype(np.float32)
    xy = np.arange(size, dtype=np.float32) * cells / size
    indices = xy.astype(int)
    f = xy - indices
    f = f * f * (3 - 2 * f)
    x, y = indices[None, :], indices[:, None]
    a = grid[y % cells, x % cells] * (1 - f[None, :]) + grid[y % cells, (x + 1) % cells] * f[None, :]
    b = grid[(y + 1) % cells, x % cells] * (1 - f[None, :]) + grid[(y + 1) % cells, (x + 1) % cells] * f[None, :]
    return a * (1 - f[:, None]) + b * f[:, None]


@lru_cache(maxsize=8)
def surface(kind, seed):
    size = 1024 if kind == 'wood' else 512
    rng = np.random.default_rng(seed)
    x, y = np.meshgrid(np.arange(size, dtype=np.float32) / size, np.arange(size, dtype=np.float32) / size)
    broad = noise(rng, size, 5)
    medium = noise(rng, size, 23)
    fine = noise(rng, size, 96)
    fleck = rng.random((size, size)).astype(np.float32)
    patina = np.zeros_like(x)

    if kind == 'wood':
        # Growth rings bend around two knots. Longitudinal pores break up the
        # rings, so the result reads as timber rather than straight stripes.
        warp = x + .021 * np.sin(y * math.tau + broad * 2) + .008 * np.sin(y * math.tau * 3)
        knots = np.zeros_like(x)
        for kx, ky, radius in ((.24, .33, .045), (.72, .81, .025)):
            dx = (x - kx + .5) % 1 - .5
            dy = (y - ky + .5) % 1 - .5
            r = np.sqrt((dx / radius) ** 2 + (dy / (radius * 2.8)) ** 2)
            influence = np.exp(-r * r * .35)
            warp += np.sign(dx) * .027 * influence
            knots += influence * (.5 + .5 * np.sin(r * 9))
        grain = (.5 + .5 * np.sin(warp * math.tau * 58 + medium * 2)) ** 10
        threads = (.5 + .5 * np.sin(warp * math.tau * 151 + fine * 1.8)) ** 18
        pores = threads * np.clip((noise(rng, size, 52) - .35) * 2, 0, 1)
        value = 1.13 - grain * .24 - knots * .20 - pores * .18 + (broad - .5) * .25
        height = .00032 * broad - .00028 * pores - .00011 * grain
        roughness = .13 * grain + .12 * pores + .12 * (broad - .5)
    elif kind == 'stone':
        pores = np.clip((fleck - .93) * 14, 0, 1) * (.3 + fine)
        vein = np.exp(-np.abs(np.sin((x * 2 + y + broad * .7) * math.tau)) * 20)
        value = .84 + .28 * broad + .14 * (medium - .5) + .16 * (fleck - .5) - .13 * pores - .07 * vein
        height = .0009 * medium + .0003 * fine - .0008 * pores
        roughness = .1 * (medium - .5) + .10 * pores
    elif kind == 'roof':
        pits = np.clip((fleck - .90) * 9, 0, 1)
        value = .74 + .4 * broad + .19 * (medium - .5) + .1 * (fleck - .5)
        height = .0007 * medium + .00025 * fine - .0004 * pits
        roughness = .16 * (broad - .5) + .12 * pits
    elif kind == 'paper':
        value = .98 + .025 * (fleck - .5) + .035 * (broad - .5)
        height = .000035 * fleck + .00002 * fine
        roughness = .055 * (fine - .5)
    elif kind in ('brushed', 'bronze'):
        streaks = rng.random(size).astype(np.float32)[None, :]
        streaks = np.broadcast_to(streaks, (size, size))
        scratches = np.clip((streaks - .95) * 18, 0, 1) * (.3 + medium * .7)
        value = .9 + .16 * broad + .09 * (streaks - .5) - .08 * scratches
        height = .000025 * streaks - .00005 * scratches
        roughness = .12 * (streaks - .5) + .09 * medium
        if kind == 'bronze':
            patina = np.clip((broad * .25 + medium * .75 - .62) * 4, 0, .45)
            roughness += patina * .30
            height += patina * .0001
    else:  # powder coating, with shallow orange peel and sparse paint wear
        chips = np.clip((fine * .45 + fleck * .55 - .88) * 14, 0, 1)
        grime = np.clip((broad - .58) * 2.5, 0, .6)
        value = 1.02 - grime * .09 + .035 * (medium - .5) - chips * .22
        height = .00010 * fine - .00013 * chips
        roughness = .13 * grime + .08 * (fine - .5) + .15 * chips

    # Tangent-space normals derived from a physical height field; derivatives
    # wrap at the boundaries, preserving seamless filtering and mipmaps.
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * size
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * size
    normal = np.stack((-dx, -dy, np.ones_like(dx)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return value, roughness, normal * .5 + .5, patina


def apply_surface(mat, color, rough, metal, kind, seed, make_texture):
    value, variation, normal, patina = surface(kind, seed)
    size = len(value)
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(np.array(color)[None, None, :] * value[:, :, None], 0, 1)
    if kind == 'bronze':
        rgba[:, :, :3] = rgba[:, :, :3] * (1 - patina[:, :, None]) + np.array([.075, .135, .10]) * patina[:, :, None]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    albedo = nodes.new('ShaderNodeTexImage')
    albedo.image = make_texture(mat.name + '_basecolor', rgba)
    links.new(albedo.outputs['Color'], bsdf.inputs['Base Color'])

    rgba[:, :, :3] = np.clip(rough + variation[:, :, None], .08, .98)
    rough_node = nodes.new('ShaderNodeTexImage')
    rough_node.image = make_texture(mat.name + '_roughness', rgba, True)
    links.new(rough_node.outputs['Color'], bsdf.inputs['Roughness'])

    normal_name = f'{kind}_{seed}_normal'
    normal_image = bpy.data.images.get(normal_name)
    if normal_image is None:
        rgba[:, :, :3] = normal
        normal_image = make_texture(normal_name, rgba, True)
    node = nodes.new('ShaderNodeTexImage')
    node.image = normal_image
    normal_node = nodes.new('ShaderNodeNormalMap')
    links.new(node.outputs['Color'], normal_node.inputs['Color'])
    links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])
    if kind == 'bronze':
        rgba[:, :, :3] = metal * (1 - patina[:, :, None] * .8)
        node = nodes.new('ShaderNodeTexImage')
        node.image = make_texture(mat.name + '_metallic', rgba, True)
        links.new(node.outputs['Color'], bsdf.inputs['Metallic'])
    mat['surface_kind'] = kind


def project_uv(obj):
    """Use physical coordinates and follow each timber member's long axis."""
    if not obj.data.materials:
        return
    mat = obj.data.materials[0]
    if mat is None or 'surface_kind' not in mat:
        return
    kind = mat['surface_kind']
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
    bounds = np.array([v.co[:] for v in obj.data.vertices])
    long_axis = int(np.argmax(np.ptp(bounds, axis=0)))
    # Vary the crop across separate planks while retaining reproducibility.
    import zlib
    phase = (zlib.crc32(obj.name.encode()) % 991) / 991
    for face in obj.data.polygons:
        dominant = max(range(3), key=lambda i: abs(face.normal[i]))
        axes = [i for i in range(3) if i != dominant]
        if kind in ('wood', 'brushed', 'bronze') and long_axis in axes:
            axes.remove(long_axis)
            axes.append(long_axis)
        su, sv = (.36, 1.5) if kind == 'wood' else (.65, .65)
        for li in face.loop_indices:
            co = obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv = (co[axes[0]] / su + phase, co[axes[1]] / sv + phase * .37)
