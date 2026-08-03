#!/usr/bin/env python3
"""Parametric enclosure for the ELP-USB48MP01-AF70 camera module.

    bash setup/tools.sh case        # writes hardware/stl/*.stl

Why this exists: the ELP 48 MP autofocus module is a bare, double-deck PCB
sandwich that gets noticeably warm and has its lens sitting on a tiny
autofocus block in the middle. The ready-made ELP cases on Thingiverse /
Printables are all for the older single-deck boards with an M12 lens barrel
and do not fit. This one is built for an exhibit: vented on all six sides,
tripod-mountable, and printable without support.

── How the board is held ────────────────────────────────────────────────
The one number the manufacturer does NOT publish is the mounting-hole
pattern, so the case deliberately ignores it. The PCB is captured like a
pane of glass instead:

    front wall ─ 4 corner pads ─ [PCB stack] ─ pressure boss ─ back plate

The cavity walls locate it in X/Y, four corner pads stop it at the front
(they land on the board's own corner screw heads, which is fine), and the
back plate's boss presses it home. Stack height varies between production
runs, so shim.stl (1 mm) takes up the slack — print as many as needed.

All dimensions in millimetres. Change PARAMS and re-run.
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
    stack_h=13.0,        # front of top PCB to back of bottom PCB
    lens_offset=8.0,     # corner pads: how far the PCB sits behind the wall

    # -- the shell -------------------------------------------------------
    outer=50.0,          # outer edge length
    corner_r=5.0,        # outer corner radius
    front_wall=2.6,      # thickness of the face the lens looks through
    depth=28.0,          # front face to back rim
    plate_h=3.0,         # back plate thickness
    boss_h=2.4,          # how far the back plate reaches into the cavity

    # -- lens opening (HFOV 70 deg / DFOV 82 deg -> flare it generously) --
    lens_in=14.0,        # diameter at the inside of the front wall
    lens_out=19.0,       # diameter at the outside (45 deg cone, no support)

    # -- fasteners -------------------------------------------------------
    post_d=5.0,          # screw column diameter
    pilot_d=2.5,         # pilot bore for M3 self-tapping screws
    screw_free=3.4,      # clearance hole in the back plate
    head_d=6.2,          # counterbore so the head sits flush
    head_h=1.8,

    # -- tripod pedestal (1/4"-20 hex nut, 11.1 across flats, 5.6 thick) --
    ped_w=18.0,          # width across the case
    ped_out=9.0,         # how far it sticks out below
    ped_z0=7.0,          # start along the optical axis
    ped_len=15.0,
    nut_af=11.3,         # across flats + fit
    nut_h=6.0,
    nut_inset=2.5,       # wall left below the nut (thin = more thread bite)
    tripod_d=7.0,        # clearance for the 1/4" screw

    # -- ventilation -----------------------------------------------------
    # Every wall carries four slots. They are wide enough for the 4-pin plug
    # to pass lengthwise, so the cable can leave on whichever side ELP put
    # the socket — and they keep a warm module cool.
    vent_w=6.5,          # slot width across the wall
    vent_len=15.0,       # slot length along the optical axis
    vent_at=(6.2, 13.4), # distance from the wall centre (the screw column)
)

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


def cut(a, *bs):
    return trimesh.boolean.difference([a, trimesh.util.concatenate(list(bs))])


def add(a, *bs):
    return trimesh.boolean.union([a, trimesh.util.concatenate(list(bs))])


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
    """The screws bite into the middle of each of the four walls — the one
    stretch the ventilation slots leave solid."""
    m = (P["board"] + 2 * P["board_fit"]) / 2 + (
        P["outer"] / 2 - (P["board"] + 2 * P["board_fit"]) / 2) / 2
    return [(0, m), (0, -m), (m, 0), (-m, 0)]


def _vent_cuts(cavity):
    """Slots through all four walls, clear of the screws (wall centre) and
    of the corners. Each cutter stops at the cavity: one that reached all
    the way through would also shave the corner pads on the far side."""
    z_mid = P["front_wall"] + (P["depth"] - P["front_wall"]) / 2
    t = P["outer"] / 2 - cavity / 2 + 2.0   # wall thickness plus a little
    mid = (P["outer"] / 2 + cavity / 2) / 2  # centre of the wall
    cuts = []
    for wall in (-1, 1):
        for a in P["vent_at"]:
            for s in (-1, 1):
                cuts.append(slab(P["vent_w"], t, P["vent_len"],
                                 x=s * a, y=wall * mid, z=z_mid))
                cuts.append(slab(t, P["vent_w"], P["vent_len"],
                                 x=wall * mid, y=s * a, z=z_mid))
    return cuts


def build_body():
    cavity = P["board"] + 2 * P["board_fit"]
    d, fw = P["depth"], P["front_wall"]

    shell = rrect(P["outer"], P["outer"], d, P["corner_r"])

    # hollow it out from the back
    shell = cut(shell, rrect(cavity, cavity, d - fw + EPS, 1.0, z0=fw))

    # lens opening: cone flaring outwards, printable at 45 deg
    shell = cut(shell, cone(P["lens_out"], P["lens_in"], -EPS, fw + EPS))

    # Four L-shaped corner pads: the front stop for the board. They reach
    # 0.4 mm into the wall so the union has no coplanar faces to trip over.
    pads = []
    pw, pl, bite = 3.2, 9.0, 0.4
    e = cavity / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            z = fw + P["lens_offset"] / 2
            pads.append(slab(pl + bite, pw + bite, P["lens_offset"],
                             x=sx * (e - (pl - bite) / 2),
                             y=sy * (e - (pw - bite) / 2), z=z))
            pads.append(slab(pw + bite, pl + bite, P["lens_offset"],
                             x=sx * (e - (pw - bite) / 2),
                             y=sy * (e - (pl - bite) / 2), z=z))
    shell = add(shell, *pads)

    shell = cut(shell, *_vent_cuts(cavity))

    bores = []
    for x, y in _post_centres():
        b = cylinder(radius=P["pilot_d"] / 2, height=16, sections=32)
        b.apply_translation([x, y, d - 16 / 2 + EPS])
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
    zc = P["ped_z0"] + P["ped_len"] / 2
    y_face = y0 - P["ped_out"]

    screw = cylinder(radius=P["tripod_d"] / 2, height=P["ped_out"] + 6,
                     sections=48)
    screw.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2, [1, 0, 0]))
    screw.apply_translation([0, y_face + (P["ped_out"] + 6) / 2 - 3, zc])

    y_nut = y_face + P["nut_inset"] + P["nut_h"] / 2
    nut = hexprism(P["nut_af"], P["nut_h"])
    nut.apply_translation([0, y_nut, zc])
    # slide-in slot for the nut, opening towards the back of the case
    slot = slab(P["nut_af"], P["nut_h"], P["ped_len"],
                x=0, y=y_nut, z=zc + P["ped_len"] / 2)
    return [screw, nut, slot]


def build_back():
    """Vented back plate. Its boss is a rim, not a slab: it presses on the
    outer 3 mm of the PCB only, so nothing lands on the components or the
    USB socket in the middle of the lower board."""
    cavity = P["board"] + 2 * P["board_fit"]
    plate = rrect(P["outer"], P["outer"], P["plate_h"], P["corner_r"])
    rim = cut(rrect(cavity - 0.4, cavity - 0.4, P["boss_h"] + EPS, 1.0,
                    z0=-P["boss_h"]),
              rrect(cavity - 7.0, cavity - 7.0, P["boss_h"] * 3, 1.0,
                    z0=-P["boss_h"] * 2))
    plate = add(plate, rim)

    cuts = []
    for i in (-1, 0, 1):                    # let the warm air out
        cuts.append(slab(5.0, 26.0, 20, x=i * 8.0, y=0, z=0))
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


# ── Entry point ─────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)
    parts = {
        "elp48-case-body": build_body,
        "elp48-case-back": build_back,
        "elp48-case-shim": build_shim,
    }
    ok = True
    for name, fn in parts.items():
        mesh = tidy(fn())
        path = os.path.join(OUT, name + ".stl")
        mesh.export(path)
        check = trimesh.load(path)          # verify what actually hit the disk
        size = check.bounds[1] - check.bounds[0]
        ok &= bool(check.is_watertight)
        print(f"  {name}.stl  {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm"
              f"   watertight={check.is_watertight}"
              f"   {check.volume / 1000:.1f} cm3")
    print(f"\n→ {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
