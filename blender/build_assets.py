"""Build the six game assets with Blender: blender -b --python blender/build_assets.py.

All dimensions are in metres. Sources are deterministic; GLBs embed their textures.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_common import *


def build_pillar():
    clear()
    plaster = material('aged_limestone', (.61, .57, .45), .86, grain='stone')
    trim = material('limestone_molding', (.48, .45, .36), .8, grain='stone', seed=22)
    shaft = box('continuous_shaft', (.266, .266, 2.78), (0, 0, 0), plaster, edge=0)
    # Shallow recesses cut into the shaft, with true inner faces and closed ends.
    for axis in (0, 1):
        for side in (-1, 1):
            for offset in (-.061, .061):
                loc = [offset, offset, 0]
                loc[axis] = side * .134
                cutter = box('groove_tool', (.016, .016, 2.5), loc, None, edge=.003)
                active(shaft)
                mod = shaft.modifiers.new('Recessed fluting', 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = cutter
                bpy.ops.object.modifier_apply(modifier=mod.name)
                bpy.data.objects.remove(cutter, do_unlink=True)
    bevel(shaft, .003, 2)
    for z, w, h in [(-1.46, .32, .08), (-1.402, .304, .036), (-1.369, .283, .03),
                     (1.36, .281, .04), (1.40, .302, .04), (1.46, .32, .08)]:
        box('stepped_molding', (w, w, h), (0, 0, z), trim, edge=.004)
    export('pillar')


def build_light_panel():
    clear()
    paint = material('enamel_housing', (.68, .67, .60), .54, .18, grain='paint')
    reflector = material('brushed_reflector', (.57, .61, .62), .3, .72, grain='brushed')
    ceramic = material('tube_sockets', (.30, .29, .25), .76)
    diffuser = material('diffuser', (1., .91, .72), .26, emission=1.4)
    screws = material('fasteners', (.19, .21, .22), .34, .85)
    # A hollow tray: no solid housing behind the visible light-emitting surface.
    box('backplate', (1.3, 3.3, .015), (0, 0, .0325), paint)
    for x in (-.629, .629):
        box('long_rim', (.042, 3.3, .08), (x, 0, 0), paint)
    for y in (-1.629, 1.629):
        box('end_rim', (1.23, .042, .08), (0, y, 0), paint)
    box('reflector_tray', (1.19, 3.18, .008), (0, 0, .02), reflector, edge=.002)
    for x in (-.29, .29):
        cylinder('fluorescent_tube', .023, 2.98, (x, 0, -.01), diffuser,
                 vertices=32, rotation=(math.pi / 2, 0, 0), edge=.002)
        for y in (-1.51, 1.51):
            box('ceramic_socket', (.085, .065, .056), (x, y, -.004), ceramic)
            cylinder('tube_endcap', .026, .065, (x, y * .971, -.01), reflector,
                     vertices=24, rotation=(math.pi / 2, 0, 0), edge=.001)
            for dx in (-.007, .007):
                cylinder('contact_pin', .002, .025, (x + dx, y, -.01), screws, 12,
                         rotation=(math.pi / 2, 0, 0), edge=0)
    for x in (-.49, 0, .49):
        box('long_louver', (.013, 3.15, .025), (x, 0, -.027), reflector, edge=.001)
    for y in (-1.26, -.84, -.42, 0, .42, .84, 1.26):
        box('cross_louver', (1.20, .012, .025), (0, y, -.027), reflector, edge=.001)
    for x in (-.63, .63):
        for y in (-1.51, 1.51):
            screw('fixing_screw', (x, y, -.039), .009, screws, ceramic, 'Z')
    # Ballast cover, folded reflector shoulders and retained service clips.
    box('ballast_cover', (.18, 2.7, .022), (0, 0, .001), paint, edge=.006)
    for x in (-.14, .14, -.44, .44):
        box('folded_reflector', (.14, 3.03, .007), (x, 0, .003), reflector,
            rotation=(0, math.copysign(.16, x), 0), edge=.001)
    for y in (-1.35, 1.35):
        box('service_clip', (.16, .04, .008), (0, y, -.014), screws, edge=.002)
    # Wiring stays above the tubes and is visible between the louvers.
    for x in (-.29, .29):
        rod('socket_lead', [(x, -1.54, .014), (x * .7, -1.58, .014), (0, -1.45, .014)], .004, ceramic, 1)
    export('light_panel')


def exit_sign(z, case, face, lettering, width=.5):
    box('sign_case', (width + .036, .04, .17), (0, -.067, z), case, edge=.009)
    box('sign_face', (width, .004, .134), (0, -.09, z), face, edge=.002)
    text('exit_lettering', 'EXIT', (0, -.094, z - .038), .105, lettering)


def build_exit_door():
    clear()
    oak = material('stained_walnut', (.32, .175, .087), .58, grain='wood')
    panel = material('walnut_panels', (.38, .22, .115), .57, grain='wood', seed=3)
    recess = material('panel_recesses', (.12, .067, .032), .82)
    brass = material('antique_brass', (.57, .39, .14), .34, .78, grain='bronze')
    black = material('door_seal', (.024, .028, .024), .92)
    green = material('exit_green', (.014, .15, .076), .5, emission=.6)
    white = material('exit_letters', (.73, 1., .84), .4, emission=1.2)
    box('door_seal', (1.83, .072, 2.3), (0, .013, 1.15), black, edge=.002)
    box('door_leaf', (1.78, .058, 2.28), (0, -.008, 1.15), oak, edge=.006)
    for x in (-.946, .946):
        box('jamb', (.108, .15, 2.32), (x, 0, 1.16), oak, edge=.009)
        box('jamb_reveal', (.026, .014, 2.31), (x - math.copysign(.031, x), -.081, 1.155), panel)
    box('header', (2., .15, .1), (0, 0, 2.35), oak, edge=.008)
    box('threshold', (1.8, .16, .018), (0, 0, .009), brass, edge=.002)
    for x in (-.435, .435):
        for z, h in ((.57, .75), (1.505, .89)):
            box('shadow_recess', (.71, .012, h), (x, -.041, z), recess)
            profile_frame('ogee_panel_molding', .70, h, (x, -.047, z),
                          [(0, 0), (.008, .007), (.015, .011), (.023, .008), (.032, -.003),
                           (.038, -.004), (.045, .004), (.054, .010), (.063, .012), (.07, .006)], oak)
            box('inset_field', (.56, .013, h - .14), (x, -.052, z), panel, edge=.004)
            # Thin brass stringing sits in the molding rather than floating above it.
            profile_frame('panel_inlay', .70 - .116, h - .116, (x, -.0594, z), [(0, 0), (.0018, 0)], brass)
    # Functional hardware: hinges, escutcheon, keyhole and a curved lever.
    for z in (.34, 1.15, 2.0):
        box('hinge_leaf', (.071, .01, .11), (-.872, -.047, z), brass, edge=.002)
        cylinder('hinge_barrel', .012, .12, (-.894, -.05, z), brass, vertices=20)
        for dz in (-.04, 0, .04):
            cylinder('hinge_knuckle', .014, .007, (-.894, -.05, z + dz), brass, 16, edge=.001)
        for dz in (-.033, .033):
            screw('hinge_screw', (-.857, -.053, z + dz), .0045, brass, black)
    box('escutcheon', (.067, .012, .205), (.745, -.048, 1.065), brass, edge=.014)
    for z in (.986, 1.148):
        screw('escutcheon_screw', (.745, -.055, z), .004, brass, black)
    cylinder('lever_spindle', .02, .055, (.745, -.08, 1.125), brass, rotation=(math.pi / 2, 0, 0))
    rod('lever_handle', [(.745, -.108, 1.125), (.71, -.132, 1.125), (.59, -.132, 1.125), (.57, -.125, 1.125)], .012, brass)
    cylinder('keyhole', .008, .004, (.745, -.057, 1.02), black, vertices=16, rotation=(math.pi / 2, 0, 0), edge=0)
    box('kick_plate', (1.65, .007, .115), (0, -.043, .088), brass, edge=.003)
    for x in (-.79, -.26, .26, .79):
        for z in (.044, .133):
            screw('kickplate_screw', (x, -.047, z), .0035, brass, black)
    # Tiered architrave and narrow carved beadwork give the frame real depth.
    for x in (-.967, .967):
        box('architrave_bead', (.022, .022, 2.28), (x, -.081, 1.16), panel, edge=.008)
    box('header_crown', (1.98, .026, .022), (0, -.082, 2.375), panel, edge=.007)
    exit_sign(2.155, brass, green, white, .48)
    export('exit_door')


def build_industrial_door():
    clear()
    steel = material('powder_coated_steel', (.26, .33, .34), .64, .18, grain='paint')
    frame = material('dark_steel_frame', (.11, .145, .15), .52, .55)
    inset = material('panel_shadow', (.048, .065, .064), .75)
    metal = material('brushed_stainless', (.50, .54, .55), .32, .8, grain='brushed')
    yellow = material('safety_ochre', (.83, .55, .065), .7)
    black = material('hazard_black', (.024, .03, .027), .82)
    glass = material('wired_glass', (.37, .50, .45), .19, .0)
    glass_bsdf = next(n for n in glass.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    glass_bsdf.inputs['Transmission Weight'].default_value = .82
    glass_bsdf.inputs['IOR'].default_value = 1.46
    green = material('exit_green', (.014, .15, .076), .5, emission=.6)
    white = material('exit_letters', (.73, 1., .84), .4, emission=1.2)
    for x in (-.944, .944):
        box('steel_jamb', (.112, .14, 2.30), (x, 0, 1.15), frame, edge=.006)
    box('steel_header', (2., .14, .10), (0, 0, 2.35), frame)
    box('threshold', (1.8, .17, .02), (0, 0, .01), metal)
    for side in (-1, 1):
        x = side * .448
        if side < 0:
            box('left_leaf', (.876, .064, 2.27), (x, .005, 1.145), steel, edge=.006)
        else:
            # The observation window is an actual opening, not glass over steel.
            for size, pos in [((.876, .064, 1.28), (x, .005, .65)),
                              ((.876, .064, .425), (x, .005, 2.0675)),
                              ((.248, .064, .565), (x - .314, .005, 1.5725)),
                              ((.248, .064, .565), (x + .314, .005, 1.5725))]:
                box('window_leaf', size, pos, steel, edge=.003)
            box('glazing', (.38, .014, .565), (x, .005, 1.5725), glass, edge=.001)
            for dx in (-.208, .208):
                box('window_frame_side', (.034, .028, .62), (x + dx, -.04, 1.5725), metal)
            for dz in (-.293, .293):
                box('window_frame_top', (.445, .028, .034), (x, -.04, 1.5725 + dz), metal)
            for dx in (-.13, 0, .13):
                rod('glass_wire', [(x + dx, -.006, 1.30), (x + dx, -.006, 1.84)], .0015, metal, 0)
            for z in (1.38, 1.52, 1.66, 1.8):
                rod('glass_wire', [(x - .187, -.006, z), (x + .187, -.006, z)], .0015, metal, 0)
        box('kickplate', (.82, .012, .32), (x, -.035, .25), metal, edge=.004)
        box('hazard_strip', (.82, .005, .09), (x, -.044, .07), yellow, edge=0)
        # Clip diagonal stripes to their rectangular band.
        for k in range(6):
            start = -.41 + k * .14
            verts = [(x + start, -.047, .025), (x + min(start + .062, .41), -.047, .025),
                     (x + min(start + .117, .41), -.047, .115), (x + min(start + .055, .41), -.047, .115)]
            mesh('clipped_hazard', verts, [(0, 1, 2, 3)], black)
        for dx in (-.37, .37):
            for z in (.15, .35, 2.17):
                screw('flush_bolt', (x + dx, -.046, z), .009, metal, black)
        for dx in (-.29, .29):
            box('panic_bar_bracket', (.065, .065, .07), (x + dx, -.06, 1.04), frame)
        box('panic_bar', (.68, .04, .06), (x, -.105, 1.04), metal, edge=.013)
        for z in (.35, 1.15, 2.02):
            cylinder('hinge_pin', .012, .13, (side * .882, -.042, z), metal, vertices=16)
            for dz in (-.047, 0, .047):
                cylinder('hinge_knuckle', .0145, .027, (side * .882, -.042, z + dz), metal, 16, edge=.001)
        # Recessed stamped perimeter, closer body and articulated return arm.
        profile_frame('pressed_leaf_seam', .83, 2.21, (x, -.028, 1.145),
                      [(0, 0), (.007, .003), (.012, .003), (.018, 0)], frame)
        box('door_closer', (.26, .065, .075), (x, -.070, 2.00), metal, edge=.015)
        rod('closer_arm', [(x + .10, -.105, 2.0), (x - .08, -.15, 2.07),
                           (x - .21, -.075, 2.21)], .009, frame, 1)
        for dx in (-.09, .09):
            screw('closer_mount', (x + dx, -.105, 2.0), .005, metal, black)
        for dx in (-.27, .27):
            screw('panicbar_mount', (x + dx, -.13, 1.04), .004, metal, black)
    box('vent_recess', (.51, .008, .32), (-.448, -.032, 1.63), inset)
    for z in (1.51, 1.56, 1.61, 1.66, 1.71, 1.76):
        box('angled_vent_louver', (.48, .025, .036), (-.448, -.046, z), steel, rotation=(.28, 0, 0), edge=.002)
    box('service_plate', (.18, .005, .068), (-.64, -.032, .61), frame, edge=.002)
    text('service_stamp', 'BR / 014', (-.64, -.036, .601), .022, metal)
    text('push_instruction', 'PUSH TO OPEN', (0, -.036, .81), .05, metal)
    exit_sign(2.16, frame, green, white)
    export('door_industrial')


def build_almond_water():
    clear()
    glass = material('bottle_glass', (.78, .91, .85), .075)
    glass_bsdf = next(n for n in glass.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    glass_bsdf.inputs['Transmission Weight'].default_value = 1
    glass_bsdf.inputs['IOR'].default_value = 1.46
    liquid = material('almond_water', (.64, .71, .52), .13)
    liquid_bsdf = next(n for n in liquid.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    liquid_bsdf.inputs['Transmission Weight'].default_value = .7
    liquid_bsdf.inputs['IOR'].default_value = 1.333
    cap = material('navy_cap', (.023, .07, .082), .42, grain='paint')
    paper = material('uncoated_label', (.89, .85, .72), .9, grain='paper')
    label_image = bpy.data.images.load(str(Path(__file__).resolve().parent / 'textures' / 'almond_label.png'))
    label_node = paper.node_tree.nodes.new('ShaderNodeTexImage')
    label_node.image = label_image
    label_bsdf = next(n for n in paper.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    paper.node_tree.links.new(label_node.outputs['Color'], label_bsdf.inputs['Base Color'])
    navy = material('label_ink', (.018, .061, .067), .94)
    gold = material('label_rules', (.59, .40, .13), .72)
    # A closed, smoothly revolved bottle with a heel, rounded shoulder and neck.
    profile = [(0, .008), (.075, .008), (.10, 0), (.132, .004), (.145, .018), (.15, .039), (.15, .47),
               (.149, .495), (.145, .522), (.136, .55), (.122, .577), (.105, .598),
               (.085, .62), (.065, .645), (.058, .666), (.057, .715), (.053, .715),
               (.052, .665), (.06, .642), (.08, .617), (.10, .594), (.116, .57),
               (.130, .546), (.139, .520), (.143, .49), (.144, .043), (.131, .024), (0, .024)]
    lathe('glass_bottle', profile, glass, 80)
    lathe('liquid_fill', [(0, .018), (.117, .018), (.133, .028), (.138, .046),
                         (.138, .467), (.135, .497), (.12, .526), (.116, .528), (.10, .525), (0, .525)], liquid, 64)
    lathe('paper_label', [(.151, .205), (.151, .48)], paper)
    for z in (.217, .469):
        lathe('printed_navy_band', [(.1515, z), (.1515, z + .008)], navy)
    for z in (.234, .456):
        lathe('printed_gold_rule', [(.1515, z), (.1515, z + .002)], gold)
    # Label graphics use cylindrical UVs so lettering follows the bottle surface.
    lathe('tamper_ring', [(0, .711), (.062, .711), (.065, .716), (.065, .73), (.06, .734), (0, .734)], cap, 48)
    lathe('screw_cap', [(0, .731), (.061, .731), (.065, .737), (.065, .782),
                        (.062, .793), (.052, .8), (0, .8)], cap, 64)
    for j in range(40):
        a = j / 40 * math.tau
        box('cap_knurl', (.003, .003, .041), (.065 * math.cos(a), .065 * math.sin(a), .758), cap,
            rotation=(0, 0, a), edge=.0007)
    # Mold seams, a rolled glass heel and the cap's separated tamper bridges.
    for angle in (0, math.pi):
        rod('mold_seam', [(r * math.cos(angle), r * math.sin(angle), z) for r, z in
                         ((.1504, .065), (.1504, .19), (.1504, .49), (.1364, .55), (.0854, .62), (.0584, .665))],
            .00055, glass, 1)
    lathe('heel_ring', [(.145, .03), (.151, .044), (.151, .049), (.15, .055)], glass, 80)
    for j in range(12):
        a = j / 12 * math.tau
        box('tamper_bridge', (.005, .003, .012), (.064 * math.cos(a), .064 * math.sin(a), .733), cap,
            rotation=(0, 0, a), edge=.0005)
    emblem = [(math.sin(a) * .013, math.cos(a) * .028, .8005) for a in np.linspace(0, math.tau, 25)]
    rod('cap_embossed_emblem', emblem, .0008, gold, 1)
    rod('emblem_vein', [(0, -.019, .8005), (.004, 0, .8005), (0, .019, .8005)], .0006, gold, 1)
    # Source dimensions represent a handheld half-litre bottle. The game uses
    # a modest enlargement for pickup visibility, not an 80 cm bottle.
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.location *= .27
            obj.scale *= .27
    export('almond_water')


def build_pavilion():
    from pavilion_asset import build_pavilion as build
    build()


if __name__ == '__main__':
    selection = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    builders = {'pillar': build_pillar, 'light_panel': build_light_panel, 'exit_door': build_exit_door,
                'door_industrial': build_industrial_door, 'almond_water': build_almond_water, 'pavilion': build_pavilion}
    for name in selection or builders:
        builders[name]()
