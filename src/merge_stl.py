import argparse
import struct
from pathlib import Path


def is_ascii_stl(file_path: Path) -> bool:
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            if header != b"solid":
                return False
            f.seek(0)
            chunk = f.read(1024)
            return b"\x00" not in chunk
    except Exception:
        return False


def parse_stl(file_path: Path):
    if is_ascii_stl(file_path):
        return parse_stl_ascii(file_path)
    return parse_stl_binary(file_path)


def parse_stl_ascii(file_path: Path):
    facets = []
    current_normal = (0.0, 0.0, 0.0)
    current_vertices = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens:
                continue
            if tokens[0] == "facet" and tokens[1] == "normal":
                current_normal = (float(tokens[2]), float(tokens[3]), float(tokens[4]))
                current_vertices = []
            elif tokens[0] == "vertex":
                current_vertices.append((float(tokens[1]), float(tokens[2]), float(tokens[3])))
            elif tokens[0] == "endfacet":
                if len(current_vertices) == 3:
                    facets.append((current_normal, current_vertices))

    return facets


def parse_stl_binary(file_path: Path):
    facets = []
    with open(file_path, "rb") as f:
        f.seek(80)
        num_triangles_data = f.read(4)
        if len(num_triangles_data) < 4:
            return facets
        num_triangles = struct.unpack("<I", num_triangles_data)[0]

        for _ in range(num_triangles):
            data = f.read(50)
            if len(data) < 50:
                break
            vals = struct.unpack("<12fH", data)
            normal = (vals[0], vals[1], vals[2])
            v1 = (vals[3], vals[4], vals[5])
            v2 = (vals[6], vals[7], vals[8])
            v3 = (vals[9], vals[10], vals[11])
            facets.append((normal, [v1, v2, v3]))

    return facets


def get_bounds(facets):
    min_x = min(min(v[0] for v in tri) for _, tri in facets)
    max_x = max(max(v[0] for v in tri) for _, tri in facets)
    min_y = min(min(v[1] for v in tri) for _, tri in facets)
    max_y = max(max(v[1] for v in tri) for _, tri in facets)
    min_z = min(min(v[2] for v in tri) for _, tri in facets)
    max_z = max(max(v[2] for v in tri) for _, tri in facets)
    return (min_x, max_x), (min_y, max_y), (min_z, max_z)


def translate_facets(facets, offset_x: float, offset_y: float, offset_z: float):
    translated = []
    for normal, tri in facets:
        new_tri = [
            (v[0] + offset_x, v[1] + offset_y, v[2] + offset_z)
            for v in tri
        ]
        translated.append((normal, new_tri))
    return translated


def write_stl_ascii(output_path: Path, all_facets):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("solid merged\n")
        for normal, tri in all_facets:
            f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
            f.write("    outer loop\n")
            for v in tri:
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid merged\n")


def merge_stls(base_path: str, attach_path: str, output_path: str, axis: str, overlap: float):
    base_facets = parse_stl(Path(base_path))
    attach_facets = parse_stl(Path(attach_path))

    bx, by, bz = get_bounds(base_facets)
    ax, ay, az = get_bounds(attach_facets)

    axis = axis.lower()
    offset_x = 0.0
    offset_y = 0.0
    offset_z = 0.0

    if axis == "z":
        offset_z = (bz[1] - overlap) - az[0]
    elif axis == "y":
        offset_y = (by[1] - overlap) - ay[0]
    elif axis == "x":
        offset_x = (bx[1] - overlap) - ax[0]
    else:
        raise ValueError("Axis must be 'x', 'y', or 'z'")

    shifted_attach = translate_facets(attach_facets, offset_x, offset_y, offset_z)
    all_facets = base_facets + shifted_attach

    write_stl_ascii(Path(output_path), all_facets)

    total_bounds = get_bounds(all_facets)
    print(f"Merged: {output_path}")
    print(f"  Base triangles: {len(base_facets)}")
    print(f"  Attach triangles: {len(attach_facets)}")
    print(f"  Total triangles: {len(all_facets)}")
    print(f"  Offset applied on {axis.upper()}: {offset_x if axis=='x' else offset_y if axis=='y' else offset_z:.2f}mm")
    print(f"  Overlap: {overlap:.2f}mm")
    print(f"  Bounding box X: {total_bounds[0][0]:.1f} -> {total_bounds[0][1]:.1f}mm")
    print(f"  Bounding box Y: {total_bounds[1][0]:.1f} -> {total_bounds[1][1]:.1f}mm")
    print(f"  Bounding box Z: {total_bounds[2][0]:.1f} -> {total_bounds[2][1]:.1f}mm")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge two STL files with controlled overlap/intersection.")
    parser.add_argument("--base", required=True, help="Base STL file path")
    parser.add_argument("--attach", required=True, help="STL file to attach on top/side")
    parser.add_argument("-o", "--output", required=True, help="Merged output STL file path")
    parser.add_argument("--axis", choices=["x", "y", "z"], default="z", help="Axis to stack along (default: z)")
    parser.add_argument("--overlap", type=float, default=0.0, help="Overlap / intersection amount in mm (default: 0.0)")

    args = parser.parse_args()
    merge_stls(args.base, args.attach, args.output, args.axis, args.overlap)
