"""Check exported GLBs, embedded resources, geometry and per-asset budgets.

Run: python scripts/validate-models.py
Writes artifacts/model-quality/validation.json; exits nonzero on broken assets.
"""
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent
BUDGETS = {'pillar': 4500, 'light_panel': 9000, 'exit_door': 12000,
           'door_industrial': 16000, 'almond_water': 16000, 'pavilion': 110000}
COMPONENTS = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2),
              5125: ('I', 4), 5126: ('f', 4)}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def validate(name, budget):
    raw = (ROOT / 'models' / (name + '.glb')).read_bytes()
    magic, version, length = struct.unpack_from('<4sII', raw)
    assert magic == b'glTF' and version == 2 and length == len(raw), 'Invalid GLB header'
    offset, chunks = 12, {}
    while offset < len(raw):
        size, kind = struct.unpack_from('<I4s', raw, offset)
        assert size % 4 == 0 and offset + 8 + size <= len(raw), 'Invalid GLB chunk'
        chunks[kind] = raw[offset + 8:offset + 8 + size]
        offset += 8 + size
    data, binary = json.loads(chunks[b'JSON']), chunks[b'BIN\x00']
    assert data['asset']['version'] == '2.0'
    assert all('uri' not in b for b in data['buffers']), 'External binary resource'
    assert all('bufferView' in image and image.get('mimeType') in ('image/png', 'image/jpeg')
               for image in data.get('images', [])), 'Non-embedded texture'

    def accessor(index):
        a = data['accessors'][index]
        view = data['bufferViews'][a['bufferView']]
        code, component_size = COMPONENTS[a['componentType']]
        width = WIDTHS[a['type']]
        packed = component_size * width
        stride = view.get('byteStride', packed)
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        end = start + (a['count'] - 1) * stride + packed
        assert end <= len(binary) and end <= view.get('byteOffset', 0) + view['byteLength'], 'Accessor out of range'
        return [struct.unpack_from('<' + code * width, binary, start + j * stride) for j in range(a['count'])]

    triangles, vertices, degenerate = 0, 0, 0
    for mesh in data['meshes']:
        for prim in mesh['primitives']:
            assert prim.get('mode', 4) == 4, 'Expected triangle primitives'
            attrs = prim['attributes']
            positions = accessor(attrs['POSITION'])
            normals = accessor(attrs['NORMAL'])
            assert len(positions) == len(normals)
            assert all(math.isfinite(v) for p in positions + normals for v in p), 'Non-finite geometry'
            assert all(.98 < sum(v * v for v in n) < 1.02 for n in normals), 'Non-unit normals'
            indices = [x[0] for x in accessor(prim['indices'])]
            assert len(indices) % 3 == 0 and max(indices) < len(positions), 'Invalid triangle indices'
            mat = data['materials'][prim['material']]
            if 'baseColorTexture' in mat.get('pbrMetallicRoughness', {}) or 'normalTexture' in mat:
                assert 'TEXCOORD_0' in attrs, 'Textured material has no UVs'
                uvs = accessor(attrs['TEXCOORD_0'])
                assert len(uvs) == len(positions) and all(math.isfinite(v) for uv in uvs for v in uv), 'Invalid UVs'
            for i in range(0, len(indices), 3):
                a, b, c = (positions[j] for j in indices[i:i + 3])
                u, v = [b[j] - a[j] for j in range(3)], [c[j] - a[j] for j in range(3)]
                cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                if sum(x * x for x in cross) < 1e-22:
                    degenerate += 1
            triangles += len(indices) // 3
            vertices += len(positions)
    assert triangles <= budget, f'Triangle budget exceeded: {triangles} > {budget}'
    assert degenerate == 0, f'{degenerate} degenerate triangles'
    assert len(data['meshes']) <= 12, 'Excessive material draw calls'
    if name == 'light_panel':
        assert any(n.get('name') == 'diffuser' for n in data['nodes']), 'Flicker mesh missing'
    assert len(raw) < 24 * 1024 * 1024, 'Asset exceeds 24 MiB download budget'
    normal_materials = sum('normalTexture' in mat for mat in data['materials'])
    if name != 'almond_water':
        assert normal_materials > 0, 'Surface relief maps missing'
    else:
        assert any(mat.get('extensions', {}).get('KHR_materials_transmission', {}).get('transmissionFactor', 0) > .9
                   for mat in data['materials']), 'Physical glass transmission missing'
    return {'asset': name, 'bytes': len(raw), 'triangles': triangles, 'budget': budget,
            'vertices': vertices, 'meshes': len(data['meshes']), 'materials': len(data['materials']),
            'embedded_images': len(data.get('images', [])), 'normal_mapped_materials': normal_materials,
            'degenerate_triangles': degenerate, 'status': 'pass'}


results = []
for name, budget in BUDGETS.items():
    try:
        result = validate(name, budget)
    except (AssertionError, KeyError, ValueError, struct.error) as error:
        result = {'asset': name, 'status': 'fail', 'error': str(error)}
    results.append(result)
    print(json.dumps(result))
out = ROOT / 'artifacts' / 'model-quality' / 'validation.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
raise SystemExit(0 if all(r['status'] == 'pass' for r in results) else 1)
