bl_info = {
    "name": "Forest Maze Generator Advanced",
    "author": "Your Name",
    "version": (3, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Forest Maze",
    "description": "Procedural forest maze with collision, fog, and multiple tree variants",
    "category": "Add Mesh",
}

import bpy
import random
import math
from mathutils import Matrix, Vector
import bmesh


COLLECTION_NAME = "FOREST_MAZE_ADVANCED"
TREE_COLLECTION = "FOREST_MAZE_TREES"
VEGETATION_COLLECTION = "FOREST_MAZE_VEGETATION"
LIGHTING_COLLECTION = "FOREST_MAZE_LIGHTING"
COLLISION_COLLECTION = "FOREST_MAZE_COLLISION"
FOG_COLLECTION = "FOREST_MAZE_FOG"


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================

def get_or_create_collection(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def link_object_to_collection(obj, collection_name):
    """Properly link object to collection and remove from others."""
    collection = get_or_create_collection(collection_name)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)


def clear_generated_objects():
    for name in [
        COLLECTION_NAME,
        TREE_COLLECTION,
        VEGETATION_COLLECTION,
        LIGHTING_COLLECTION,
        COLLISION_COLLECTION,
        FOG_COLLECTION,
    ]:
        collection = bpy.data.collections.get(name)
        if collection:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)


# ============================================================
# MATERIALS
# ============================================================

def create_material(name, color, roughness=0.5, metallic=0.0, transmission=0.0, alpha=1.0):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name=name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*color, alpha)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Transmission"].default_value = transmission
    return material


def get_wall_material():
    return create_material("ForestMazeWallMaterial", (0.09, 0.09, 0.09), 0.8, 0.0)


def get_floor_material():
    return create_material("ForestMazeFloorMaterial", (0.08, 0.12, 0.06), 0.9, 0.0)


def get_spawn_material():
    return create_material("ForestSpawnMaterial", (0.18, 0.9, 0.18), 0.3, 0.0)


def get_exit_material():
    return create_material("ForestExitMaterial", (0.9, 0.22, 0.18), 0.3, 0.0)


def get_grass_material():
    return create_material("ForestGrassMaterial", (0.12, 0.35, 0.13), 0.9, 0.0)


def get_sky_material():
    return create_material("ForestSkyMaterial", (0.53, 0.78, 0.92), 0.0, 0.0)


def get_fog_material():
    return create_material("ForestFogMaterial", (0.78, 0.82, 0.86), 0.0, 0.0, 0.25, 0.3)


def assign_material(obj, material):
    if not obj.data:
        return
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


# ============================================================
# MAZE GENERATION
# ============================================================

def init_grid(width, height):
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append({
                "visited": False,
                "room": False,
                "wall_n": True,
                "wall_s": True,
                "wall_e": True,
                "wall_w": True,
            })
        grid.append(row)
    return grid


def in_bounds(grid, x, y):
    return 0 <= x < len(grid[0]) and 0 <= y < len(grid)


def remove_wall_between(grid, x1, y1, x2, y2):
    if x2 == x1 + 1:
        grid[y1][x1]["wall_e"] = False
        grid[y2][x2]["wall_w"] = False
    elif x2 == x1 - 1:
        grid[y1][x1]["wall_w"] = False
        grid[y2][x2]["wall_e"] = False
    elif y2 == y1 + 1:
        grid[y1][x1]["wall_s"] = False
        grid[y2][x2]["wall_n"] = False
    elif y2 == y1 - 1:
        grid[y1][x1]["wall_n"] = False
        grid[y2][x2]["wall_s"] = False


def carve_backtracking(grid, start_x, start_y):
    stack = [(start_x, start_y)]
    grid[start_y][start_x]["visited"] = True

    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    random.shuffle(directions)

    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if in_bounds(grid, nx, ny) and not grid[ny][nx]["visited"]:
                neighbors.append((nx, ny))

        if neighbors:
            nx, ny = random.choice(neighbors)
            remove_wall_between(grid, x, y, nx, ny)
            grid[ny][nx]["visited"] = True
            stack.append((nx, ny))
        else:
            stack.pop()


def generate_base_maze(width, height, seed):
    random.seed(seed)
    width = width if width % 2 == 1 else width + 1
    height = height if height % 2 == 1 else height + 1
    maze = init_grid(width, height)
    carve_backtracking(maze, 1, 1)
    return maze


def generate_rooms(grid, density, min_room_size, max_room_size):
    if density <= 0:
        return

    rows = len(grid)
    cols = len(grid[0])
    room_count = max(1, int((rows * cols) * density / 20))

    safe_cells = []
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):
            if not (grid[y][x]["wall_n"] and grid[y][x]["wall_s"] and grid[y][x]["wall_e"] and grid[y][x]["wall_w"]):
                safe_cells.append((x, y))

    if not safe_cells:
        return

    random.shuffle(safe_cells)
    for cx, cy in safe_cells[:room_count]:
        room_w = random.randint(min_room_size, max_room_size)
        room_h = random.randint(min_room_size, max_room_size)
        x0 = max(1, cx - room_w // 2)
        y0 = max(1, cy - room_h // 2)
        x1 = min(cols - 2, cx + room_w // 2)
        y1 = min(rows - 2, cy + room_h // 2)

        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if in_bounds(grid, x, y):
                    grid[y][x]["room"] = True

        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if x > x0:
                    grid[y][x]["wall_w"] = False
                    grid[y][x - 1]["wall_e"] = False
                if y > y0:
                    grid[y][x]["wall_n"] = False
                    grid[y - 1][x]["wall_s"] = False


# ============================================================
# MESH GENERATION
# ============================================================

def get_grid_world_position(x, y, cell_size, grid_width, grid_height):
    offset_x = (grid_width * cell_size) / 2.0
    offset_y = (grid_height * cell_size) / 2.0
    world_x = x * cell_size - offset_x + (cell_size / 2.0)
    world_y = y * cell_size - offset_y + (cell_size / 2.0)
    return world_x, world_y


def build_box_bmesh(bm, center, size):
    sx, sy, sz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
    local = [
        Vector((-sx, -sy, -sz)),
        Vector((sx, -sy, -sz)),
        Vector((sx, sy, -sz)),
        Vector((-sx, sy, -sz)),
        Vector((-sx, -sy, sz)),
        Vector((sx, -sy, sz)),
        Vector((sx, sy, sz)),
        Vector((-sx, sy, sz)),
    ]
    trans = Matrix.Translation(center)
    verts = [bm.verts.new(trans @ v) for v in local]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]
    for face in faces:
        bm.faces.new([verts[i] for i in face])


def create_wall_mesh(grid, cell_size, wall_height):
    rows = len(grid)
    cols = len(grid[0])
    bm = bmesh.new()

    for y in range(rows):
        for x in range(cols):
            cell = grid[y][x]
            world_x, world_y = get_grid_world_position(x, y, cell_size, cols, rows)

            if cell["wall_n"]:
                build_box_bmesh(bm, Vector((world_x, world_y - cell_size / 2.0, wall_height / 2.0)), (cell_size, 0.12, wall_height))
            if cell["wall_s"]:
                build_box_bmesh(bm, Vector((world_x, world_y + cell_size / 2.0, wall_height / 2.0)), (cell_size, 0.12, wall_height))
            if cell["wall_w"]:
                build_box_bmesh(bm, Vector((world_x - cell_size / 2.0, world_y, wall_height / 2.0)), (0.12, cell_size, wall_height))
            if cell["wall_e"]:
                build_box_bmesh(bm, Vector((world_x + cell_size / 2.0, world_y, wall_height / 2.0)), (0.12, cell_size, wall_height))

    mesh = bpy.data.meshes.new("MazeWallsMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("MazeWalls", mesh)
    link_object_to_collection(obj, COLLECTION_NAME)
    assign_material(obj, get_wall_material())
    return obj


def create_floor_mesh(grid, cell_size):
    rows = len(grid)
    cols = len(grid[0])
    bm = bmesh.new()
    offset_x = (cols * cell_size) / 2.0
    offset_y = (rows * cell_size) / 2.0

    for y in range(rows):
        for x in range(cols):
            cx = x * cell_size - offset_x + cell_size / 2.0
            cy = y * cell_size - offset_y + cell_size / 2.0
            verts = [
                Vector((cx - cell_size / 2.0, cy - cell_size / 2.0, 0.02)),
                Vector((cx + cell_size / 2.0, cy - cell_size / 2.0, 0.02)),
                Vector((cx + cell_size / 2.0, cy + cell_size / 2.0, 0.02)),
                Vector((cx - cell_size / 2.0, cy + cell_size / 2.0, 0.02)),
            ]
            vtx = [bm.verts.new(v) for v in verts]
            bm.faces.new(vtx)

    mesh = bpy.data.meshes.new("MazeFloorMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("MazeFloor", mesh)
    link_object_to_collection(obj, COLLECTION_NAME)
    assign_material(obj, get_floor_material())
    return obj


def create_ground_plane(width, height, cell_size):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, -0.1))
    obj = bpy.context.object
    obj.name = "MazeGround"
    obj.scale = ((width * cell_size) / 2.0, (height * cell_size) / 2.0, 1.0)
    assign_material(obj, get_grass_material())
    link_object_to_collection(obj, COLLECTION_NAME)
    return obj


# ============================================================
# COLLISION MESH (B)
# ============================================================

def create_collision_mesh(grid, cell_size):
    rows = len(grid)
    cols = len(grid[0])
    bm = bmesh.new()
    offset_x = (cols * cell_size) / 2.0
    offset_y = (rows * cell_size) / 2.0

    for y in range(rows):
        for x in range(cols):
            if grid[y][x]["wall_n"]:
                cx = x * cell_size - offset_x + (cell_size / 2.0)
                cy = y * cell_size - offset_y + (cell_size / 2.0) - (cell_size / 2.0)
                verts = [
                    Vector((cx - cell_size / 2.0, cy - 0.05, 0.0)),
                    Vector((cx + cell_size / 2.0, cy - 0.05, 0.0)),
                    Vector((cx + cell_size / 2.0, cy + 0.05, 0.0)),
                    Vector((cx - cell_size / 2.0, cy + 0.05, 0.0)),
                    Vector((cx - cell_size / 2.0, cy - 0.05, 3.0)),
                    Vector((cx + cell_size / 2.0, cy - 0.05, 3.0)),
                    Vector((cx + cell_size / 2.0, cy + 0.05, 3.0)),
                    Vector((cx - cell_size / 2.0, cy + 0.05, 3.0)),
                ]
                vtx = [bm.verts.new(v) for v in verts]
                bm.faces.new([vtx[0], vtx[1], vtx[2], vtx[3]])
                bm.faces.new([vtx[4], vtx[5], vtx[6], vtx[7]])
                bm.faces.new([vtx[0], vtx[4], vtx[5], vtx[1]])
                bm.faces.new([vtx[1], vtx[5], vtx[6], vtx[2]])
                bm.faces.new([vtx[2], vtx[6], vtx[7], vtx[3]])
                bm.faces.new([vtx[3], vtx[7], vtx[4], vtx[0]])

            if grid[y][x]["wall_w"]:
                cx = x * cell_size - offset_x + (cell_size / 2.0) - (cell_size / 2.0)
                cy = y * cell_size - offset_y + (cell_size / 2.0)
                verts = [
                    Vector((cx - 0.05, cy - cell_size / 2.0, 0.0)),
                    Vector((cx + 0.05, cy - cell_size / 2.0, 0.0)),
                    Vector((cx + 0.05, cy + cell_size / 2.0, 0.0)),
                    Vector((cx - 0.05, cy + cell_size / 2.0, 0.0)),
                    Vector((cx - 0.05, cy - cell_size / 2.0, 3.0)),
                    Vector((cx + 0.05, cy - cell_size / 2.0, 3.0)),
                    Vector((cx + 0.05, cy + cell_size / 2.0, 3.0)),
                    Vector((cx - 0.05, cy + cell_size / 2.0, 3.0)),
                ]
                vtx = [bm.verts.new(v) for v in verts]
                bm.faces.new([vtx[0], vtx[1], vtx[2], vtx[3]])
                bm.faces.new([vtx[4], vtx[5], vtx[6], vtx[7]])
                bm.faces.new([vtx[0], vtx[4], vtx[5], vtx[1]])
                bm.faces.new([vtx[1], vtx[5], vtx[6], vtx[2]])
                bm.faces.new([vtx[2], vtx[6], vtx[7], vtx[3]])
                bm.faces.new([vtx[3], vtx[7], vtx[4], vtx[0]])

    mesh = bpy.data.meshes.new("MazeCollisionMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("MazeCollision", mesh)
    link_object_to_collection(obj, COLLISION_COLLECTION)
    obj.hide_render = True
    return obj


# ============================================================
# FOG VOLUME (D)
# ============================================================

def create_fog_volume(width, height, cell_size, fog_density=0.15):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 4.0))
    fog = bpy.context.object
    fog.name = "ForestFogVolume"
    fog.scale = ((width * cell_size) * 1.5, (height * cell_size) * 1.5, 10.0)

    mat = get_fog_material()
    fog.data.materials.clear()
    fog.data.materials.append(mat)
    fog.hide_render = False

    if fog.data.materials:
        material = fog.data.materials[0]
        material.blend_method = 'BLEND'
        material.shadow_method = 'HASHED'

    link_object_to_collection(fog, FOG_COLLECTION)
    return fog


# ============================================================
# MULTI TREE TYPES (E)
# ============================================================

def make_pine_tree(location, trunk_height, trunk_radius, foliage_radius):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6,
        radius=trunk_radius,
        depth=trunk_height,
        location=(location[0], location[1], location[2] + trunk_height / 2.0)
    )
    trunk = bpy.context.object
    trunk.name = "PineTrunk"
    trunk.data.materials.clear()
    trunk.data.materials.append(create_material("PineBark", (0.27, 0.20, 0.12), 0.9, 0.0))
    link_object_to_collection(trunk, TREE_COLLECTION)

    for i, scale in enumerate([1.6, 1.2, 0.9]):
        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=foliage_radius * scale,
            radius2=0.0,
            depth=foliage_radius * 1.8,
            location=(location[0], location[1], location[2] + trunk_height + foliage_radius * (i + 1))
        )
        cone = bpy.context.object
        cone.name = f"PineCone_{i}"
        cone.data.materials.clear()
        cone.data.materials.append(create_material(f"PineFoliage_{i}", (0.10, 0.35, 0.14), 0.7, 0.0))
        link_object_to_collection(cone, TREE_COLLECTION)

    return trunk


def make_oak_tree(location, trunk_height, trunk_radius, foliage_radius):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=trunk_radius,
        depth=trunk_height,
        location=(location[0], location[1], location[2] + trunk_height / 2.0)
    )
    trunk = bpy.context.object
    trunk.name = "OakTrunk"
    trunk.data.materials.clear()
    trunk.data.materials.append(create_material("OakBark", (0.24, 0.17, 0.10), 0.8, 0.0))
    link_object_to_collection(trunk, TREE_COLLECTION)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=foliage_radius, location=(location[0], location[1], location[2] + trunk_height + foliage_radius * 0.8))
    sphere = bpy.context.object
    sphere.data.materials.clear()
    sphere.data.materials.append(create_material("OakFoliage", (0.18, 0.42, 0.18), 0.6, 0.0))
    link_object_to_collection(sphere, TREE_COLLECTION)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=foliage_radius * 0.7, location=(location[0] + foliage_radius * 0.5, location[1], location[2] + trunk_height + foliage_radius * 0.4))
    sphere2 = bpy.context.object
    sphere2.data.materials.clear()
    sphere2.data.materials.append(create_material("OakFoliage2", (0.18, 0.42, 0.18), 0.6, 0.0))
    link_object_to_collection(sphere2, TREE_COLLECTION)

    return trunk


def make_birch_tree(location, trunk_height, trunk_radius, foliage_radius):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=trunk_radius,
        depth=trunk_height,
        location=(location[0], location[1], location[2] + trunk_height / 2.0)
    )
    trunk = bpy.context.object
    trunk.name = "BirchTrunk"
    trunk.data.materials.clear()
    trunk.data.materials.append(create_material("BirchBark", (0.78, 0.75, 0.68), 0.8, 0.0))
    link_object_to_collection(trunk, TREE_COLLECTION)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=foliage_radius, location=(location[0], location[1], location[2] + trunk_height + foliage_radius * 0.6))
    sphere = bpy.context.object
    sphere.data.materials.clear()
    sphere.data.materials.append(create_material("BirchFoliage", (0.20, 0.52, 0.18), 0.7, 0.0))
    link_object_to_collection(sphere, TREE_COLLECTION)

    return trunk


def create_tree_variant(location, variant_name, trunk_height, trunk_radius, foliage_radius):
    variant_map = {
        "pine": make_pine_tree,
        "oak": make_oak_tree,
        "birch": make_birch_tree,
    }
    fn = variant_map.get(variant_name, make_oak_tree)
    return fn(location, trunk_height, trunk_radius, foliage_radius)


def scatter_trees(grid, cell_size, tree_density, min_height, max_height, allow_variants=True):
    rows = len(grid)
    cols = len(grid[0])
    radius = max(rows, cols) * cell_size * 0.7
    tree_count = max(10, int(tree_density * rows * cols / 8))

    variants = ["pine", "oak", "birch"]

    for _ in range(tree_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(radius * 0.4, radius)
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        z = 0.0

        trunk_height = random.uniform(min_height, max_height)
        trunk_radius = random.uniform(0.12, 0.25)
        foliage_radius = random.uniform(trunk_height * 0.25, trunk_height * 0.45)

        variant = random.choice(variants) if allow_variants else "oak"
        create_tree_variant((x, y, z), variant, trunk_height, trunk_radius, foliage_radius)


# ============================================================
# SKY / LIGHTING
# ============================================================

def create_sky_dome():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=250, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "ForestSky"
    assign_material(obj, get_sky_material())
    link_object_to_collection(obj, COLLECTION_NAME)
    return obj


def create_lighting():
    bpy.ops.object.light_add(type='SUN', location=(50, 40, 60))
    sun = bpy.context.object
    sun.name = "ForestSun"
    sun.data.energy = 2.0
    sun.data.angle = math.radians(3)
    link_object_to_collection(sun, LIGHTING_COLLECTION)

    bpy.ops.object.light_add(type='AREA', location=(0, 0, 25))
    area = bpy.context.object
    area.name = "ForestAreaFill"
    area.data.energy = 0.9
    area.data.shape = 'RECTANGLE'
    area.data.size = 40
    area.data.size_y = 40
    link_object_to_collection(area, LIGHTING_COLLECTION)

    return sun, area


# ============================================================
# MARKERS
# ============================================================

def create_marker(name, location, radius, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=0.12, location=location)
    obj = bpy.context.object
    obj.name = name
    assign_material(obj, material)
    link_object_to_collection(obj, COLLECTION_NAME)
    return obj


def create_player_exit_markers(grid, cell_size):
    rows = len(grid)
    cols = len(grid[0])
    offset_x = (cols * cell_size) / 2.0
    offset_y = (rows * cell_size) / 2.0

    spawn = None
    exit_cell = None

    for y in range(rows):
        for x in range(cols):
            if not (grid[y][x]["wall_n"] and grid[y][x]["wall_s"] and grid[y][x]["wall_e"] and grid[y][x]["wall_w"]):
                spawn = (x, y)
                break
        if spawn:
            break

    for y in range(rows - 1, -1, -1):
        for x in range(cols - 1, -1, -1):
            if not (grid[y][x]["wall_n"] and grid[y][x]["wall_s"] and grid[y][x]["wall_e"] and grid[y][x]["wall_w"]):
                exit_cell = (x, y)
                break
        if exit_cell:
            break

    if spawn:
        sx, sy = spawn
        loc = (sx * cell_size - offset_x + cell_size / 2.0, sy * cell_size - offset_y + cell_size / 2.0, 0.08)
        spawn_obj = create_marker("MAZE_PLAYER_SPAWN", loc, 0.35, get_spawn_material())
        spawn_obj["maze_role"] = "player_spawn"

    if exit_cell:
        ex, ey = exit_cell
        loc = (ex * cell_size - offset_x + cell_size / 2.0, ey * cell_size - offset_y + cell_size / 2.0, 0.08)
        exit_obj = create_marker("MAZE_EXIT", loc, 0.35, get_exit_material())
        exit_obj["maze_role"] = "exit"


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_forest_maze(scene):
    clear_generated_objects()

    maze = generate_base_maze(
        max(5, scene.forest_advanced_width),
        max(5, scene.forest_advanced_height),
        scene.forest_advanced_seed
    )

    if scene.forest_advanced_use_rooms:
        generate_rooms(
            maze,
            scene.forest_advanced_room_density,
            scene.forest_advanced_room_min_size,
            scene.forest_advanced_room_max_size
        )

    create_wall_mesh(maze, scene.forest_advanced_cell_size, scene.forest_advanced_wall_height)
    create_floor_mesh(maze, scene.forest_advanced_cell_size)
    create_ground_plane(len(maze[0]), len(maze), scene.forest_advanced_cell_size)

    if scene.forest_advanced_create_collision:
        create_collision_mesh(maze, scene.forest_advanced_cell_size)

    if scene.forest_advanced_create_fog:
        create_fog_volume(len(maze[0]), len(maze), scene.forest_advanced_cell_size, scene.forest_advanced_fog_density)

    if scene.forest_advanced_create_trees:
        scatter_trees(
            maze,
            scene.forest_advanced_cell_size,
            scene.forest_advanced_tree_density,
            scene.forest_advanced_tree_min_height,
            scene.forest_advanced_tree_max_height,
            scene.forest_advanced_tree_variants
        )

    if scene.forest_advanced_create_markers:
        create_player_exit_markers(maze, scene.forest_advanced_cell_size)

    if scene.forest_advanced_create_lighting:
        create_lighting()

    if scene.forest_advanced_create_sky:
        create_sky_dome()


# ============================================================
# OPERATORS
# ============================================================

class FORESTADVANCED_OT_generate(bpy.types.Operator):
    bl_idname = "forestadvanced.generate"
    bl_label = "Generate Forest Maze"
    bl_description = "Generate a forest maze with collision, fog, and multiple tree types"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        generate_forest_maze(context.scene)
        self.report({"INFO"}, "Forest maze generated successfully!")
        return {"FINISHED"}


class FORESTADVANCED_OT_clear(bpy.types.Operator):
    bl_idname = "forestadvanced.clear"
    bl_label = "Clear Forest Maze"
    bl_description = "Remove all generated maze geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_generated_objects()
        self.report({"INFO"}, "Forest maze cleared")
        return {"FINISHED"}


# ============================================================
# PANEL
# ============================================================

class FORESTADVANCED_PT_panel(bpy.types.Panel):
    bl_label = "Forest Maze Advanced"
    bl_idname = "FORESTADVANCED_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Forest Maze"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="Maze Settings", icon="GRID")
        box.prop(scene, "forest_advanced_width")
        box.prop(scene, "forest_advanced_height")
        box.prop(scene, "forest_advanced_seed")
        box.prop(scene, "forest_advanced_cell_size")
        box.prop(scene, "forest_advanced_wall_height")

        box = layout.box()
        box.label(text="Room Layout", icon="MODIFIER")
        box.prop(scene, "forest_advanced_use_rooms")
        if scene.forest_advanced_use_rooms:
            box.prop(scene, "forest_advanced_room_density")
            box.prop(scene, "forest_advanced_room_min_size")
            box.prop(scene, "forest_advanced_room_max_size")

        box = layout.box()
        box.label(text="Collision & Fog", icon="PHYSICS")
        box.prop(scene, "forest_advanced_create_collision")
        box.prop(scene, "forest_advanced_create_fog")
        if scene.forest_advanced_create_fog:
            box.prop(scene, "forest_advanced_fog_density")

        box = layout.box()
        box.label(text="Forest", icon="WORLD_DATA")
        box.prop(scene, "forest_advanced_create_trees")
        if scene.forest_advanced_create_trees:
            box.prop(scene, "forest_advanced_tree_density")
            box.prop(scene, "forest_advanced_tree_min_height")
            box.prop(scene, "forest_advanced_tree_max_height")
            box.prop(scene, "forest_advanced_tree_variants")

        box = layout.box()
        box.label(text="Environment", icon="OUTLINER_OB_LIGHT")
        box.prop(scene, "forest_advanced_create_lighting")
        box.prop(scene, "forest_advanced_create_sky")
        box.prop(scene, "forest_advanced_create_markers")

        layout.separator()
        row = layout.row()
        row.scale_y = 1.8
        row.operator("forestadvanced.generate", icon="PLAY", text="Generate Forest Maze")

        row = layout.row()
        row.operator("forestadvanced.clear", icon="TRASH")


# ============================================================
# REGISTRATION
# ============================================================

classes = (
    FORESTADVANCED_OT_generate,
    FORESTADVANCED_OT_clear,
    FORESTADVANCED_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Maze
    bpy.types.Scene.forest_advanced_width = bpy.props.IntProperty(name="Width", default=17, min=5, max=101)
    bpy.types.Scene.forest_advanced_height = bpy.props.IntProperty(name="Height", default=17, min=5, max=101)
    bpy.types.Scene.forest_advanced_seed = bpy.props.IntProperty(name="Seed", default=12345)
    bpy.types.Scene.forest_advanced_cell_size = bpy.props.FloatProperty(name="Cell Size", default=2.5, min=0.5, max=20.0)
    bpy.types.Scene.forest_advanced_wall_height = bpy.props.FloatProperty(name="Wall Height", default=2.8, min=0.1, max=30.0)

    # Rooms
    bpy.types.Scene.forest_advanced_use_rooms = bpy.props.BoolProperty(name="Use Rooms", default=True)
    bpy.types.Scene.forest_advanced_room_density = bpy.props.FloatProperty(name="Room Density", default=0.35, min=0.05, max=1.0)
    bpy.types.Scene.forest_advanced_room_min_size = bpy.props.IntProperty(name="Room Min Size", default=1, min=1, max=8)
    bpy.types.Scene.forest_advanced_room_max_size = bpy.props.IntProperty(name="Room Max Size", default=4, min=2, max=12)

    # Collision / Fog
    bpy.types.Scene.forest_advanced_create_collision = bpy.props.BoolProperty(name="Create Collision Mesh", default=True)
    bpy.types.Scene.forest_advanced_create_fog = bpy.props.BoolProperty(name="Create Fog Volume", default=True)
    bpy.types.Scene.forest_advanced_fog_density = bpy.props.FloatProperty(name="Fog Density", default=0.15, min=0.01, max=1.0)

    # Trees
    bpy.types.Scene.forest_advanced_create_trees = bpy.props.BoolProperty(name="Create Trees", default=True)
    bpy.types.Scene.forest_advanced_tree_density = bpy.props.FloatProperty(name="Tree Density", default=0.8, min=0.1, max=2.5)
    bpy.types.Scene.forest_advanced_tree_min_height = bpy.props.FloatProperty(name="Tree Min Height", default=4.0, min=1.0, max=20.0)
    bpy.types.Scene.forest_advanced_tree_max_height = bpy.props.FloatProperty(name="Tree Max Height", default=12.0, min=2.0, max=30.0)
    bpy.types.Scene.forest_advanced_tree_variants = bpy.props.BoolProperty(name="Use Tree Variants", default=True)

    # Environment
    bpy.types.Scene.forest_advanced_create_lighting = bpy.props.BoolProperty(name="Create Lighting", default=True)
    bpy.types.Scene.forest_advanced_create_sky = bpy.props.BoolProperty(name="Create Sky", default=True)
    bpy.types.Scene.forest_advanced_create_markers = bpy.props.BoolProperty(name="Create Spawn / Exit", default=True)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    props = [
        "forest_advanced_width", "forest_advanced_height", "forest_advanced_seed",
        "forest_advanced_cell_size", "forest_advanced_wall_height",
        "forest_advanced_use_rooms", "forest_advanced_room_density",
        "forest_advanced_room_min_size", "forest_advanced_room_max_size",
        "forest_advanced_create_collision", "forest_advanced_create_fog",
        "forest_advanced_fog_density", "forest_advanced_create_trees",
        "forest_advanced_tree_density", "forest_advanced_tree_min_height",
        "forest_advanced_tree_max_height", "forest_advanced_tree_variants",
        "forest_advanced_create_lighting", "forest_advanced_create_sky",
        "forest_advanced_create_markers",
    ]
    for prop in props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)


if __name__ == "__main__":
    register()
