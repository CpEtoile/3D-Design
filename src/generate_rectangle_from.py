import argparse

def generate_form_and_file(output_file_name: str, outer_width: float = None, outer_length: float = None, inner_width: float = None, inner_length: float = None, height: float = None, outer_left: float = None, outer_right: float = None):
    if outer_left is not None and outer_right is not None:
        ow_left = outer_left
        ow_right = outer_right
        outer_width = outer_left + outer_right
    elif outer_width is not None:
        ow_left = outer_width / 2
        ow_right = outer_width / 2
    else:
        raise ValueError("Either outer_width or both outer_left and outer_right must be specified")

    ol = outer_length / 2
    iw = inner_width / 2
    il = inner_length / 2

    def write_facet(f, normal, v1, v2, v3):
        f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
        f.write("    outer loop\n")
        f.write(f"      vertex {v1[0]} {v1[1]} {v1[2]}\n")
        f.write(f"      vertex {v2[0]} {v2[1]} {v2[2]}\n")
        f.write(f"      vertex {v3[0]} {v3[1]} {v3[2]}\n")
        f.write("    endloop\n")
        f.write("  endfacet\n")

    with open(output_file_name, "w") as f:
        f.write("solid ascii_model\n")

        z0 = 0.0
        z1 = height

        o = [(-ow_left, -ol), (ow_right, -ol), (ow_right, ol), (-ow_left, ol)]
        i = [(-iw, -il), (iw, -il), (iw, il), (-iw, il)]

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

    print(f"Generated: {output_file_name}")
    print(f"  Outer: {outer_width}mm x {outer_length}mm ({outer_width/10}cm x {outer_length/10}cm)")
    print(f"  Outer extent X: -{ow_left}mm to +{ow_right}mm")
    print(f"  Inner hole: {inner_width}mm x {inner_length}mm ({inner_width/10}cm x {inner_length/10}cm)")
    print(f"  Height: {height}mm ({height/10}cm)")
    print(f"  Wall thickness X left: {ow_left - iw}mm ({(ow_left - iw) / 10}cm)")
    print(f"  Wall thickness X right: {ow_right - iw}mm ({(ow_right - iw) / 10}cm)")
    print(f"  Wall thickness Y: {(outer_length - inner_length) / 2}mm ({(outer_length - inner_length) / 20}cm)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a rectangular frame STL file.")
    parser.add_argument("-o", "--output", dest="output_file_name", type=str, required=True, help="Output STL file name")
    parser.add_argument("--outer-width", dest="outer_width", type=float, default=None, help="Outer width X (mm)")
    parser.add_argument("--outer-left", dest="outer_left", type=float, default=None, help="Outer left extent X (mm)")
    parser.add_argument("--outer-right", dest="outer_right", type=float, default=None, help="Outer right extent X (mm)")
    parser.add_argument("--outer-length", dest="outer_length", type=float, required=True, help="Outer length Y (mm)")
    parser.add_argument("--inner-width", dest="inner_width", type=float, required=True, help="Inner hole width X (mm)")
    parser.add_argument("--inner-length", dest="inner_length", type=float, required=True, help="Inner hole length Y (mm)")
    parser.add_argument("--height", dest="height", type=float, required=True, help="Height Z (mm)")

    args = parser.parse_args()
    if args.outer_width is None and (args.outer_left is None or args.outer_right is None):
        parser.error("Either --outer-width or both --outer-left and --outer-right must be specified")

    generate_form_and_file(
        output_file_name=args.output_file_name,
        outer_width=args.outer_width,
        outer_length=args.outer_length,
        inner_width=args.inner_width,
        inner_length=args.inner_length,
        height=args.height,
        outer_left=args.outer_left,
        outer_right=args.outer_right,
    )
