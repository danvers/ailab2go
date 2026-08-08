#!/usr/bin/env python3
"""Parametric enclosure for the ELP-USB48MP01-AF70 camera module.

    bash setup/tools.sh case        # writes hardware/stl/*.stl

Why this exists: the ELP 48 MP autofocus module is a bare, double-deck PCB
sandwich that gets noticeably warm and has its lens sitting on a tiny
autofocus block in the middle. The ready-made ELP cases on Thingiverse /
Printables are all for the older single-deck boards with an M12 lens barrel
and do not fit. This one is built for an exhibit: vented on all six sides,
tripod-mountable, and printable without support.

── How the module is held ──────────────────────────────────────────────
The one number the manufacturer does NOT publish is the mounting-hole
pattern, so the case deliberately ignores it. The module is captured like
a pane of glass instead:

    front wall ─ 4 corner pads ─ [PCB stack + stands + cooler] ─ press
    bars ─ back plate

The cavity walls locate it in X/Y, four corner pads stop it at the front
(they land on the board's own corner screw heads, which is fine), and the
back plate's press bars push on the COOLER PLATE, which passes the force
through its stands into the boards. Stack heights are field-measured and
vary, so shim.stl takes up the slack — print as many as needed.

Rev 2, after measuring the real module (thanks Dan):
  * the module carries a passive cooler on 12 mm stands (plate 4 mm) —
    the case is deeper and the back is a fin grid so the cooler breathes;
  * the 4-pin plug leaves the stack at the BOTTOM CENTRE towards the back
    — the back plate has a notch and the lower press bar is split so plug
    and cable pass;
  * walls carry fin arrays (chamfered ribs) instead of three slots: more
    cooling edge, less material, nicer to look at.

All dimensions in millimetres. Change PARAMS, re-run, and READ THE FIT
TABLE it prints — it shows where every part of the stack ends up and
flags collisions before you print.
"""

import os
import sys

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

# ── Parameters ──────────────────────────────────────────────────────────
P = dict(
    # -- the module (ELP datasheet: "Double-deck, 38mm x 38mm") ----------
    board=38.0,          # PCB edge length
    board_fit=0.4,       # clearance per side, so the cavity is 38.8
    stack_h=6.0,         # PCB sandwich: front of top PCB to back of rear PCB
    lens_offset=6.0,     # corner pads: how far the PCB sits behind the wall

    # -- cooler on stands (field-measured on the real module) ------------
    stand_h=12.0,        # rear PCB to cooler plate
    cooler_h=4.0,        # cooler plate thickness
    cooler_w=38.0,       # cooler edge length (assumed = board; shrink ok)
    press_gap=1.0,       # air between cooler back and the press bars
                         # before shims — one shim closes it

    # -- 4-pin plug, bottom centre, pointing backwards -------------------
    plug_w=10.0,         # plug housing width  (measured)
    plug_h=5.0,          # plug housing height (measured)
    plug_clear=2.0,      # clearance per side around it
    plug_lift=1.0,       # bottom of plug above the board's bottom edge

    # -- the shell -------------------------------------------------------
    outer=50.0,          # outer edge length
    corner_r=4.0,        # outer corner radius
    pad=5.5,             # corner rest pads: edge length of each square
    front_wall=2.6,      # thickness of the face the lens looks through
    chamfer=1.2,         # bevel on the outer front and back edges
    plate_h=3.0,         # back plate thickness

    # -- lens opening (HFOV 70 deg / DFOV 82 deg -> flare it generously) --
    lens_in=14.0,        # diameter at the inside of the front wall
    lens_out=19.0,       # diameter at the outside (45 deg cone, no support)

    # -- fasteners -------------------------------------------------------
    screw_at=21.5,       # X and Y of the four corner screws
    pilot_d=2.5,         # pilot bore for M3 self-tapping screws
    screw_free=3.4,      # clearance hole in the back plate
    head_d=6.2,          # counterbore so the head sits flush
    head_h=1.8,

    # -- tripod pedestal (1/4"-20 hex nut, 11.1 across flats, 5.6 thick) --
    ped_w=18.0,          # width across the case
    ped_out=9.0,         # how far it sticks out below
    # The pedestal runs nearly the full depth for a reason: its leading edge
    # is chamfered 45 deg so it prints without support, and that chamfer
    # climbs 9 mm — as long as the pedestal sticks out. A short pedestal
    # would have the chamfer cutting straight through the nut seat.
    ped_z0=2.5,          # start along the optical axis
    ped_len=25.0,
    nut_af=11.3,         # across flats + fit
    nut_h=6.0,
    nut_inset=2.5,       # wall left below the nut (thin = more thread bite)
    nut_z=18.5,          # seat centre, clear of the chamfer and the rim
    tripod_d=7.0,        # clearance for the 1/4" screw

    # -- ventilation: fin arrays -----------------------------------------
    # Every wall carries a row of slots; the material left between them is
    # the cooling ribs. Both slot openings are flared (45 deg), which gives
    # every rib a chamfered edge — more surface, no sharp corners, and the
    # flare prints support-free in the face-down orientation.
    fin_slots=5,         # slots per wall (ribs between = fin_slots - 1)
    # Geometry constraint: slot_w + 2*flare must stay below the pitch
    # (fin_span / fin_slots = 6.4), or neighbouring flares intersect and
    # the ribs taper to knife edges instead of keeping a flat crown.
    fin_slot_w=3.4,      # slot width at the inner wall
    fin_flare=0.9,       # each opening widens by this much at the skin
                         # -> 5.2 outer opening, 1.2 flat rib crown
    fin_span=32.0,       # the row's total width along the wall
    fin_z0=5.0,          # slot start behind the front face
    fin_margin=3.6,      # solid rim kept before the back edge

    # -- back plate press bars (push on the cooler, not the PCB) ---------
    bar_w=3.4,           # bar thickness in Y
    bar_seg=12.0,        # length of the two lower segments (plug passes
                         # between them, exactly like Dan's hand-cut plate)
)

# Everything sits on the optical axis, so the case depth is not a guess but
# the sum of the stack — change any layer above and the case follows:
#   front wall + lens block + PCBs + stands + cooler + press gap
P["depth"] = (P["front_wall"] + P["lens_offset"] + P["stack_h"]
              + P["stand_h"] + P["cooler_h"] + P["press_gap"])

EPS = 0.01
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")


# ── Small geometry helpers ──────────────────────────────────────────────

def rrect(w, h, d, r, z0=0.0):
    """Rounded-rectangle prism, centred in XY, spanning z0..z0+d."""
    r = max(r, 0.001)
    posts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = cylinder(radius=r, height=d, sections=64)
            c.apply_translation([sx * (w / 2 - r), sy * (h / 2 - r), z0 + d / 2])
            posts.append(c)
    return trimesh.util.concatenate(posts).convex_hull


def slab(w, h, d, x=0.0, y=0.0, z=0.0):
    """Axis-aligned box, given by its corner-to-corner size and centre."""
    b = box(extents=[w, h, d])
    b.apply_translation([x, y, z])
    return b


def cone(d0, d1, z0, z1):
    """Truncated cone along Z: diameter d0 at z0 growing to d1 at z1."""
    c = cylinder(radius=1.0, height=1.0, sections=96)
    v = c.vertices.copy()
    t = v[:, 2] + 0.5                       # 0 at the bottom, 1 at the top
    scale = (d0 / 2) * (1 - t) + (d1 / 2) * t
    v[:, 0] *= scale
    v[:, 1] *= scale
    v[:, 2] = z0 + t * (z1 - z0)
    return trimesh.Trimesh(vertices=v, faces=c.faces, process=True)


def hexprism(across_flats, height, axis="y"):
    """Hex prism for a nut trap, centred at the origin."""
    r = across_flats / np.sqrt(3)           # circumradius
    h = cylinder(radius=r, height=height, sections=6)
    if axis == "y":
        h.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi / 2, [1, 0, 0]))
    return h


def _merge(bs):
    """Fuse the tool solids into one. Merely concatenating them is not the
    same thing: where two tools overlap, the leftover inner faces survive
    the boolean as a sealed pocket inside the part — an STL that looks
    watertight and slices into a hollow nobody asked for."""
    bs = list(bs)
    return bs[0] if len(bs) == 1 else trimesh.boolean.union(bs)


def cut(a, *bs):
    return trimesh.boolean.difference([a, _merge(bs)])


def add(a, *bs):
    return trimesh.boolean.union([a, _merge(bs)])


def tidy(mesh):
    """Booleans leave slivers where faces meet exactly. Drop those, weld the
    vertices and close what is left — a slicer that has to guess produces
    stringy walls, and this print has to work on a school's printer."""
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-6))
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    if not mesh.is_watertight:
        mesh.fill_holes()
    trimesh.repair.fix_normals(mesh)
    return mesh


# ── The parts ───────────────────────────────────────────────────────────

def _post_centres():
    """The screws sit on the diagonals, in the solid corners of the shell —
    the walls are wanted for ventilation."""
    a = P["screw_at"]
    return [(a, a), (a, -a), (-a, a), (-a, -a)]


def _flared_slot(w_in, length, z0, wall_t, horizontal, pos, side):
    """One vent slot whose opening widens 45 deg towards the skin: the hull
    of a narrow box at the inner wall face and a wider one at the outer
    face. Cutting with these is what puts the chamfer on every rib."""
    w_out = w_in + 2 * P["fin_flare"]
    zc = z0 + length / 2
    r_in = P["board"] / 2 + P["board_fit"] - 0.5      # just inside the wall
    r_out = P["outer"] / 2 + 1.0                      # just outside the skin
    boxes = []
    for r, w in ((r_in, w_in), (r_out, w_out)):
        if horizontal:
            boxes.append(slab(w, 0.02, length, x=pos, y=side * r, z=zc))
        else:
            boxes.append(slab(0.02, w, length, x=side * r, y=pos, z=zc))
    return trimesh.util.concatenate(boxes).convex_hull


def _fin_cuts():
    """Fin arrays on all four walls: n slots, ribs in between, every edge
    chamfered by the flare. The row stays inside fin_span, clear of the
    corner posts that carry the screws."""
    n, span = P["fin_slots"], P["fin_span"]
    pitch = span / n
    length = P["depth"] - P["fin_z0"] - P["fin_margin"]
    cuts = []
    for i in range(n):
        pos = -span / 2 + pitch * (i + 0.5)
        for side in (-1, 1):
            for horizontal in (True, False):
                cuts.append(_flared_slot(P["fin_slot_w"], length,
                                         P["fin_z0"], 0, horizontal,
                                         pos, side))
    return cuts


def _edge_chamfers(depth):
    """45 deg bevels on the outer front and back edges — the hull of a thin
    full-size slab and a thin inset slab, used as the shell's end caps."""
    c, w, r = P["chamfer"], P["outer"], P["corner_r"]
    def cap(z_small, z_big):
        small = rrect(w - 2 * c, w - 2 * c, 0.02, max(r - c, 0.6), z0=z_small)
        big = rrect(w, w, 0.02, r, z0=z_big)
        return trimesh.util.concatenate([small, big]).convex_hull
    return (cap(0.0, c),                     # front: narrow at the face
            cap(depth - 0.02, depth - c))    # back: narrow at the rim


def build_body():
    cavity = P["board"] + 2 * P["board_fit"]
    d, fw = P["depth"], P["front_wall"]

    # straight prism between two chamfered end caps
    c = P["chamfer"]
    front_cap, back_cap = _edge_chamfers(d)
    shell = add(rrect(P["outer"], P["outer"], d - 2 * c, P["corner_r"], z0=c),
                front_cap, back_cap)

    # Everything hollow is built as one solid and removed in a single pass.
    # Cutting piece by piece leaves coplanar faces where two cuts meet, and
    # those are exactly the slivers that make an STL non-watertight.
    void = rrect(cavity, cavity, d - fw + EPS, 1.0, z0=fw)

    # notch four corner pads back out of the cavity: the board's front stop
    pads, e, s = [], cavity / 2, P["pad"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            pads.append(slab(s, s, P["lens_offset"] + EPS,
                             x=sx * (e - s / 2), y=sy * (e - s / 2),
                             z=fw + P["lens_offset"] / 2))
    void = cut(void, *pads)

    void = add(void,
               cone(P["lens_out"], P["lens_in"], -EPS, fw + EPS),
               *_fin_cuts())
    shell = cut(shell, void)

    bores = []
    for x, y in _post_centres():
        b = cylinder(radius=P["pilot_d"] / 2, height=17, sections=32)
        b.apply_translation([x, y, d - 17 / 2 + EPS])
        bores.append(b)
    shell = cut(shell, *bores)

    shell = add(shell, _pedestal())
    shell = cut(shell, *_pedestal_bores())
    return shell


def _pedestal():
    """Tripod boss under the case. The low-Z end is chamfered so it prints
    without support when the case stands on its face."""
    y0 = -P["outer"] / 2
    w, out = P["ped_w"], P["ped_out"]
    z0, ln = P["ped_z0"], P["ped_len"]

    block = slab(w, out + 4, ln, x=0, y=y0 - out / 2 + 2, z=z0 + ln / 2)
    # 45 deg ramp on the leading edge
    ramp = box(extents=[w, out * 1.6, out * 1.6])
    ramp.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 4, [1, 0, 0]))
    ramp.apply_translation([0, y0 - out, z0])
    return cut(block, ramp)


def _pedestal_bores():
    y0 = -P["outer"] / 2
    zc = P["nut_z"]
    y_face = y0 - P["ped_out"]

    screw = cylinder(radius=P["tripod_d"] / 2, height=P["ped_out"] + 6,
                     sections=48)
    screw.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2, [1, 0, 0]))
    screw.apply_translation([0, y_face + (P["ped_out"] + 6) / 2 - 3, zc])

    y_nut = y_face + P["nut_inset"] + P["nut_h"] / 2
    nut = hexprism(P["nut_af"], P["nut_h"])
    nut.apply_translation([0, y_nut, zc])
    # Slide-in channel, open towards the back of the case. It has to clear
    # the nut ACROSS THE CORNERS (11.3 across flats is 13.05 across corners)
    # or the nut cannot travel down to its seat — measuring the wrong
    # diagonal here is how a nut trap ends up unusable.
    across_corners = P["nut_af"] * 2 / np.sqrt(3)
    slot = slab(across_corners + 0.4, P["nut_h"] + 0.3, P["ped_len"],
                x=0, y=y_nut, z=zc + P["ped_len"] / 2)
    return [screw, nut, slot]


def _plug_notch():
    """Keep-out for the 4-pin plug and its cable: bottom centre, from deep
    inside the case out through the back plate. Kept as one tool so body
    tests, press bars and the plate all honour the same window."""
    w = P["plug_w"] + 2 * P["plug_clear"]
    h = P["plug_h"] + 2 * P["plug_clear"]
    y = -P["board"] / 2 + P["plug_lift"] + h / 2 - P["plug_clear"]
    return slab(w, h, 40, x=0, y=y, z=0), y


def build_back():
    """Back plate, rev 2. Three jobs:
    * a FIN GRID over the cooler instead of a closed lid — same chamfered
      ribs as the walls, so the passive cooler actually convects;
    * PRESS BARS instead of a rim: a full-width bar above, two short
      segments below, pushing on the cooler plate. The gap between the
      lower segments is the plug's doorway (Dan's hand-cut layout);
    * a NOTCH at the bottom so plug and cable leave through the plate."""
    cavity = P["board"] + 2 * P["board_fit"]
    plate = rrect(P["outer"], P["outer"], P["plate_h"], P["corner_r"])

    # press bars, stopping a tenth short of the cooler's nominal back face:
    # the screws close that last bit, shims take production spread — and the
    # collision check below stays a real proof instead of measuring its own
    # deliberate overlap
    reach = P["press_gap"] - 0.1
    bar_y = P["cooler_w"] / 2 - P["bar_w"] / 2 - 1.0
    bars = [slab(P["cooler_w"] - 2.0, P["bar_w"], reach,
                 y=bar_y, z=-reach / 2)]
    for sx in (-1, 1):
        bars.append(slab(P["bar_seg"], P["bar_w"], reach,
                         x=sx * (P["cooler_w"] / 2 - P["bar_seg"] / 2 - 1.0),
                         y=-bar_y, z=-reach / 2))
    plate = add(plate, *bars)

    cuts = []
    # Fin grid over the cooler: flared slots -> chamfered ribs, like the
    # walls. The grid's lower edge stops a BRIDGE above the plug window —
    # without it the two middle ribs would end in mid-air over the notch
    # and the whole grid would hang from its top edge alone.
    notch, notch_y = _plug_notch()
    notch_top = notch_y + (P["plug_h"] + 2 * P["plug_clear"]) / 2
    bridge = 3.0
    grid_top = P["cooler_w"] / 2 - 4.0
    grid_bot = notch_top + bridge
    grid_h = grid_top - grid_bot
    grid_yc = (grid_top + grid_bot) / 2
    n, span = P["fin_slots"], P["cooler_w"] - 6.0
    pitch = span / n
    for i in range(n):
        x = -span / 2 + pitch * (i + 0.5)
        inner = slab(P["fin_slot_w"], grid_h, 0.02, x=x, y=grid_yc, z=-EPS)
        outer = slab(P["fin_slot_w"] + 2 * P["fin_flare"],
                     grid_h + 2 * P["fin_flare"], 0.02,
                     x=x, y=grid_yc, z=P["plate_h"] + EPS)
        cuts.append(trimesh.util.concatenate([inner, outer]).convex_hull)

    cuts.append(notch)

    for x, y in _post_centres():
        free = cylinder(radius=P["screw_free"] / 2, height=20, sections=32)
        free.apply_translation([x, y, 0])
        cuts.append(free)
        head = cylinder(radius=P["head_d"] / 2, height=P["head_h"] * 2,
                        sections=48)
        head.apply_translation([x, y, P["plate_h"]])
        cuts.append(head)
    return cut(plate, *cuts)


def build_shim():
    """1 mm spacer ring — stack it behind the board if it has any play."""
    cavity = P["board"] + 2 * P["board_fit"]
    ring = rrect(cavity - 0.6, cavity - 0.6, 1.0, 1.0)
    return cut(ring, slab(28, 28, 4))


def module_mock():
    """Stand-in of the real module for previews and the collision check:
    PCB sandwich, four corner stands, cooler plate, lens block in front and
    the plug leaving the stack at the bottom, pointing backwards."""
    z0 = P["front_wall"] + P["lens_offset"]
    z1 = z0 + P["stack_h"]
    z2 = z1 + P["stand_h"]
    parts = [slab(P["board"], P["board"], P["stack_h"],
                  z=z0 + P["stack_h"] / 2)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            s = cylinder(radius=2.2, height=P["stand_h"], sections=24)
            s.apply_translation([sx * 15, sy * 15, z1 + P["stand_h"] / 2])
            parts.append(s)
    parts.append(slab(P["cooler_w"], P["cooler_w"], P["cooler_h"],
                      z=z2 + P["cooler_h"] / 2))
    _, plug_y = _plug_notch()
    plug_len = P["stand_h"] + P["cooler_h"] + 5.0
    parts.append(slab(P["plug_w"], P["plug_h"], plug_len,
                      x=0, y=plug_y, z=z1 + plug_len / 2))
    lens = cylinder(radius=4.2, height=P["lens_offset"] + 1.5, sections=48)
    lens.apply_translation([0, 0, z0 - (P["lens_offset"] + 1.5) / 2 + 0.5])
    parts.append(lens)
    return trimesh.util.concatenate(parts)


def fit_report(body, back):
    """The assembly in numbers, then hard proof: the assembled case must
    not intersect the module mock. Eyeballed measurements go in PARAMS;
    this table is where they either add up or get caught."""
    z0 = P["front_wall"] + P["lens_offset"]
    z1, d = z0 + P["stack_h"], P["depth"]
    z2 = z1 + P["stand_h"]
    z3 = z2 + P["cooler_h"]
    print("\n  fit table (mm along the optical axis, 0 = front face)")
    for name, a, b in (("front wall", 0, P["front_wall"]),
                       ("lens block / corner pads", P["front_wall"], z0),
                       ("PCB sandwich", z0, z1),
                       ("cooler stands", z1, z2),
                       ("cooler plate", z2, z3),
                       ("press gap (add shims here)", z3, d),
                       ("back plate", d, d + P["plate_h"])):
        print(f"    {a:5.1f} … {b:5.1f}   {name}")
    ok = True
    assembled = back.copy()
    assembled.apply_translation([0, 0, d])
    mock = module_mock()
    for name, part in (("body", body), ("back plate", assembled)):
        inter = trimesh.boolean.intersection([part, mock])
        vol = 0.0 if inter is None or inter.is_empty else abs(inter.volume)
        flag = "  <- COLLISION, do not print" if vol > 1.0 else "  ok"
        print(f"    module vs {name}: overlap {vol:6.2f} mm3{flag}")
        ok &= vol <= 1.0
    return ok


# ── Preview renderer ────────────────────────────────────────────────────

def render(scene, path, elev=22.0, azim=-55.0, zoom=1.02):
    """Flat-shaded preview: painter's algorithm plus a single light. Enough
    to see whether the thing looks right before anyone spends four hours of
    filament on it."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb

    e, a = np.radians(elev), np.radians(azim)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    cam_up = np.cross(right, fwd)
    light = fwd * 0.55 + cam_up * 0.5 + right * 0.35
    light /= np.linalg.norm(light)

    polys, colours, depths = [], [], []
    for mesh, colour in scene:
        # sorting by centroid only works if no triangle is huge
        mesh = mesh.subdivide_to_size(max_edge=2.5)
        tri = mesh.vertices[mesh.faces]
        normals = mesh.face_normals
        facing = normals @ fwd
        keep = facing > 0                    # cull the far side
        tri, normals = tri[keep], normals[keep]
        shade = np.clip(normals @ light, 0, 1) * 0.72 + 0.28
        base = np.array(to_rgb(colour))
        polys.extend(np.stack([tri @ right, tri @ cam_up], axis=-1))
        colours.extend(np.clip(base * shade[:, None], 0, 1))
        depths.extend((tri @ fwd).mean(axis=1))

    order = np.argsort(depths)
    shown = [colours[i] for i in order]
    fig, ax = plt.subplots(figsize=(7, 7))
    # Each triangle is outlined in its own colour: without that, the
    # antialiased seams between triangles let the geometry behind show
    # through and the case looks like frosted glass.
    ax.add_collection(PolyCollection(
        [polys[i] for i in order], facecolors=shown, edgecolors=shown,
        linewidths=0.4, antialiased=True))
    pts = np.concatenate(polys)
    ctr, span = pts.mean(axis=0), np.ptp(pts, axis=0).max() / 2 * zoom
    ax.set_xlim(ctr[0] - span, ctr[0] + span)
    ax.set_ylim(ctr[1] - span, ctr[1] + span)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)


def previews(body, back, shim):
    """Three views, one of them exploded with a stand-in for the module.
    Everything is tipped upright first, so the pictures show the camera the
    way it stands on a tripod rather than lying on its back."""
    shell, plate, pcb = "#7fb2d9", "#e2a862", "#39424d"
    mock = module_mock()

    seated = back.copy()
    seated.apply_translation([0, 0, P["depth"]])
    apart = back.copy()
    apart.apply_translation([0, 0, P["depth"] + 18])

    upright = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])

    def view(scene, name, elev, azim):
        tipped = []
        for mesh, colour in scene:
            m = mesh.copy()
            m.apply_transform(upright)
            tipped.append((m, colour))
        render(tipped, os.path.join(OUT, name), elev=elev, azim=azim)

    # after the rotation the lens looks towards +Y, so the camera goes there
    view([(body, shell), (seated, plate)], "preview-front.png", 18, 62)
    view([(body, shell), (seated, plate)], "preview-back.png", 16, -118)
    view([(body, shell), (mock, pcb), (apart, plate)],
         "preview-exploded.png", 14, -115)
    print("  preview-front.png, preview-back.png, preview-exploded.png")


# ── Entry point ─────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)
    parts = {
        "elp48-case-body": build_body,
        "elp48-case-back": build_back,
        "elp48-case-shim": build_shim,
    }
    ok, built = True, {}
    for name, fn in parts.items():
        mesh = tidy(fn())
        path = os.path.join(OUT, name + ".stl")
        mesh.export(path)
        check = trimesh.load(path)          # verify what actually hit the disk
        size = check.bounds[1] - check.bounds[0]
        ok &= bool(check.is_watertight)
        built[name] = check
        print(f"  {name}.stl  {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm"
              f"   watertight={check.is_watertight}"
              f"   {check.volume / 1000:.1f} cm3")

    ok &= fit_report(built["elp48-case-body"], built["elp48-case-back"])

    try:
        previews(built["elp48-case-body"], built["elp48-case-back"],
                 built["elp48-case-shim"])
    except ImportError:
        print("  (no matplotlib — skipping the preview images)")

    print(f"\n→ {OUT}")
    if not ok:
        print("!! a check failed above (watertightness or fit) — "
              "do not print yet")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
