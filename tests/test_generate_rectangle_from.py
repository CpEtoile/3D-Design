import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "src" / "generate_rectangle_from.py"


def run_generator(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, args)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def parse_stl_vertices(stl_path: Path):
    vertices = []
    for line in stl_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            parts = line.split()
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
    return vertices


def test_symmetric_outer_width(tmp_path):
    output_stl = tmp_path / "symmetric.stl"
    result = run_generator(
        "--output", output_stl,
        "--outer-width", 40,
        "--outer-length", 40,
        "--inner-width", 30,
        "--inner-length", 30,
        "--height", 50,
    )
    assert result.returncode == 0
    assert output_stl.exists()

    vertices = parse_stl_vertices(output_stl)
    xs = {v[0] for v in vertices}
    ys = {v[1] for v in vertices}
    zs = {v[2] for v in vertices}

    assert xs == {-20.0, -15.0, 15.0, 20.0}
    assert ys == {-20.0, -15.0, 15.0, 20.0}
    assert zs == {0.0, 50.0}


def test_asymmetric_outer_left_right(tmp_path):
    output_stl = tmp_path / "asymmetric.stl"
    result = run_generator(
        "--output", output_stl,
        "--outer-left", 40,
        "--outer-right", 20,
        "--outer-length", 40,
        "--inner-width", 30,
        "--inner-length", 30,
        "--height", 50,
    )
    assert result.returncode == 0
    assert output_stl.exists()

    vertices = parse_stl_vertices(output_stl)
    xs = {v[0] for v in vertices}
    ys = {v[1] for v in vertices}
    zs = {v[2] for v in vertices}

    assert xs == {-40.0, -15.0, 15.0, 20.0}
    assert ys == {-20.0, -15.0, 15.0, 20.0}
    assert zs == {0.0, 50.0}


def test_missing_width_and_left_right_errors(tmp_path):
    output_stl = tmp_path / "missing.stl"
    result = run_generator(
        "--output", output_stl,
        "--outer-length", 40,
        "--inner-width", 30,
        "--inner-length", 30,
        "--height", 50,
    )
    assert result.returncode != 0
