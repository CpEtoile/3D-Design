import struct
from pathlib import Path

# Input binary STL
input_path = Path("data/cover2.stl")

# Output ASCII STL
output_path = Path("cover2.stl_ascii.stl")

# -----------------------------
# Read binary STL
# -----------------------------

with open(input_path, "rb") as f:

    # 80-byte header
    header = f.read(80)

    # Number of triangles
    triangle_count = struct.unpack("<I", f.read(4))[0]

    triangles = []

    for _ in range(triangle_count):

        # Each triangle = 50 bytes
        data = f.read(50)

        # Skip incomplete data
        if len(data) < 50:
            break

        # Binary STL format:
        # 12 floats + 1 unsigned short
        values = struct.unpack("<12fH", data)

        normal = values[0:3]

        v1 = values[3:6]
        v2 = values[6:9]
        v3 = values[9:12]

        triangles.append((normal, v1, v2, v3))

# -----------------------------
# Write ASCII STL
# -----------------------------

with open(output_path, "w") as out:

    out.write("solid ascii_model\n")

    for normal, v1, v2, v3 in triangles:

        out.write(
            f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n"
        )

        out.write("    outer loop\n")

        out.write(
            f"      vertex {v1[0]} {v1[1]} {v1[2]}\n"
        )

        out.write(
            f"      vertex {v2[0]} {v2[1]} {v2[2]}\n"
        )

        out.write(
            f"      vertex {v3[0]} {v3[1]} {v3[2]}\n"
        )

        out.write("    endloop\n")
        out.write("  endfacet\n")

    out.write("endsolid ascii_model\n")

print("Conversion complete.")
print(f"ASCII STL saved to: {output_path}")