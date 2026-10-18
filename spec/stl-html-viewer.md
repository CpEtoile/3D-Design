# SDD: STL HTML Viewer

## 1. Goal

Provide one command that opens an STL model in an interactive HTML viewer.

## 2. User Story

As a 3D design user, I want to run a command with an STL path so I can inspect the model shape in a browser before printing or editing it.

## 3. Scope

### In scope

- Read ASCII and binary STL files.
- Generate an HTML file containing the selected model data.
- Display model with orbit, pan, and zoom controls.
- Fit model to camera automatically.
- Show model metadata: file name and triangle count when available.
- Edit rendered model transform: position, rotation, and scale.
- Save edited model from the HTML page as a new binary STL file.
- Open generated HTML in default browser by default.
- Allow explicit output path.
- Allow generation without opening browser for scripts and CI.

### Out of scope

- Editing or repairing STL geometry.
- Mesh conversion or slicing.
- Vertex-level sculpting, cutting, holes, and boolean operations.
- Persistent web server.
- Support for formats other than STL.

## 4. Proposed Command

```bash
python src/show_stl.py MODEL.stl
```

Options:

```text
-o, --output PATH   HTML output path. Default: MODEL.html
--no-open           Generate HTML without opening browser
```

Examples:

```bash
python src/show_stl.py cover2.stl
python src/show_stl.py "Swanky Esboo-Wluff.stl_ascii.stl" --output /tmp/model.html
python src/show_stl.py model.stl --no-open
```

## 5. Behavior

1. Validate input path exists and is a regular file.
2. Read STL bytes without changing source file.
3. Embed model bytes in generated HTML using base64.
4. Write HTML to requested output path, creating its parent directory when needed.
5. Print generated output path.
6. Open output with system default browser unless `--no-open` is supplied.

Invalid input or output errors must return a non-zero exit status and a concise error message.

## 6. Viewer UX

- Dark background suitable for inspecting light-colored meshes.
- Neutral solid material with visible edges or lighting.
- Left-drag orbit, right-drag pan, wheel zoom through standard trackball controls.
- `Reset view` control restores fitted camera.
- Model centered and scaled to fit viewport.
- Responsive layout for desktop and mobile browser widths.
- Visible operations guide explains every available control, gesture, and result.

### Editing controls

- Numeric controls for X, Y, Z position.
- Numeric controls for X, Y, Z rotation in degrees.
- Uniform scale control, with an option to unlock independent axis scaling.
- `Apply` updates the rendered model immediately.
- `Reset edits` restores source transform.
- `Save as STL` converts the currently edited HTML model into a new binary STL file and downloads it.
- Export name defaults to the source name with `-edited.stl` suffix.
- Save uses current position, rotation, and scale values.
- Save operation does not overwrite the source STL or generated HTML.

### Operations guide

Generated HTML must show an `Operations` section containing:

- Left mouse drag: orbit camera around model.
- Right mouse drag: pan camera.
- Mouse wheel: zoom camera.
- Position fields: move model along X, Y, or Z axis.
- Rotation fields: rotate model around X, Y, or Z axis.
- Uniform scale field: change model size.
- `Reset view and edits`: restore original transform and fitted camera.
- `Save as STL`: download current edited model as binary STL.

Editing applies to the complete loaded mesh. It does not modify individual triangles or alter topology.

## 7. Technical Design

- Python standard library handles argument parsing, file reading, base64 encoding, and browser launch.
- Generated page loads Three.js and STLLoader from pinned CDN URLs.
- Browser decodes embedded bytes and parses STL client-side.
- Browser applies transforms through Three.js before export.
- Save uses transformed triangle vertices and recalculated normals to create a binary STL.
- No Python package installation required.
- Generated HTML remains portable, but requires network access for CDN assets.

## 8. Acceptance Criteria

- `python src/show_stl.py existing-model.stl --no-open` exits with status 0 and creates HTML.
- Generated HTML contains embedded model data and viewer code.
- Generated HTML does not require a local server to open.
- Both repository ASCII STL and binary STL input are accepted.
- Default output is next to input with `.html` suffix.
- `--output` writes exactly to requested path.
- Missing input returns non-zero status without creating HTML.
- Browser launch is skipped with `--no-open`.
- Position, rotation, and scale controls visibly change model shape or placement.
- Edited HTML can save its current model as a downloadable binary STL.
- Saved STL contains transformed model geometry and opens as a valid STL file.
- Source STL remains unchanged after editing and export.

## 9. Editing Boundary

This version treats "edit shape" as transform editing. It changes model placement, orientation, and size while preserving mesh topology.

If individual vertex editing, cutting, hole creation, boolean union/subtraction, or mesh repair is required, that should be specified as a separate editor phase because it needs selection tools, topology validation, and more extensive export testing.

## 10. Verification

Use repository model:

```bash
python src/show_stl.py empty_cube.ascii.stl --no-open
```

Verify generated HTML exists, then open it in browser and confirm model renders, rotates, pans, zooms, and resets.

Change position, rotation, and scale. Confirm rendered model updates. Export edited STL and confirm source file remains unchanged.
