# FK Chain Controller Generator for Maya

A small Python tool that builds a clean FK control chain from selected joints in Maya, with optional shapes from the mGear icon library.

![Result](docs/result.png)

## What it does

- Creates one control per selected joint, matched to the joint's position and orientation.
- Uses `offsetParentMatrix` instead of offset groups, so every control stays at zero in the Channel Box.
- Creates curves without construction history (no `makeNurbCircle` nodes left in the scene).
- Parents the controls in the same hierarchy as the joints.
- Colors each control by side, in RGB: `L_` red, `R_` blue, anything else yellow.
- Drives the joints with constraints (parent constraint on the root, orient constraints on the rest).
- Runs in a single undo chunk: one Ctrl+Z reverts the whole chain.
- Offers a choice of control shapes, built in or taken from mGear.

## Requirements

- Autodesk Maya [version tested] or newer (`offsetParentMatrix` requires Maya 2020+).
- mGear is **optional**. The tool was tested with mGear 5.4.0; without it, the built-in shapes are used.
- No other dependencies: only `maya.cmds` and `maya.api.OpenMaya`.

## Usage

1. Select the joints of a chain.
2. Save `fk_chain.py` in your Maya scripts folder, then run in the Script Editor (Python tab):

```python
import fk_chain
fk_chain.build_fk_chain(shape="cube", radius=2.0)
```

Joints are sorted from parent to child automatically, and a `_jnt` suffix is removed from the control names.

### Parameters

| Parameter | Default | Description |
| --- | --- | --- |
| `shape` | `"circle"` | Name of the control shape (see below) |
| `radius` | `1.0` | Half-size of the control |
| `use_mgear` | `False` | Use the shape from mGear's icon library when available |

### Shapes

- **Built in:** `circle`, `square`, `diamond`, `cross`, `cube`.
- **From mGear** (`use_mgear=True`): `circle`, `square`, `cube`, `diamond`, `cross`, `sphere`, `pyramid`, `cylinder`, `gear`, `flower`, `arrow`, `crossarrow`, `compas`, `cubewithpeak`, `axis`.

mGear shapes are measured after creation: flat shapes are turned to face the X axis and every shape is scaled to the same size. If mGear is not installed or a shape cannot be created, the tool warns you and falls back to a built-in shape.

```python
fk_chain.build_fk_chain(shape="gear", radius=2.0, use_mgear=True)
```

## Naming convention

| Joint name | Control name | Color |
| --- | --- | --- |
| `L_arm` | `L_arm_ctrl` | Red |
| `R_arm` | `R_arm_ctrl` | Blue |
| `spine` | `spine_ctrl` | Yellow |

## Ideas for next versions

- Left/right mirroring (finding the opposite joint by name).
- Custom colors and naming rules.
- A small UI window.
- Integration as an mGear Shifter custom step.
