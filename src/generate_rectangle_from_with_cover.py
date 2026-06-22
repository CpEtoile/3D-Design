import argparse


def generate_cover_and_file(output_file_name: str, outer_w: float, outer_h: float, wall_thickness: float, total_height: float):
    """
    Generate a hollow rectangular cover (box lid) as an ASCII STL file.
    The cover has a solid top, walls going down, and is open at the bottom.
    It can be placed over a rectangular frame to close it.

    Shape (cross-section):
        |====================|  <- top (solid)
        |  |              |  |
        |  |   (hollow)   |  |  <- walls with wall_thickness
        |  |              |  |
        |__|              |__|  <- open bottom
    """
    output_file = output_file_name

    inner_w = outer_w - 2 * wall_thickness
    inner_h = outer_h - 2 * wall_thickness
    cavity_height = total_height - wall_thickness  # height of the hollow cavity

    # Half-dimensions (centered at origin)
    ow = outer_w / 2
    oh = outer_h / 2
    iw = inner_w / 2
    ih = inner_h / 2

    z0 = 0.0
    z1 = cavity_height  # top of inner walls / bottom of top plate
    z2 = total_height   # top surface

    # Outer corners
    o = [(-ow, -oh), (ow, -oh), (ow, oh), (-ow, oh)]
    # Inner corners
    i = [(-iw, -ih), (iw, -ih), (iw, ih), (-iw, ih)]

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

        # --- Top face (z=total_height), solid rectangle, normal (0, 0, 1) ---
        write_facet(f, (0, 0, 1),
                    (-ow, -oh, z2), (ow, -oh, z2), (ow, oh, z2))
        write_facet(f, (0, 0, 1),
                    (-ow, -oh, z2), (ow, oh, z2), (-ow, oh, z2))

        # --- Bottom ring face (z=0), normal (0, 0, -1) ---
        # Ring between outer and inner perimeter (open in the middle)
        for side in range(4):
            n = (side + 1) % 4
            write_facet(f, (0, 0, -1),
                        (o[side][0], o[side][1], z0),
                        (i[side][0], i[side][1], z0),
                        (i[n][0], i[n][1], z0))
            write_facet(f, (0, 0, -1),
                        (o[side][0], o[side][1], z0),
                        (i[n][0], i[n][1], z0),
                        (o[n][0], o[n][1], z0))

        # --- Inner ceiling (z=cavity_height), solid rectangle, normal (0, 0, -1) ---
        # This is the underside of the top plate, closing the cavity
        write_facet(f, (0, 0, -1),
                    (-iw, -ih, z1), (iw, ih, z1), (iw, -ih, z1))
        write_facet(f, (0, 0, -1),
                    (-iw, -ih, z1), (-iw, ih, z1), (iw, ih, z1))

        # --- Outer walls (4 sides), z=0 to z=total_height ---
        normals_outer = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
        for side in range(4):
            n = (side + 1) % 4
            nx, ny, nz = normals_outer[side]
            write_facet(f, (nx, ny, nz),
                        (o[side][0], o[side][1], z0),
                        (o[n][0], o[n][1], z0),
                        (o[n][0], o[n][1], z2))
            write_facet(f, (nx, ny, nz),
                        (o[side][0], o[side][1], z0),
                        (o[n][0], o[n][1], z2),
                        (o[side][0], o[side][1], z2))

        # --- Inner walls (4 sides), z=0 to z=cavity_height ---
        # Normals point inward (toward the hollow center)
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

    print(f"Generated hollow cover: {output_file}")
    print(f"  Outer: {outer_w}mm x {outer_h}mm")
    print(f"  Inner cavity: {inner_w}mm x {inner_h}mm")
    print(f"  Total height: {total_height}mm")
    print(f"  Wall thickness: {wall_thickness}mm")
    print(f"  Cavity depth: {cavity_height}mm")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a hollow rectangular cover (box lid) STL file.")
    parser.add_argument("output_file_name", type=str, help="Output STL file name (e.g. cover_lid.stl_ascii.stl)")
    parser.add_argument("outer_w", type=float, help="Outer width in mm")
    parser.add_argument("outer_h", type=float, help="Outer height in mm")
    parser.add_argument("wall_thickness", type=float, help="Wall and top plate thickness in mm")
    parser.add_argument("total_height", type=float, help="Total height of the cover in mm")

    args = parser.parse_args()
    generate_cover_and_file(args.output_file_name, args.outer_w, args.outer_h, args.wall_thickness, args.total_height)
