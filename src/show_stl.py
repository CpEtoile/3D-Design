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
    source_name_json = json.dumps(stl_path.name)
    viewer_script = Path(__file__).with_name("stl_viewer.js").read_text(encoding="utf-8")
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
    #show-control {{ margin-left: auto; width: auto; padding: 6px 10px; }}
    main {{ display: grid; grid-template-columns: minmax(0, 1fr) 280px; height: calc(100vh - 53px); }}
    #viewport {{ min-width: 0; min-height: 360px; position: relative; background: #0b1220; border-right: 1px solid #374151; }}
    #viewport canvas {{ display: block; width: 100%; height: 100%; }}
    #viewport-message {{ position: absolute; inset: 0; display: grid; place-items: center; padding: 24px; color: #fca5a5; white-space: pre-wrap; overflow: auto; text-align: left; pointer-events: none; }}
    aside {{ display: flex; flex-direction: column; padding: 16px; overflow-y: auto; background: #1f2937; border-left: 1px solid #374151; }}
    #controls-legend {{ order: -1; position: sticky; top: 0; z-index: 5; background: #1f2937; }}
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
    #vertex-status, #status {{ color: #9ca3af; font-size: .8rem; line-height: 1.4; }}
    @media (max-width: 700px) {{ main {{ grid-template-columns: 1fr; grid-template-rows: minmax(360px, 1fr) auto; height: auto; min-height: calc(100vh - 53px); }} aside {{ border-left: 0; border-top: 1px solid #374151; }} }}
  </style>
</head>
<body>
  <header><h1>{title}</h1><span id="status">Loading...</span><button id="show-control" class="secondary">Hide controls</button></header>
  <main>
    <section id="viewport" aria-label="3D STL model viewer">
      <div id="viewport-message" hidden></div>
    </section>
    <aside>
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
      <fieldset>
        <legend>Vertex editing</legend>
        <p id="vertex-status">Select vertex: click a vertex on model.</p>
        <button id="reset-vertices" class="secondary">Reset vertex edits</button>
      </fieldset>
    </aside>
  </main>
  <script type="importmap">
    {{"imports": {{
      "three": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/examples/jsm/"
    }}}}
  </script>
  <script>
    function formatViewerError(error, fallbackMessage) {{
      if (error instanceof Error) return error.stack || error.message;
      if (typeof error === 'string') return error;
      try {{ return JSON.stringify(error, null, 2); }} catch {{ return fallbackMessage || String(error); }}
    }}
    function showViewerError(error, fallbackMessage) {{
      const message = document.querySelector('#viewport-message');
      if (!message) return;
      message.hidden = false;
      message.textContent = `Viewer error:\n${{formatViewerError(error, fallbackMessage)}}`;
    }}
    window.addEventListener('error', (event) => {{ showViewerError(event.error, event.message); }});
    window.addEventListener('unhandledrejection', (event) => {{ showViewerError(event.reason, 'Unhandled promise rejection'); }});
    window.STL_MODEL_DATA = {model_data_json};
    window.STL_SOURCE_NAME = {source_name_json};
  </script>
  <script type="module">
{viewer_script}
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
