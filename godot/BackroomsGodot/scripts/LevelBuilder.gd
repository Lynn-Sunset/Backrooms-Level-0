class_name LevelBuilder
extends RefCounted

## 程序化关卡构建器：根据 JSON 生成基础地面/天花板/墙体碰撞。
## 后续可扩展：道具实例化、光照、出口、拾取物、LOD 等。

var _wall_material: StandardMaterial3D
var _floor_material: StandardMaterial3D

func build(data: Dictionary) -> Node3D:
	_wall_material = StandardMaterial3D.new()
	_floor_material = StandardMaterial3D.new()
	var theme: String = str(data.get("theme", "backrooms"))
	if theme == "warehouse":
		_wall_material.albedo_color = Color(0.55, 0.56, 0.58)
		_floor_material.albedo_color = Color(0.35, 0.36, 0.38)
	elif theme == "garden":
		_wall_material.albedo_color = Color(0.91, 0.88, 0.84)
		_floor_material.albedo_color = Color(0.56, 0.57, 0.53)
	else:
		_wall_material.albedo_color = Color(0.90, 0.84, 0.58)
		_floor_material.albedo_color = Color(0.60, 0.55, 0.44)

	var level := Node3D.new()
	level.name = "GeneratedLevel"

	var grid_w: int = int(data.get("gridW", 7))
	var grid_h: int = int(data.get("gridH", 7))
	var room_size: float = float(data.get("roomSize", 11.0))
	var room_h: float = float(data.get("roomH", 6.5))
	var wall_thick: float = float(data.get("wallThick", 0.25))
	var door_w: float = float(data.get("doorW", 6.0))
	var merge_chance: float = float(data.get("mergeChance", 0.3))
	var extra_open: float = float(data.get("extraOpen", 0.4))

	var maze := _generate_maze(grid_w, grid_h, extra_open)

	# 地面
	level.add_child(_make_box_static(
		Vector3(grid_w * room_size, 0.2, grid_h * room_size),
		Vector3(grid_w * room_size * 0.5, -0.1, grid_h * room_size * 0.5),
		_floor_material))

	# 天花板（园林 openSky=true 时可不封顶）
	if not bool(data.get("openSky", false)):
		level.add_child(_make_box_static(
			Vector3(grid_w * room_size, 0.2, grid_h * room_size),
			Vector3(grid_w * room_size * 0.5, room_h + 0.1, grid_h * room_size * 0.5),
			_floor_material))

	# 水平墙（沿 X）
	for z in range(grid_h + 1):
		for x in range(grid_w):
			var cx: float = (x + 0.5) * room_size
			var cz: float = z * room_size
			var has_wall: bool = z == 0 or z == grid_h or maze[z - 1][x]["s"]
			if has_wall:
				level.add_child(_make_box_static(
					Vector3(room_size + 0.05, room_h + 0.2, wall_thick),
					Vector3(cx, room_h * 0.5, cz), _wall_material))
			elif not _is_merged(x, z, merge_chance):
				var seg: float = (room_size - door_w) * 0.5 + 0.05
				if seg > 0.1:
					var offset: float = (room_size + door_w) * 0.25
					level.add_child(_make_box_static(Vector3(seg, room_h + 0.2, wall_thick), Vector3(cx - offset, room_h * 0.5, cz), _wall_material))
					level.add_child(_make_box_static(Vector3(seg, room_h + 0.2, wall_thick), Vector3(cx + offset, room_h * 0.5, cz), _wall_material))

	# 垂直墙（沿 Z）
	for x in range(grid_w + 1):
		for z in range(grid_h):
			var cx: float = x * room_size
			var cz: float = (z + 0.5) * room_size
			var has_wall: bool = x == 0 or x == grid_w or maze[z][x - 1]["e"]
			if has_wall:
				level.add_child(_make_box_static(
					Vector3(wall_thick, room_h + 0.2, room_size + 0.05),
					Vector3(cx, room_h * 0.5, cz), _wall_material))
			elif not _is_merged(x, z, merge_chance):
				var seg: float = (room_size - door_w) * 0.5 + 0.05
				if seg > 0.1:
					var offset: float = (room_size + door_w) * 0.25
					level.add_child(_make_box_static(Vector3(wall_thick, room_h + 0.2, seg), Vector3(cx, room_h * 0.5, cz - offset), _wall_material))
					level.add_child(_make_box_static(Vector3(wall_thick, room_h + 0.2, seg), Vector3(cx, room_h * 0.5, cz + offset), _wall_material))

	_spawn_lights(level, data)

	return level

func _spawn_lights(level: Node3D, data: Dictionary) -> void:
	var theme: String = str(data.get("theme", "backrooms"))
	var spacing: int = int(data.get("lightSpacing", 3))
	var dist: float = float(data.get("lightDist", 30.0))
	var energy: float = float(data.get("lightEnergy", 1.2))
	var color := Color(1.0, 0.95, 0.9)
	if theme == "warehouse":
		color = Color(0.85, 0.92, 1.0)
	elif theme == "garden":
		color = Color(1.0, 0.82, 0.6)

	var grid_w: int = int(data.get("gridW", 7))
	var grid_h: int = int(data.get("gridH", 7))
	var room_size: float = float(data.get("roomSize", 11.0))
	var room_h: float = float(data.get("roomH", 6.5))
	for z in range(grid_h):
		for x in range(grid_w):
			if x % spacing == 0 and z % spacing == 0:
				var light := OmniLight3D.new()
				light.omni_range = dist
				light.light_energy = energy
				light.light_color = color
				light.position = Vector3((x + 0.5) * room_size, room_h * 0.7, (z + 0.5) * room_size)
				level.add_child(light)

func _make_box_static(size: Vector3, pos: Vector3, material: Material) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.position = pos
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	col.shape = shape
	body.add_child(col)
	var mi := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh.material = material
	mi.mesh = mesh
	body.add_child(mi)
	return body

func _is_merged(x: int, z: int, chance: float) -> bool:
	var hv := (x * 374761393 + z * 668265263) & 0x7fffffff
	hv = ((hv ^ (hv >> 13)) * 1274126177) & 0x7fffffff
	hv = hv ^ (hv >> 16)
	return float(hv % 10) < round(chance * 10.0)

func _generate_maze(grid_w: int, grid_h: int, extra_open: float) -> Array:
	var cells: Array = []
	for z in range(grid_h):
		var row: Array = []
		for x in range(grid_w):
			row.append({
				"visited": false,
				"n": true, "s": true, "e": true, "w": true,
			})
		cells.append(row)
	_carve(cells, 0, 0, grid_w, grid_h)
	for z in range(grid_h):
		for x in range(grid_w):
			var cell: Dictionary = cells[z][x]
			if z < grid_h - 1 and cell["s"] and randf() < extra_open:
				cell["s"] = false
				cells[z + 1][x]["n"] = false
			if x < grid_w - 1 and cell["e"] and randf() < extra_open:
				cell["e"] = false
				cells[z][x + 1]["w"] = false
	return cells

func _carve(cells: Array, x: int, z: int, grid_w: int, grid_h: int) -> void:
	cells[z][x]["visited"] = true
	var dirs: Array[Vector2i] = [Vector2i(0, -1), Vector2i(0, 1), Vector2i(1, 0), Vector2i(-1, 0)]
	dirs.shuffle()
	for d: Vector2i in dirs:
		var nx := x + d.x
		var nz := z + d.y
		if nx >= 0 and nx < grid_w and nz >= 0 and nz < grid_h and not cells[nz][nx]["visited"]:
			if d.y == -1:
				cells[z][x]["n"] = false
				cells[nz][nx]["s"] = false
			elif d.y == 1:
				cells[z][x]["s"] = false
				cells[nz][nx]["n"] = false
			elif d.x == 1:
				cells[z][x]["e"] = false
				cells[nz][nx]["w"] = false
			else:
				cells[z][x]["w"] = false
				cells[nz][nx]["e"] = false
			_carve(cells, nx, nz, grid_w, grid_h)
