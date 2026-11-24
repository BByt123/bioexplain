"""Build and frame an editable desk lamp in the current Blender scene."""

from math import cos, sin, tau


FINISHES = {
    "Matte Charcoal": ("34383B", 0.82),
    "Dark Charcoal": ("24272A", 0.84),
    "Graphite Hardware": ("53595E", 0.72),
    "Warm Yellow": ("F6B93F", 0.72),
    "Shade Lining": ("F6DA91", 0.84),
    "Frosted Diffuser": ("FFF1CD", 0.48),
}

BASE_PIVOT = (-0.30, 0.0, 0.36)
ELBOW = (-0.72, 0.0, 1.58)
HEAD_PIVOT = (0.65, 0.0, 2.45)
SHADE_AXIS = (0.60, 0.0, -0.80)
HINGE_AXIS = (0.0, 1.0, 0.0)
UP = (0.0, 0.0, 1.0)
VIEW_DIRECTION = (1.72, -2.55, 0.64)
VIEW_CENTER = (0.35, 0.0, 1.29)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(v, factor):
    return tuple(component * factor for component in v)


def subtract(a, b):
    return add(a, scale(b, -1))


def cross(a, b):
    x, y, z = a
    i, j, k = b
    return (y * k - z * j, z * i - x * k, x * j - y * i)


def ring_mesh(rings):
    sides = len(rings[0])
    vertices = [vertex for ring in rings for vertex in ring]
    faces = [tuple(reversed(range(sides)))]
    for start in range(0, len(vertices) - sides, sides):
        for index in range(sides):
            next_index = (index + 1) % sides
            faces.append((start + index, start + next_index,
                          start + sides + next_index, start + sides + index))
    faces.append(tuple(range(len(vertices) - sides, len(vertices))))
    return vertices, faces


def turned(center, axis, profile, sides):
    u = (1.0, 0.0, 0.0) if axis == HINGE_AXIS else HINGE_AXIS
    v = cross(axis, u)
    angles = [tau * index / sides for index in range(sides)]
    directions = [add(scale(u, cos(angle)), scale(v, sin(angle))) for angle in angles]
    return ring_mesh([
        [add(add(center, scale(axis, distance)), scale(direction, radius))
         for direction in directions]
        for distance, radius in profile
    ])


def arm_link(start, end, width, depth):
    delta = subtract(end, start)
    axis = scale(delta, sum(value * value for value in delta) ** -0.5)
    across = cross(axis, HINGE_AXIS)
    half_depth, half_width = depth / 2, width / 2
    bevel = 0.025
    section = [
        (half_depth, half_width - bevel), (half_depth - bevel, half_width),
        (-half_depth + bevel, half_width), (-half_depth, half_width - bevel),
        (-half_depth, -half_width + bevel), (-half_depth + bevel, -half_width),
        (half_depth - bevel, -half_width), (half_depth, -half_width + bevel),
    ]
    return ring_mesh([
        [add(add(center, scale(HINGE_AXIS, y * taper)), scale(across, x * taper))
         for y, x in section]
        for center, taper in ((start, 0.96), (add(start, scale(axis, 0.12)), 1.0),
                              (add(end, scale(axis, -0.12)), 0.92), (end, 0.86))
    ])


def lamp_parts():
    parts = []

    def mesh(name, finish, geometry, parent=None, origin=(0.0, 0.0, 0.0), lining=0):
        vertices, faces = geometry
        parts.append((name, finish, vertices, faces, parent, origin, lining))

    def lathe(name, finish, center, axis, profile, sides, parent=None):
        mesh(name, finish, turned(center, axis, profile, sides), parent, center)

    lathe("Round Base", "Matte Charcoal", (0, 0, 0), UP,
          [(0.025, 0.77), (0.061, 0.825), (0.15, 0.825), (0.207, 0.763)], 24)
    lathe("Base Foot", "Dark Charcoal", (0, 0, 0), UP,
          [(0.0, 0.715), (0.014, 0.76), (0.043, 0.76)], 24, "Round Base")
    lathe("Pivot Pedestal", "Matte Charcoal", (-0.30, 0, 0), UP,
          [(0.201, 0.202), (0.232, 0.202), (0.334, 0.127), (0.36, 0.119)],
          16, "Round Base")
    lathe("Switch Collar", "Dark Charcoal", (0.43, 0, 0), UP,
          [(0.205, 0.105), (0.218, 0.108), (0.235, 0.096)], 12, "Round Base")
    lathe("Power Switch", "Graphite Hardware", (0.43, 0, 0), UP,
          [(0.222, 0.076), (0.254, 0.076), (0.268, 0.066)], 12, "Round Base")

    mesh("Lower Arm", "Matte Charcoal", arm_link(BASE_PIVOT, ELBOW, 0.25, 0.22),
         "Round Base", BASE_PIVOT)
    mesh("Upper Arm", "Matte Charcoal", arm_link(ELBOW, HEAD_PIVOT, 0.217, 0.208),
         "Lower Arm", ELBOW)
    for label, center, radius, parent in (
        ("Base", BASE_PIVOT, 0.150, "Round Base"),
        ("Elbow", ELBOW, 0.180, "Lower Arm"),
        ("Shade", HEAD_PIVOT, 0.134, "Upper Arm"),
    ):
        lathe(f"{label} Hinge", "Matte Charcoal", center, HINGE_AXIS,
              [(-0.158, radius * 0.88), (-0.130, radius), (0.130, radius),
               (0.158, radius * 0.88)], 16, parent)
        for side, offset in (("Front", -1), ("Back", 1)):
            profile = sorted([(offset * 0.155, radius * 0.52),
                              (offset * 0.172, radius * 0.52),
                              (offset * 0.179, radius * 0.43)])
            lathe(f"{label} Hinge Pin {side}", "Graphite Hardware", center,
                  HINGE_AXIS, profile, 12, parent)

    shade_profile = [
        (0.152, 0.153), (0.19, 0.199), (0.76, 0.524),
        (0.809, 0.548), (0.831, 0.538), (0.836, 0.507),
        (0.79, 0.486), (0.23, 0.162), (0.208, 0.127),
    ]
    mesh("Cone Shade", "Warm Yellow", turned(HEAD_PIVOT, SHADE_AXIS, shade_profile, 20),
         "Upper Arm", HEAD_PIVOT, 1 + 5 * 20)
    lathe("Shade Collar", "Matte Charcoal", HEAD_PIVOT, SHADE_AXIS,
          [(0.055, 0.112), (0.113, 0.149), (0.195, 0.149)], 16, "Cone Shade")
    lathe("Frosted Diffuser", "Frosted Diffuser", HEAD_PIVOT, SHADE_AXIS,
          [(0.204, 0.071), (0.305, 0.071), (0.33, 0.095),
           (0.38, 0.132), (0.54, 0.164), (0.61, 0.156),
           (0.68, 0.106), (0.70, 0.058)], 16, "Cone Shade")
    return parts


def linear_color(color):
    rgb = [int(color[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    return tuple(value / 12.92 if value <= 0.04045 else
                 ((value + 0.055) / 1.055) ** 2.4 for value in rgb)


def build_lamp():
    import bpy
    from mathutils import Vector

    scene = bpy.context.scene
    collection = bpy.data.collections.get("Desk Lamp")
    if collection is not None and collection.get("desk_lamp_model"):
        raise RuntimeError("This file already contains the Desk Lamp model.")
    if collection is None:
        collection = bpy.data.collections.new("Desk Lamp")
    if collection not in scene.collection.children_recursive:
        scene.collection.children.link(collection)
    collection["desk_lamp_model"] = True

    materials = {}
    for name, (color, roughness) in FINISHES.items():
        material = bpy.data.materials.new(name)
        material.diffuse_color = (*linear_color(color), 1)
        material.roughness = roughness
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = material.diffuse_color
        shader.inputs["Roughness"].default_value = roughness
        materials[name] = material

    objects = {}
    for name, finish, vertices, faces, parent, origin, lining in lamp_parts():
        geometry = bpy.data.meshes.new(name)
        geometry.from_pydata([subtract(vertex, origin) for vertex in vertices], [], faces)
        geometry.update()
        obj = bpy.data.objects.new(name, geometry)
        collection.objects.link(obj)
        geometry.materials.append(materials[finish])
        if lining:
            geometry.materials.append(materials["Shade Lining"])
            for polygon in list(geometry.polygons)[lining:]:
                polygon.material_index = 1
        if parent is None:
            obj.location = origin
        else:
            parent_obj, parent_origin = objects[parent]
            obj.parent = parent_obj
            obj.location = subtract(origin, parent_origin)
        objects[name] = (obj, origin)

    bpy.context.view_layer.update()
    if bpy.context.screen is not None:
        for area in bpy.context.screen.areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'
                    space.shading.color_type = 'MATERIAL'
                    space.region_3d.view_perspective = 'ORTHO'
                    space.region_3d.view_rotation = Vector(VIEW_DIRECTION).to_track_quat('Z', 'Y')
                    space.region_3d.view_location = VIEW_CENTER
                    space.region_3d.view_distance = 5.2
            area.tag_redraw()
    return collection


if __name__ == "__main__":
    build_lamp()
