import argparse
import base64
import html
import json
import sys
import webbrowser
from pathlib import Path


THREE_VERSION = "0.161.0"


def build_html(stl_path: Path, stl_bytes: bytes) -> str:
    model_data = base64.b64encode(stl_bytes).decode("ascii")
    title = html.escape(stl_path.name)
    model_data_json = json.dumps(f"data:model/stl;base64,{model_data}")
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>STL viewer: {title}</title>
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: #111827; color: #e5e7eb; }}
    header {{ display: flex; gap: 12px; align-items: center; padding: 12px 16px; border-bottom: 1px solid #374151; }}
    header h1 {{ margin: 0; font-size: 1rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    #help {{ margin-left: auto; width: auto; padding: 6px 10px; }}
    main {{ display: grid; grid-template-columns: minmax(0, 1fr) 280px; height: calc(100vh - 53px); }}
    #viewport {{ min-width: 0; min-height: 0; position: relative; }}
    aside {{ padding: 16px; overflow-y: auto; background: #1f2937; border-left: 1px solid #374151; }}
    fieldset {{ margin: 0 0 16px; padding: 12px; border: 1px solid #4b5563; border-radius: 8px; }}
    legend {{ padding: 0 6px; color: #93c5fd; }}
    label {{ display: grid; grid-template-columns: 1fr 90px; gap: 8px; align-items: center; margin: 8px 0; font-size: .875rem; }}
    input, button {{ width: 100%; border: 1px solid #4b5563; border-radius: 5px; padding: 7px 8px; background: #111827; color: inherit; }}
    button {{ cursor: pointer; background: #2563eb; border-color: #3b82f6; }}
    button.secondary {{ background: #374151; border-color: #6b7280; }}
    .buttons {{ display: grid; gap: 8px; }}
    .operations {{ margin: 16px 0 0; padding-left: 20px; color: #d1d5db; font-size: .8rem; line-height: 1.5; }}
    .operations li {{ margin: 6px 0; }}
    .operations strong {{ color: #bfdbfe; }}
    .legend-group h3 {{ margin: 12px 0 6px; font-size: .85rem; color: #bfdbfe; }}
    #status {{ color: #9ca3af; font-size: .8rem; line-height: 1.4; }}
    @media (max-width: 700px) {{ main {{ grid-template-columns: 1fr; grid-template-rows: minmax(360px, 1fr) auto; height: auto; min-height: calc(100vh - 53px); }} aside {{ border-left: 0; border-top: 1px solid #374151; }} }}
  </style>
</head>
<body>
  <header><h1>{title}</h1><span id="status">Loading...</span><button id="help" class="secondary">Hide controls</button></header>
  <main>
    <section id="viewport" aria-label="3D STL model viewer"></section>
    <aside>
      <fieldset>
        <legend>Position</legend>
        <label>X <input id="position-x" type="number" step="0.1" value="0"></label>
        <label>Y <input id="position-y" type="number" step="0.1" value="0"></label>
        <label>Z <input id="position-z" type="number" step="0.1" value="0"></label>
      </fieldset>
      <fieldset>
        <legend>Rotation (degrees)</legend>
        <label>X <input id="rotation-x" type="number" step="1" value="0"></label>
        <label>Y <input id="rotation-y" type="number" step="1" value="0"></label>
        <label>Z <input id="rotation-z" type="number" step="1" value="0"></label>
      </fieldset>
      <fieldset>
        <legend>Scale</legend>
        <label>Uniform <input id="scale" type="number" min="0.001" step="0.1" value="1"></label>
      </fieldset>
      <div class="buttons">
        <button id="reset" class="secondary">Reset view and edits</button>
        <button id="save">Save as STL</button>
      </div>
      <fieldset id="controls-legend" tabindex="-1">
        <legend>Controls legend</legend>
        <div class="legend-group">
          <h3>Explore model</h3>
          <ul class="operations">
            <li><strong>[Orbit] Left mouse drag:</strong> rotate camera around model.</li>
            <li><strong>[Pan] Right mouse drag:</strong> move camera.</li>
            <li><strong>[Zoom] Mouse wheel:</strong> zoom camera in or out.</li>
          </ul>
        </div>
        <div class="legend-group">
          <h3>Manipulate model</h3>
          <ul class="operations">
            <li><strong>[Move] Position fields:</strong> move model on X, Y, or Z axis.</li>
            <li><strong>[Rotate] Rotation fields:</strong> rotate model around X, Y, or Z axis.</li>
            <li><strong>[Scale] Uniform scale:</strong> change model size.</li>
            <li><strong>[Reset] Reset view and edits:</strong> restore original transform and fitted camera.</li>
            <li><strong>[Save] Save as STL:</strong> download current edits as binary STL.</li>
          </ul>
        </div>
      </fieldset>
    </aside>
  </main>
  <script type="importmap">
    {{"imports": {{
      "three": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/"
    }}}}
  </script>
  <script type="module">
    import * as THREE from 'three';
    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
    import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';

    const embeddedModel = {model_data_json};
    const viewport = document.querySelector('#viewport');
    const status = document.querySelector('#status');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111827);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100000);
    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    viewport.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2);
    keyLight.position.set(1, 2, 3);
    scene.add(keyLight);
    scene.add(new THREE.GridHelper(10, 10, 0x475569, 0x334155));

    let mesh;
    let sourceName = {json.dumps(stl_path.name)};
    const sourceTransform = {{ position: new THREE.Vector3(), rotation: new THREE.Euler(), scale: new THREE.Vector3(1, 1, 1) }};

    function resize() {{
      const width = viewport.clientWidth;
      const height = viewport.clientHeight;
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    }}

    function fitCamera() {{
      if (!mesh) return;
      const box = new THREE.Box3().setFromObject(mesh);
      const sphere = box.getBoundingSphere(new THREE.Sphere());
      const distance = sphere.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2));
      camera.position.set(sphere.center.x + distance, sphere.center.y + distance * 0.6, sphere.center.z + distance);
      camera.near = Math.max(distance / 1000, 0.001);
      camera.far = Math.max(distance * 100, 1000);
      camera.updateProjectionMatrix();
      controls.target.copy(sphere.center);
      controls.update();
    }}

    function inputValue(id) {{ return Number(document.querySelector(id).value) || 0; }}

    function applyTransform() {{
      if (!mesh) return;
      mesh.position.set(inputValue('#position-x'), inputValue('#position-y'), inputValue('#position-z'));
      mesh.rotation.set(
        THREE.MathUtils.degToRad(inputValue('#rotation-x')),
        THREE.MathUtils.degToRad(inputValue('#rotation-y')),
        THREE.MathUtils.degToRad(inputValue('#rotation-z'))
      );
      const scale = Math.max(inputValue('#scale'), 0.001);
      mesh.scale.setScalar(scale);
    }}

    function reset() {{
      document.querySelectorAll('input').forEach((input) => {{ input.value = input.id === 'scale' ? '1' : '0'; }});
      applyTransform();
      fitCamera();
    }}

    function downloadEditedStl() {{
      mesh.updateMatrixWorld(true);
      const positions = mesh.geometry.getAttribute('position');
      const triangleCount = Math.floor(positions.count / 3);
      const buffer = new ArrayBuffer(84 + triangleCount * 50);
      const view = new DataView(buffer);
      const encoder = new TextEncoder();
      const header = encoder.encode('Edited by STL HTML Viewer');
      new Uint8Array(buffer, 0, header.length).set(header);
      view.setUint32(80, triangleCount, true);
      const first = new THREE.Vector3();
      const second = new THREE.Vector3();
      const third = new THREE.Vector3();
      const normal = new THREE.Vector3();
      for (let triangle = 0; triangle < triangleCount; triangle += 1) {{
        const offset = 84 + triangle * 50;
        first.fromBufferAttribute(positions, triangle * 3).applyMatrix4(mesh.matrixWorld);
        second.fromBufferAttribute(positions, triangle * 3 + 1).applyMatrix4(mesh.matrixWorld);
        third.fromBufferAttribute(positions, triangle * 3 + 2).applyMatrix4(mesh.matrixWorld);
        normal.subVectors(second, first).cross(new THREE.Vector3().subVectors(third, first)).normalize();
        [normal, first, second, third].forEach((vector, index) => {{
          view.setFloat32(offset + 12 + index * 12, vector.x, true);
          view.setFloat32(offset + 16 + index * 12, vector.y, true);
          view.setFloat32(offset + 20 + index * 12, vector.z, true);
        }});
        view.setUint16(offset + 48, 0, true);
      }}
      const filename = sourceName.replace(/\.stl$/i, '') + '-edited.stl';
      const link = document.createElement('a');
      link.href = URL.createObjectURL(new Blob([buffer], {{ type: 'model/stl' }}));
      link.download = filename;
      link.click();
      URL.revokeObjectURL(link.href);
    }}

    const bytes = Uint8Array.from(atob(embeddedModel.split(',')[1]), (character) => character.charCodeAt(0));
    mesh = new THREE.Mesh(new STLLoader().parse(bytes.buffer), new THREE.MeshStandardMaterial({{ color: 0x60a5fa, roughness: 0.65, metalness: 0.05 }}));
    scene.add(mesh);
    mesh.geometry.computeVertexNormals();
    document.querySelectorAll('input').forEach((input) => input.addEventListener('input', applyTransform));
    document.querySelector('#reset').addEventListener('click', reset);
    document.querySelector('#save').addEventListener('click', downloadEditedStl);
    document.querySelector('#help').addEventListener('click', () => {{
      const panel = document.querySelector('#controls-legend');
      const visible = !panel.hidden;
      panel.hidden = visible;
      document.querySelector('#help').textContent = visible ? 'Show controls' : 'Hide controls';
      if (!visible) panel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
    status.textContent = `${{mesh.geometry.getAttribute('position').count / 3}} triangles`;
    window.addEventListener('resize', resize);
    resize();
    fitCamera();
    renderer.setAnimationLoop(() => {{ controls.update(); renderer.render(scene, camera); }});
  </script>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Show and edit an STL file in an HTML viewer.")
    parser.add_argument("input_file", type=Path, help="ASCII or binary STL file")
    parser.add_argument("-o", "--output", type=Path, help="HTML output path")
    parser.add_argument("--no-open", action="store_true", help="Generate HTML without opening browser")
    args = parser.parse_args()

    if not args.input_file.is_file():
        print(f"Input STL file not found: {args.input_file}", file=sys.stderr)
        return 1

    output_path = args.output or args.input_file.with_suffix(".html")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_html(args.input_file, args.input_file.read_bytes()), encoding="utf-8")
    except OSError as error:
        print(f"Could not write HTML output: {error}", file=sys.stderr)
        return 1

    print(f"Generated HTML viewer: {output_path}")
    if not args.no_open:
        webbrowser.open(output_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
