import math

# Parameters
outer_radius = 35.0  # 7 cm diameter / 2
inner_radius = 30.0  # 6 cm diameter / 2
height = 4.0  # keep 4mm thickness
segments = 64  # number of segments to approximate circles
output_file = "cover3.stl_ascii.stl"


def vertex_str(x, y, z):
    return f"      vertex {x} {y} {z}\n"


def write_facet(f, normal, v1, v2, v3):
    f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
    f.write("    outer loop\n")
    f.write(vertex_str(*v1))
    f.write(vertex_str(*v2))
    f.write(vertex_str(*v3))
    f.write("    endloop\n")
    f.write("  endfacet\n")


with open(output_file, "w") as f:
    f.write("solid ascii_model\n")

    for i in range(segments):
        angle1 = 2 * math.pi * i / segments
        angle2 = 2 * math.pi * (i + 1) / segments

        # Outer circle points
        ox1 = outer_radius * math.cos(angle1)
        oy1 = outer_radius * math.sin(angle1)
        ox2 = outer_radius * math.cos(angle2)
        oy2 = outer_radius * math.sin(angle2)

        # Inner circle points
        ix1 = inner_radius * math.cos(angle1)
        iy1 = inner_radius * math.sin(angle1)
        ix2 = inner_radius * math.cos(angle2)
        iy2 = inner_radius * math.sin(angle2)

        # --- Bottom face (z=0), normal (0, 0, -1) ---
        write_facet(f, (0, 0, -1), (ox1, oy1, 0), (ix1, iy1, 0), (ix2, iy2, 0))
        write_facet(f, (0, 0, -1), (ox1, oy1, 0), (ix2, iy2, 0), (ox2, oy2, 0))

        # --- Top face (z=height), normal (0, 0, 1) ---
        write_facet(f, (0, 0, 1), (ox1, oy1, height), (ix2, iy2, height), (ix1, iy1, height))
        write_facet(f, (0, 0, 1), (ox1, oy1, height), (ox2, oy2, height), (ix2, iy2, height))

        # --- Outer wall, normal points outward ---
        nx = math.cos((angle1 + angle2) / 2)
        ny = math.sin((angle1 + angle2) / 2)
        write_facet(f, (nx, ny, 0), (ox1, oy1, 0), (ox2, oy2, 0), (ox2, oy2, height))
        write_facet(f, (nx, ny, 0), (ox1, oy1, 0), (ox2, oy2, height), (ox1, oy1, height))

        # --- Inner wall, normal points inward (toward center) ---
        write_facet(f, (-nx, -ny, 0), (ix1, iy1, 0), (ix2, iy2, height), (ix2, iy2, 0))
        write_facet(f, (-nx, -ny, 0), (ix1, iy1, 0), (ix1, iy1, height), (ix2, iy2, height))

    f.write("endsolid ascii_model\n")

print(f"Generated circular ring STL: {output_file}")
print(f"  Outer diameter: {outer_radius * 2} mm (7 cm)")
print(f"  Inner diameter: {inner_radius * 2} mm (6 cm)")
print(f"  Height: {height} mm")
print(f"  Segments: {segments}")
