# 3D Design STL Tools

Python tools for inspecting and editing STL files used in 3D printing.

## STL HTML Viewer

Open an STL file in an interactive browser viewer:

```bash
python3 src/show_stl.py model.stl
```

For example, to view the generated rectangular frame:

```bash
python3 src/show_stl.py output.stl
```

The command creates `output.html` (or `<filename>.html`) beside the STL file and opens it in the default browser. It reads mesh geometry, calculates dimensions, and displays measurements in centimeters (assuming standard millimeter STL coordinates).

Generate HTML without opening a browser:

```bash
python3 src/show_stl.py model.stl --no-open
```

Choose an output path:

```bash
python3 src/show_stl.py model.stl --output viewer.html
```

## Generate Rectangular Frame STL

Generate a hollow rectangular tube/frame STL file using millimeter units:

```bash
python3 src/generate_rectangle_from.py \
  --output output.stl \
  --outer-width 40 \
  --outer-length 40 \
  --inner-width 30 \
  --inner-length 30 \
  --height 50
```

Parameters:

- `-o, --output`: output STL file path (e.g. `output.stl`)
- `--outer-width`: outer width along X axis in mm (e.g. `40` for 4 cm)
- `--outer-length`: outer length along Y axis in mm (e.g. `40` for 4 cm)
- `--inner-width`: inner hole width along X axis in mm (e.g. `30` for 3 cm)
- `--inner-length`: inner hole length along Y axis in mm (e.g. `30` for 3 cm)
- `--height`: vertical extrusion height along Z axis in mm (e.g. `50` for 5 cm)

Produces an ASCII STL centered on X and Y, sitting on Z=0. Wall thickness is `(outer - inner) / 2` (5 mm / 0.5 cm in example above).

## Merge Two STL Files

Merge two STL models along an axis with controlled overlap/intersection:

```bash
python3 src/merge_stl.py \
  --base output.stl \
  --attach part_top.stl \
  --output merged.stl \
  --axis z \
  --overlap 5
```

Parameters:

- `--base`: base STL file path
- `--attach`: secondary STL file to attach
- `-o, --output`: merged output STL file path
- `--axis`: axis to stack along (`x`, `y`, or `z`, default `z`)
- `--overlap`: intersection amount in mm (e.g. `5` sinks the attached part 5 mm into the base)

Viewer features:

- Orbit, pan, and zoom model
- Edit position, rotation, and scale
- Select and move mesh vertices with X/Y/Z gizmo
- Add a vertex by clicking a triangle, splitting it into three triangles
- Reset vertex edits
- Reset view and edits
- Save edited model as a new binary STL with `Save as STL`
- Keep source STL unchanged

Generated HTML loads Three.js and STLLoader from a pinned CDN URL, so browser needs internet access.

## Binary STL Conversion

STL files exported from tools such as [Tinkercad](https://www.tinkercad.com/) may use binary format. The existing conversion script converts the configured binary input into readable ASCII STL:

```python src/binary_convertion.py```

Update input and output paths in `src/binary_convertion.py` before running it.

## Tests

Install pytest:

```bash
python3 -m pip install pytest
```

Run viewer tests:

```bash
python3 -m pytest -q tests/test_show_stl.py
```

## Specification

Feature requirements and acceptance criteria are in `spec/stl-html-viewer.md`.
