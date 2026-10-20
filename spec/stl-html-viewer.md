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
- Select and move individual mesh vertices with an axis gizmo.
- Add a new vertex and connect it to existing vertices to form valid triangles.
- Preview vertex edits before saving.
- Save edited model as a new binary STL file.
- Open generated HTML in default browser by default.
- Allow explicit output path.
- Allow generation without opening browser for scripts and CI.

### Out of scope

- Editing or repairing STL geometry.
- Mesh conversion or slicing.
- Face extrusion, cutting, holes, boolean operations, and full CAD editing.
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

Generated HTML must show a `Controls legend` section containing:

- `Explore model` group:
  - Left mouse drag: orbit camera around model.
  - Right mouse drag: pan camera.
  - Mouse wheel: zoom camera.
- `Manipulate model` group:
  - Position fields: move model along X, Y, or Z axis.
  - Rotation fields: rotate model around X, Y, or Z axis.
  - Uniform scale field: change model size.
  - `Reset view and edits`: restore original transform and fitted camera.
  - `Save as STL`: download current edited model as binary STL.
- `Show controls` toggles legend visibility without changing model state.

Transform editing applies to the complete loaded mesh. Vertex editing changes selected vertex positions without altering topology.

### Vertex editing

The first shape-editing phase adds direct vertex manipulation:

- Click a visible vertex to select it.
- Show X, Y, and Z axis gizmo for selected vertex.
- Drag gizmo axis to move vertex along that axis.
- Update all triangles connected to moved vertex immediately.
- Keep other vertices unchanged.
- Show edited mesh in the viewport before save.
- `Reset vertex edits` restores vertex positions from source mesh.
- `Save as STL` exports edited vertex positions and recalculated normals.

Vertex editing changes mesh geometry but does not add or remove triangles. STL files do not retain original parametric dimensions, so controls such as wall thickness or named hole diameter are not available for arbitrary imported STL files.

### Adding a vertex and connecting to existing vertices

STL files only support complete 3-vertex facets (triangles). Free floating vertices or standalone edges cannot exist in STL geometry. Therefore, adding a vertex must always form complete triangles.

Connecting a new vertex to existing vertices supports two workflows:

1. **Automatic Triangle Subdivision (Split mode):**
   - Click any point on an existing triangle face.
   - Places new vertex $P$ at intersection point.
   - Automatically replaces the hit triangle $(V_A, V_B, V_C)$ with three new triangles: $(V_A, V_B, P)$, $(V_B, V_C, P)$, and $(V_C, V_A, P)$.
   - Preserves closed surface manifold topology.

2. **Manual Vertex Connection (Connect mode):**
   - User activates `Add & Connect Vertex` mode.
   - Step 1: Click to place new vertex position $P$ on model surface. A temporary point marker highlights $P$.
   - Step 2: Hover/click existing vertices on model to select connections.
     - Select 2 existing vertices $(V_1, V_2)$ to create one triangle $(P, V_1, V_2)$.
     - User can select additional vertex pairs to create fan or bridge connections around $P$.
   - Step 3: Click `Complete` or automatically finalize once triangle is formed.
   - Normal is computed automatically based on right-hand rule or matching adjacent face orientations.
   - Triangle count in status bar increments accordingly.
   - Cancel button discards pending unattached vertex without corrupting mesh.

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

This version treats "edit shape" as transform editing, direct vertex movement, and vertex insertion with triangle formation. All edits maintain valid triangle meshes for STL export.

Cutting, hole creation, boolean union/subtraction, face extrusion, and mesh repair remain separate editor phases because they need topology changes, validation, and more extensive export testing.

## 10. Verification

Use repository model:

```bash
python src/show_stl.py empty_cube.ascii.stl --no-open
```

Verify generated HTML exists, then open it in browser and confirm model renders, rotates, pans, zooms, and resets.

Change position, rotation, and scale. Confirm rendered model updates. Export edited STL and confirm source file remains unchanged.

Select a vertex, move it along each axis, confirm connected triangles update, reset vertex edits, and save a new STL. Confirm source file remains unchanged and saved STL contains moved vertex geometry.

Add a vertex by clicking a triangle or picking existing vertices to connect, confirm new triangles render, normals update, and exported STL contains newly created faces.
