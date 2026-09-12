"""A connected hexagonal garden pavilion with tiled, curved hip roofs."""
import math
from asset_common import *


def roof_layer(name, inner, outer, low, rise, tile_rows, tile_cols, tiles, dark):
    def point(side, t, u, lift=0):
        a = side * math.pi / 3
        b = (side + 1) * math.pi / 3
        radius = inner + (outer - inner) * t
        z = low + rise * (1 - t) ** 2 + .21 * t ** 8 + .13 * t ** 5 * abs(2 * u - 1) ** 4
        return (radius * ((1 - u) * math.cos(a) + u * math.cos(b)),
                radius * ((1 - u) * math.sin(a) + u * math.sin(b)), z + lift)

    # Closed underside and fascia stop daylight showing through roof joints.
    for side in range(6):
        vertices, faces = [], []
        for row in range(tile_rows + 1):
            for col in range(tile_cols + 1):
                vertices.append(point(side, row / tile_rows, col / tile_cols, -.025))
        for row in range(tile_rows):
            for col in range(tile_cols):
                a = row * (tile_cols + 1) + col
                faces.append((a, a + tile_cols + 1, a + tile_cols + 2, a + 1))
        underside = mesh(name + '_sheathing', vertices, faces, dark)
        solid = underside.modifiers.new('Roof thickness', 'SOLIDIFY')
        solid.thickness = .045
        active(underside)
        bpy.ops.object.modifier_apply(modifier=solid.name)

    buckets = [([], []) for _ in tiles]
    # Each tile has a curved cross-section, a raised lip, and slight overlap.
    for side in range(6):
        for row in range(tile_rows):
            for col in range(tile_cols):
                verts, faces = buckets[(side * 11 + row * 7 + col * 3) % len(tiles)]
                start = len(verts)
                for dr in (0, 1):
                    t = max(0, min(1, (row + dr) / tile_rows + (0 if dr == 0 else .006)))
                    for dc in range(5):
                        u = (col + dc / 4) / tile_cols
                        lift = .024 * math.sin(dc / 4 * math.pi) + (.006 if dr == 1 else 0)
                        verts.append(point(side, t, u, lift))
                for k in range(4):
                    faces.append((start + k, start + 5 + k, start + 6 + k, start + k + 1))
    for i, (verts, faces) in enumerate(buckets):
        obj = mesh(name + '_clay_tiles_' + str(i), verts, faces, tiles[i])
        for p in obj.data.polygons:
            p.use_smooth = True
    for side in range(6):
        rod(name + '_hip_ridge', [point(side, j / 24, 0, .055) for j in range(25)], .043, dark, 1)
        rod(name + '_eave_fascia', [point(side, 1, j / 20, -.025) for j in range(21)], .055, dark, 1)
        # The upturned corner is an extension of its hip ridge, not a vertical rod.
        tip = Vector(point(side, 1, 0, .055))
        radial = Vector((math.cos(side * math.pi / 3), math.sin(side * math.pi / 3), 0))
        rod(name + '_eave_tip', [tuple(tip), tuple(tip + radial * .10 + Vector((0, 0, .045))),
                                tuple(tip + radial * .19 + Vector((0, 0, .15)))], .038, dark, 2)
    # Close each tile at the eave. These scalloped ends catch the light and
    # give the clay a visible thickness when viewed from ground level.
    verts, faces = [], []
    for side in range(6):
        for col in range(tile_cols):
            start = len(verts)
            for dc in range(5):
                u = (col + dc / 4) / tile_cols
                p = point(side, 1, u, .024 * math.sin(dc / 4 * math.pi))
                verts.extend([p, (p[0], p[1], p[2] - .028)])
            for dc in range(4):
                a = start + dc * 2
                faces.append((a, a + 1, a + 3, a + 2))
    mesh(name + '_scalloped_tile_ends', verts, faces, tiles[1])


def knee_brace(origin, direction, mat):
    # A closed curved corbel joining a column to its adjacent ring beam.
    origin, direction = Vector(origin), Vector(direction)
    normal = Vector((-direction.y, direction.x, 0))
    outline = [(0, 3.05), (.075, 3.12), (.13, 3.28), (.23, 3.41), (.36, 3.48),
               (.61, 3.54), (.72, 3.65), (.72, 3.72), (0, 3.72)]
    vertices = [tuple(origin + direction * s + normal * depth + Vector((0, 0, z)))
                for depth in (-.048, .048) for s, z in outline]
    n = len(outline)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    bevel(mesh('carved_cloud_brace', vertices, faces, mat), .009, 2)


def build_pavilion():
    clear()
    stone = material('granite_platform', (.53, .55, .50), .89, grain='stone')
    edge = material('dressed_stone', (.64, .65, .59), .82, grain='stone', seed=21)
    wood = material('pavilion_timber', (.31, .135, .066), .67, grain='wood')
    darkwood = material('dark_joinery', (.18, .076, .038), .74, grain='wood', seed=31)
    roof = material('roof_ridges', (.065, .083, .083), .76, grain='roof')
    tiles = [material('clay_tile_' + str(i), (.09 + i * .009, .12 + i * .009, .122 + i * .01), .77, grain='roof')
             for i in range(4)]
    brass = material('aged_bronze', (.40, .29, .105), .42, .74, grain='bronze')
    lantern = material('lantern_silk', (.46, .08, .026), .7, emission=.4)
    grout = material('stone_joints', (.20, .23, .205), .96)
    platform = lathe('profiled_hexagonal_platform', [(0, 0), (2.97, 0), (3.02, .035), (3.02, .34),
                      (2.97, .38), (2.97, .425), (3.07, .445), (3.07, .49), (3., .54), (0, .54)], stone, 6)
    for face in platform.data.polygons:
        face.use_smooth = False
    # Separate stone tread caps. The last step meets the top face exactly;
    # no overlapping coplanar slabs or detached nosings.
    top_edge = -3 * math.sqrt(3) / 2
    for i in range(3):
        back = top_edge - (2 - i) * .32
        h = (i + 1) * .18
        box('stair_riser', (1.85, .32, h - .035), (0, back - .16, (h - .035) / 2), stone, edge=.009)
        box('solid_tread_cap', (1.9, .335, .035), (0, back - .1675, h - .0175), edge, edge=.004)
        for x in (-.60, 0, .60):
            box('tread_joint', (.006, .325, .0015), (x, back - .167, h + .001), grout, edge=0)
    # Radial dressed paving with a central compass/lotus medallion.
    for i in range(6):
        a = i * math.pi / 3
        b = (i + 1) * math.pi / 3
        p, q = Vector((3 * math.cos(a), 3 * math.sin(a), .542)), Vector((3 * math.cos(b), 3 * math.sin(b), .542))
        for t in (.33, .67):
            c = p.lerp(q, t)
            beam('paving_joint', tuple(c * .39 + Vector((0, 0, .331))), tuple(c), .007, .002, grout, 0)
        middle = p.lerp(q, .5)
        beam('foundation_joint', (middle.x * 1.005, middle.y * 1.005, .045),
             (middle.x * 1.005, middle.y * 1.005, .338), .008, .005, grout, 0)
    for radius in (.76, .82, 1.06):
        lathe('stone_medallion_ring', [(radius + .012, .543), (radius, .543)], edge, 64)
    for i in range(8):
        a = i * math.tau / 8
        direction = Vector((math.cos(a), math.sin(a), 0))
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        vertices = [tuple(direction * r + tangent * w + Vector((0, 0, .544)))
                    for r, w in ((.06, 0), (.37, -.11), (.72, 0), (.37, .11))]
        mesh('inlaid_lotus_petal', vertices, [(0, 1, 2, 3)], grout)
    radius = 2.43
    positions = [(radius * math.cos(i * math.pi / 3), radius * math.sin(i * math.pi / 3)) for i in range(6)]
    for i, (x, y) in enumerate(positions):
        lathe('carved_column_base', [(0, .54), (.185, .54), (.205, .57), (.205, .65), (.175, .71),
                                    (.135, .75), (0, .75)], edge, 32, (x, y, 0))
        cylinder('timber_column', .115, 3.05, (x, y, 2.265), wood, 32, edge=.006)
        cylinder('column_foot_ring', .128, .065, (x, y, .79), darkwood, 32)
        for petal in range(8):
            angle = petal * math.tau / 8
            vertices = []
            for da, r, z in ((0, .186, .57), (-.12, .211, .62), (0, .175, .716), (.12, .211, .62), (0, .22, .633)):
                vertices.append((x + r * math.cos(angle + da), y + r * math.sin(angle + da), z))
            obj = mesh('lotus_column_carving', vertices, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], stone)
            for face in obj.data.polygons:
                face.use_smooth = True
        a = i * math.pi / 3
        for z, length in ((3.78, .39), (3.9, .62), (4.02, .83)):
            box('bracket_radial', (length, .145, .11), (x, y, z), wood, rotation=(0, 0, a), edge=.01)
            box('bracket_cross', (.145, length * .84, .11), (x, y, z + .045), darkwood, rotation=(0, 0, a), edge=.01)
    for i in range(6):
        a = Vector((*positions[i], 0))
        b = Vector((*positions[(i + 1) % 6], 0))
        center = (a + b) / 2
        tangent = (b - a).normalized()
        yaw = math.atan2(tangent.y, tangent.x)
        knee_brace(a, tangent, wood)
        knee_brace(b, -tangent, wood)
        for z, width, depth in ((3.67, .16, .22), (3.87, .21, .14)):
            box('ring_beam', (2.46, width, depth), (center.x, center.y, z), darkwood, rotation=(0, 0, yaw), edge=.009)
        # A continuous lattice frieze attached to the beams.
        for z in (3.2, 3.48):
            box('frieze_rail', (2.22, .055, .055), (center.x, center.y, z), wood, rotation=(0, 0, yaw))
        for k in range(6):
            c = center + tangent * ((k - 2.5) * .33)
            for sign in (-1, 1):
                p = c - tangent * .15
                q = c + tangent * .15
                beam('lattice_diagonal', (p.x, p.y, 3.2 if sign == 1 else 3.48),
                     (q.x, q.y, 3.48 if sign == 1 else 3.2), .026, .04, wood, .002)
        # Fine horizontal stringing and pegged mortise joints.
        for z in (3.225, 3.455):
            box('frieze_inlay', (2.20, .058, .008), (center.x, center.y, z), brass, rotation=(0, 0, yaw), edge=.001)
        for p in (a.lerp(b, .055), a.lerp(b, .945)):
            for z in (3.58, 3.74):
                cylinder('joinery_peg', .018, .017, (p.x, p.y, z), darkwood, 12,
                         rotation=(math.pi / 2, 0, yaw), edge=.001)
        if i == 4:
            continue  # entrance; no bench or railing across the stairs
        for t in (.22, .78):
            c = a.lerp(b, t)
            box('bench_leg', (.09, .18, .41), (c.x, c.y, .745), darkwood, rotation=(0, 0, yaw))
        box('bench_seat', (2.22, .37, .09), (center.x, center.y, .99), wood, rotation=(0, 0, yaw), edge=.012)
        box('bench_backrail', (2.22, .08, .09), (center.x, center.y, 1.43), darkwood, rotation=(0, 0, yaw), edge=.009)
        for k in range(7):
            c = a.lerp(b, (k + 1) / 8)
            box('bench_spindle', (.028, .045, .36), (c.x, c.y, 1.22), wood, rotation=(0, 0, yaw), edge=.004)
        box('bench_lower_rail', (2.17, .055, .045), (center.x, center.y, 1.065), darkwood, rotation=(0, 0, yaw))
        for t in (.30, .70):
            c = a.lerp(b, t)
            diamond = [tuple(c + tangent * s + Vector((0, 0, z)))
                       for s, z in ((0, 1.115), (.095, 1.245), (0, 1.375), (-.095, 1.245), (0, 1.115))]
            rod('bench_lozenge', diamond, .012, wood, 1)
    cylinder('coffered_ceiling', 2.12, .09, (0, 0, 4.03), darkwood, 6)
    for i, (x, y) in enumerate(positions):
        beam('ceiling_radial', (0, 0, 3.975), (x * .87, y * .87, 3.975), .07, .1, wood)
    for radius in (1.05, 1.63):
        ring = [(radius * math.cos(i * math.pi / 3), radius * math.sin(i * math.pi / 3), 3.96) for i in range(7)]
        rod('coffered_ceiling_ring', ring, .035, wood, 1)
    roof_layer('lower_roof', .43, 3.34, 4.00, 1.34, 15, 22, tiles, roof)
    cylinder('upper_drum', .68, .34, (0, 0, 5.37), darkwood, 6)
    roof_layer('upper_roof', .10, 1.52, 5.28, .96, 9, 12, tiles, roof)
    lathe('bronze_finial', [(0, 6.2), (.14, 6.2), (.16, 6.26), (.12, 6.31), (.13, 6.36),
                           (.16, 6.43), (.12, 6.5), (.06, 6.55), (.045, 6.65), (0, 6.73)], brass, 32)
    for i in range(6):
        a = i * math.pi / 3
        x, y = math.cos(a) * 3.17, math.sin(a) * 3.17
        rod('bell_cord', [(x, y, 4.19), (x, y, 3.98)], .006, darkwood, 0)
        lathe('eave_bell', [(0, 3.87), (.045, 3.87), (.047, 3.89), (.03, 3.94), (.022, 3.97), (0, 3.97)], brass, 20, (x, y, 0))
    rod('lantern_hanger', [(0, 0, 3.98), (0, 0, 3.76)], .007, brass, 0)
    lathe('silk_lantern', [(0, 3.34), (.11, 3.34), (.16, 3.40), (.18, 3.51), (.16, 3.66), (.11, 3.72), (0, 3.72)], lantern, 32)
    for z in (3.34, 3.71):
        cylinder('lantern_band', .115, .035, (0, 0, z), brass, 24)
    for i in range(12):
        a = i * math.tau / 12
        rod('lantern_bamboo_rib', [(r * math.cos(a), r * math.sin(a), z)
            for r, z in ((.11, 3.34), (.16, 3.40), (.183, 3.51), (.163, 3.66), (.11, 3.72))], .004, brass, 1)
    rod('tassel', [(0, 0, 3.32), (0, 0, 3.13)], .018, lantern)
    box('entrance_nameboard', (1.08, .055, .245), (0, -2.20, 3.73), darkwood, edge=.011)
    profile_frame('nameboard_border', 1.03, .205, (0, -2.23, 3.73),
                  [(0, 0), (.005, .003), (.009, .003)], brass)
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    if font_path.exists():
        # Convert to mesh before export; the game never needs a local font.
        curve = bpy.data.curves.new('pavilion_name', 'FONT')
        curve.body = '听雨亭'
        curve.font = bpy.data.fonts.load(str(font_path))
        curve.align_x = 'CENTER'
        curve.size = .135
        curve.extrude = .001
        obj = bpy.data.objects.new('pavilion_name', curve)
        bpy.context.collection.objects.link(obj)
        obj.location = (0, -2.235, 3.68)
        obj.rotation_euler = (math.pi / 2, 0, 0)
        obj.data.materials.append(brass)
        active(obj)
        bpy.ops.object.convert(target='MESH')
        project_uv(obj)
    else:
        text('pavilion_name', 'RAIN PAVILION', (0, -2.235, 3.70), .073, brass)
    export('pavilion')
