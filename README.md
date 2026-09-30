# Professional 3D Maze Generator for Blender

A production-ready Blender addon that generates fully 3D, walkable mazes with advanced features including room/corridor generation, procedural wall meshes, player spawning, and AI pathfinding support.

## Features

### Core Features
- **Recursive Backtracking Algorithm**: Perfect maze generation with single solution paths
- **Odd-dimension maze support**: Automatically handles dimensions for proper maze generation
- **Procedural wall meshes**: True 3D walls built with BMesh for editing and customization
- **Floor generation**: Optional procedural floor plane
- **Player spawn markers**: Automatic spawn point placement at maze entrance
- **Exit markers**: Visual markers for maze exit points

### Advanced Features
- **Room & Corridor Generation**: Create distinct rooms connected by corridors
- **BMesh-based geometry**: True procedural mesh generation for advanced editing
- **Game-ready features**: 
  - Player spawn and camera points
  - Enemy patrol path generation
  - Navigation mesh (navmesh) generation
  - Collision-ready geometry
- **Material system**: Pre-configured materials for walls, floors, spawn points, and exits
- **Collection management**: Auto-organized maze objects in Blender collections
- **Customizable parameters**:
  - Maze dimensions (width × height)
  - Cell size (world scale)
  - Wall height and thickness
  - Room size ratios
  - Random seed (reproducible generation)

## Installation

1. Clone or download this repository
2. Copy the `maze_generator` folder to your Blender addons directory:
   - **Linux/Mac**: `~/.config/blender/[version]/scripts/addons/`
   - **Windows**: `%appdata%\Blender Foundation\Blender\[version]\scripts\addons\`
3. Open Blender, go to Edit → Preferences → Add-ons
4. Search for "Maze Generator" and enable it
5. The panel appears in the View3D sidebar under "Maze Generator" tab

## Usage

### Basic Maze Generation
1. Open the Maze Generator panel (View3D → Sidebar → Maze Generator)
2. Configure settings:
   - **Width/Height**: Maze dimensions (cells)
   - **Cell Size**: World space size per cell
   - **Wall Height**: Height of walls (recommended: 2.5-3.0 for first-person)
   - **Wall Thickness**: Thickness of wall segments
   - **Seed**: Random seed (0 = random, any other value = reproducible)
3. Click **Generate Maze**
4. Optionally click **Clear Maze** to remove all generated objects

### Room & Corridor Maze
1. Enable "Advanced Mode" in the panel
2. Set "Room Density" (0.1-0.9) to control room frequency
3. Configure room size constraints
4. Click "Generate Room Maze"

### Game-Ready Setup
1. Enable "Game Mode" for:
   - Automatic player camera spawn point
   - Enemy patrol path generation
   - Navigation mesh for AI pathfinding
2. Click "Generate Maze"
3. Use the generated spawn markers and navmesh for player/AI setup

## Generated Objects

- **MazeWalls**: Main wall mesh (BMesh-based, fully editable)
- **MazeFloor**: Floor plane (optional)
- **MAZE_PLAYER_SPAWN**: Player spawn marker (cylinder)
- **MAZE_EXIT**: Exit marker (cylinder)
- **MazeNavMesh**: Navigation mesh for AI (if Game Mode enabled)
- **MAZE_PATROL_PATHS**: Bezier curve with enemy patrol waypoints

## Technical Details

### Maze Algorithm
The addon uses **Recursive Backtracking** (Depth-First Search) to generate perfect mazes:
- Starts at (1,1) in an all-walls grid
- Randomly carves passages by removing walls between cells
- Generates 1 entrance and 1 exit with guarantee of solvability

### Room Generation
Advanced room+corridor mode:
- Divides maze into regions
- Creates rectangular rooms at intervals
- Connects rooms with corridors
- Maintains single-solution guarantee

### BMesh Implementation
Walls are generated using Blender's BMesh API for:
- True 3D extrusion and beveling
- Post-generation editing (loop cuts, bevels, etc.)
- Better performance than primitive objects
- UV-mapping ready for texturing

### Navigation Mesh
- Automatically generated from floor cells
- Ready for use with Blender's game engine or third-party AI
- Supports enemy pathfinding visualization

## Parameters Explained

| Parameter | Range | Default | Notes |
|-----------|-------|---------|-------|
| Width | 5-101 | 17 | Must be odd for perfect maze |
| Height | 5-101 | 17 | Must be odd for perfect maze |
| Cell Size | 0.5-20.0 | 2.0 | World units per cell |
| Wall Height | 0.1-50.0 | 2.8 | Recommended: 2.5-3.0 for first-person |
| Wall Thickness | 0.02-2.0 | 0.18 | Affects wall appearance |
| Seed | Any int | 12345 | 0 = random, else reproducible |
| Room Density | 0.1-0.9 | 0.5 | Advanced mode: % of cells as rooms |

## Advanced Features Documentation

### Player Spawn Setup
- MAZE_PLAYER_SPAWN marker is placed at maze entrance
- Position this or use its location for player camera placement
- Small cylinder (0.35 radius) for visibility during development

### Enemy Patrol Paths
- MAZE_PATROL_PATHS Bezier curve generated in Game Mode
- Use curve modifier on enemy characters to follow patrol route
- Waypoints auto-spaced through maze corridors
- Edit curve handles to customize patrol behavior

### Navigation Mesh
- MazeNavMesh represents walkable floor areas
- Can be used with Blender Game Engine or exported to game engines
- Supports path queries for AI navigation
- One face per floor cell for simple pathfinding

## Performance Notes

- Large mazes (>50x50) may take a few seconds to generate
- Wall mesh optimization: Consider using face simplification for very large mazes
- NavMesh generation scales linearly with maze floor area
- Procedural generation is one-time cost; editing is instant after generation

## Customization & Extension

### Adding Custom Materials
Edit `materials.py` to add your own wall/floor materials:
```python
def get_custom_material():
    return create_material("CustomWall", (r, g, b))
```

### Modifying Maze Algorithm
Edit `generator.py` to implement different algorithms:
- Prim's algorithm (minimum spanning tree)
- Kruskal's algorithm
- Eller's algorithm

### Adding Custom Geometry
Extend `mesh.py` to add:
- Doors and openings
- Ceiling geometry
- Pillars and columns
- Custom wall textures

## Troubleshooting

**Issue**: Maze doesn't generate
- Check that width/height are positive integers
- Ensure seed value is valid
- Look for error messages in Blender's system console

**Issue**: Walls are disconnected or have gaps
- This is normal with recursive backtracking (single-solution guarantee)
- Check wall thickness isn't too small relative to cell size

**Issue**: Performance is slow
- Reduce maze dimensions
- Disable floor and markers if not needed
- Use lower room density in advanced mode

**Issue**: NavMesh doesn't match floor
- Regenerate maze (navmesh is recalculated)
- Check that "Game Mode" is enabled

## Future Roadmap

- [ ] Multiple maze algorithms (Prim's, Kruskal's, Eller's)
- [ ] 3D multi-level mazes
- [ ] Door and opening system
- [ ] Ceiling and roof generation
- [ ] Texture atlas support
- [ ] Export to common game engines (Unity, Unreal, Godot)
- [ ] Real-time maze solving visualization
- [ ] Difficulty levels (maze complexity)
- [ ] Preset maze templates

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Submit a pull request

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation above

## Credits

Created as a professional Blender addon for procedural game level generation.

---

**Version**: 2.0.0  
**Blender Version**: 3.0+  
**Last Updated**: 2025
