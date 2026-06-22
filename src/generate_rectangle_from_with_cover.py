import argparse

def generate_form_and_file(output_file_name: str, outer_w: float, outer_h: float, inner_w: float, inner_h: float, thickness: float):
    # src/generate_rect_cover.py
    # eg "cover4.stl_ascii.stl"
    output_file = output_file_name

    # Dimensions (mm)
    # outer_w = 70.0  # 7 cm outer width
    # outer_h = 70.0  # 7 cm outer height
    # inner_w = 60.0  # 6 cm inner width
    # inner_h = 60.0  # 6 cm inner height
    # thickness = 4.0  # keep 4mm height

    # Half-dimensions (centered at origin)
    ow = outer_w / 2  # 35
    oh = outer_h / 2  # 35
    iw = inner_w / 2  # 30
    ih = inner_h / 2  # 30

    def write_facet(f, normal, v1, v2, v3):
        f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
        f.write("    outer loop\n")
        f.write(f"      vertex {v1[0]} {v1[1]} {v1[2]}\n")
        f.write(f"      vertex {v2[0]} {v2[1]} {v2[2]}\n")
        f.write(f"      vertex {v3[0]} {v3[1]} {v3[2]}\n")
        f.write("    endloop\n")
        f.write("  endfacet\n")

    with open(output_file, "w") as f:
        f.write("solid ascii_model\n")

        z0 = 0.0
        z1 = thickness

        # Outer corners (bottom-left, bottom-right, top-right, top-left)
        o = [(-ow, -oh), (ow, -oh), (ow, oh), (-ow, oh)]
        # Inner corners
        i = [(-iw, -ih), (iw, -ih), (iw, ih), (-iw, ih)]

        # --- Bottom face (z=0), normal (0, 0, -1) ---
        # 8 triangles to form the rectangular ring on bottom
        for side in range(4):
            n = (side + 1) % 4
            # Triangle: outer[side], inner[side], inner[next]
            write_facet(f, (0, 0, -1),
                        (o[side][0], o[side][1], z0),
                        (i[side][0], i[side][1], z0),
                        (i[n][0], i[n][1], z0))
            # Triangle: outer[side], inner[next], outer[next]
            write_facet(f, (0, 0, -1),
                        (o[side][0], o[side][1], z0),
                        (i[n][0], i[n][1], z0),
                        (o[n][0], o[n][1], z0))

        # --- Top face (z=thickness), normal (0, 0, 1) ---
        for side in range(4):
            n = (side + 1) % 4
            write_facet(f, (0, 0, 1),
                        (o[side][0], o[side][1], z1),
                        (i[n][0], i[n][1], z1),
                        (i[side][0], i[side][1], z1))
            write_facet(f, (0, 0, 1),
                        (o[side][0], o[side][1], z1),
                        (o[n][0], o[n][1], z1),
                        (i[n][0], i[n][1], z1))

        # --- Outer walls (4 sides) ---
        normals_outer = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
        for side in range(4):
            n = (side + 1) % 4
            nx, ny, nz = normals_outer[side]
            write_facet(f, (nx, ny, nz),
                        (o[side][0], o[side][1], z0),
                        (o[n][0], o[n][1], z0),
                        (o[n][0], o[n][1], z1))
            write_facet(f, (nx, ny, nz),
                        (o[side][0], o[side][1], z0),
                        (o[n][0], o[n][1], z1),
                        (o[side][0], o[side][1], z1))

        # --- Inner walls (4 sides, normals point inward) ---
        normals_inner = [(0, 1, 0), (-1, 0, 0), (0, -1, 0), (1, 0, 0)]
        for side in range(4):
            n = (side + 1) % 4
            nx, ny, nz = normals_inner[side]
            write_facet(f, (nx, ny, nz),
                        (i[side][0], i[side][1], z0),
                        (i[n][0], i[n][1], z1),
                        (i[n][0], i[n][1], z0))
            write_facet(f, (nx, ny, nz),
                        (i[side][0], i[side][1], z0),
                        (i[side][0], i[side][1], z1),
                        (i[n][0], i[n][1], z1))

        f.write("endsolid ascii_model\n")

    print(f"Generated: {output_file}")
    print(f"  Outer: {outer_w}mm x {outer_h}mm (7cm x 7cm)")
    print(f"  Inner hole: {inner_w}mm x {inner_h}mm (6cm x 6cm)")
    print(f"  Height: {thickness}mm")
    print(f"  Wall thickness: {(outer_w - inner_w) / 2}mm")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a rectangular frame STL file.")
    parser.add_argument("output_file_name", type=str, help="Output STL file name (e.g. cover4.stl_ascii.stl)")
    parser.add_argument("outer_w", type=float, help="Outer width in mm")
    parser.add_argument("outer_h", type=float, help="Outer height in mm")
    parser.add_argument("inner_w", type=float, help="Inner width in mm")
    parser.add_argument("inner_h", type=float, help="Inner height in mm")
    parser.add_argument("thickness", type=float, help="Thickness (height) in mm")

    args = parser.parse_args()
    generate_form_and_file(args.output_file_name, args.outer_w, args.outer_h, args.inner_w, args.inner_h, args.thickness)
