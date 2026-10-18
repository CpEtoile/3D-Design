# 3D Design STL Tools

Python tools for inspecting and editing STL files used in 3D printing.

## STL HTML Viewer

Open an STL file in an interactive browser viewer:

```bash
python3 src/show_stl.py model.stl
```

The command creates `model.html` beside the STL file and opens it in the default browser.

Generate HTML without opening a browser:

```bash
python3 src/show_stl.py model.stl --no-open
```

Choose an output path:

```bash
python3 src/show_stl.py model.stl --output viewer.html
```

Viewer features:

- Orbit, pan, and zoom model
- Edit position, rotation, and scale
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
