"""
FK Chain Controller Generator for Maya
======================================

Builds a clean FK control chain from the selected joints.

- One control per joint, placed with offsetParentMatrix (no offset groups).
- Controls are created without construction history.
- Controls are parented in the same hierarchy as the joints.
- Color by side (RGB): "L_" red, "R_" blue, anything else yellow.
- The joints are driven by constraints (parent constraint on the root,
  orient constraints on the rest).
- Everything runs in a single undo chunk.
- Optional shapes from the mGear icon library (mGear is not required).

Tested with Maya [version] and mGear 5.4.0.
Requires Maya 2020 or newer (offsetParentMatrix).

Usage:
    import fk_chain
    fk_chain.build_fk_chain(shape="gear", radius=2.0, use_mgear=True)
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om

# mGear is optional: the tool also works without it.
try:
    from mgear.core import icon as mgear_icon
    HAS_MGEAR = True
except ImportError:
    mgear_icon = None
    HAS_MGEAR = False

# Shapes available from the mGear icon library.
MGEAR_SHAPES = ("circle", "square", "cube", "diamond", "cross", "sphere", "pyramid",
                "cylinder", "gear", "flower", "arrow", "crossarrow", "compas",
                "cubewithpeak", "axis")

# Built-in shapes (fallback when mGear is not used or not installed).
SHAPES = {
    "square":  [(0, -1, -1), (0, -1, 1), (0, 1, 1), (0, 1, -1), (0, -1, -1)],
    "diamond": [(0, 1, 0), (0, 0, 1), (0, -1, 0), (0, 0, -1), (0, 1, 0)],
    "cross":   [(0, .33, 1), (0, .33, .33), (0, 1, .33), (0, 1, -.33), (0, .33, -.33),
                (0, .33, -1), (0, -.33, -1), (0, -.33, -.33), (0, -1, -.33), (0, -1, .33),
                (0, -.33, .33), (0, -.33, 1), (0, .33, 1)],
    "cube":    [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
                (-1, -1, 1), (1, -1, 1), (1, -1, -1), (-1, -1, -1), (1, -1, -1), (1, 1, -1),
                (1, 1, 1), (1, -1, 1), (-1, -1, 1), (-1, 1, 1)],
}


def normalize_shape(ctrl, radius):
    """Scale a shape to the requested size and face flat shapes toward the X axis."""
    bb = cmds.exactWorldBoundingBox(ctrl)           # xmin, ymin, zmin, xmax, ymax, zmax
    ext = [bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]
    biggest = max(ext)
    if biggest <= 0:
        return
    smallest = ext.index(min(ext))
    if min(ext) < biggest * 0.01:                    # flat shape: align its normal to X
        if smallest == 1:
            cmds.rotate(0, 0, 90, ctrl)
        elif smallest == 2:
            cmds.rotate(0, 90, 0, ctrl)
    s = (2.0 * radius) / biggest
    cmds.scale(s, s, s, ctrl)
    cmds.makeIdentity(ctrl, apply=True, rotate=True, scale=True)


def create_shape(kind, name, radius, use_mgear=False):
    """Create a control shape, from mGear if requested and available."""
    if use_mgear and HAS_MGEAR and kind in MGEAR_SHAPES:
        try:
            ctrl = mgear_icon.create(None, name, icon=kind).split("|")[-1]
            normalize_shape(ctrl, radius)
            return ctrl
        except Exception as err:
            cmds.warning("mGear: shape '%s' not created (%s), using fallback." % (kind, err))
    if kind == "circle":
        return cmds.circle(name=name, normal=(1, 0, 0), radius=radius,
                           constructionHistory=False)[0]
    if kind not in SHAPES:
        raise ValueError("Unknown shape: " + kind)
    points = [(x * radius, y * radius, z * radius) for x, y, z in SHAPES[kind]]
    return cmds.curve(name=name, degree=1, point=points)


def side_color(name):
    """RGB color from the side prefix: L_ red, R_ blue, otherwise yellow."""
    if name.startswith("L_"):
        return (1.0, 0.1, 0.1)
    if name.startswith("R_"):
        return (0.1, 0.3, 1.0)
    return (1.0, 0.9, 0.1)


def set_color(ctrl, rgb):
    for shape in cmds.listRelatives(ctrl, shapes=True) or []:
        cmds.setAttr(shape + ".overrideEnabled", 1)
        cmds.setAttr(shape + ".overrideRGBColors", 1)
        cmds.setAttr(shape + ".overrideColorRGB", rgb[0], rgb[1], rgb[2])


def world_matrix(node):
    return om.MMatrix(cmds.xform(node, query=True, matrix=True, worldSpace=True))


def make_ctrl(joint, parent_ctrl=None, shape="circle", radius=1.0, use_mgear=False):
    """Create one control for a joint, placed with offsetParentMatrix."""
    base = joint.split("|")[-1]
    if base.endswith("_jnt"):
        base = base[:-4]
    ctrl = create_shape(shape, base + "_ctrl", radius, use_mgear)

    if parent_ctrl:
        ctrl = cmds.parent(ctrl, parent_ctrl, relative=True)[0]
        parent_world = om.MMatrix(cmds.getAttr(parent_ctrl + ".worldMatrix[0]"))
        offset = world_matrix(joint) * parent_world.inverse()
    else:
        offset = world_matrix(joint)

    cmds.setAttr(ctrl + ".offsetParentMatrix", list(offset), type="matrix")
    set_color(ctrl, side_color(base))
    return ctrl


def build_fk_chain(shape="circle", radius=1.0, use_mgear=False):
    """Build an FK control chain from the selected joints (parent to child)."""
    sel = cmds.ls(selection=True, type="joint", long=True)
    if not sel:
        cmds.warning("Select joints first.")
        return
    joints = sorted(sel, key=lambda j: j.count("|"))     # parents first
    cmds.undoInfo(openChunk=True)
    try:
        previous = None
        for i, j in enumerate(joints):
            ctrl = make_ctrl(j, previous, shape, radius, use_mgear)
            if i == 0:
                cmds.parentConstraint(ctrl, j, maintainOffset=True)
            else:
                cmds.orientConstraint(ctrl, j, maintainOffset=True)
            previous = ctrl
    finally:
        cmds.undoInfo(closeChunk=True)


if __name__ == "__main__":
    build_fk_chain(shape="circle", radius=1.0)
