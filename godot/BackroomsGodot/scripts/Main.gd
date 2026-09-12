extends Node3D

@export var start_level := "level0"

@onready var player: Player = $Player
@onready var levels: Node3D = $Levels
@onready var ui: CanvasLayer = $UI

var _current_level := ""

func _ready() -> void:
	_load_level(start_level)

func _load_level(id: String) -> void:
	# 清理旧关卡
	for child in levels.get_children():
		child.queue_free()
	_current_level = id

	var data := LevelData.load_level(id)
	if data.is_empty():
		return

	var builder := LevelBuilder.new()
	var level := builder.build(data)
	levels.add_child(level)

	# 玩家出生点
	if data.has("spawn"):
		var spawn: Dictionary = data["spawn"]
		player.global_position = Vector3(
			float(spawn.get("x", 0.0)),
			float(spawn.get("y", 1.7)),
			float(spawn.get("z", 0.0)))

	_spawn_exits(level, data)
	_spawn_pickups(level, data)

func _spawn_exits(level: Node3D, data: Dictionary) -> void:
	for exit_data in data.get("exits", []):
		var trigger := Area3D.new()
		var shape := CollisionShape3D.new()
		var sphere := SphereShape3D.new()
		sphere.radius = 1.5
		shape.shape = sphere
		trigger.add_child(shape)
		trigger.position = Vector3(float(exit_data.get("x", 0.0)), 1.7, float(exit_data.get("z", 0.0)))
		trigger.set_script(load("res://scripts/ExitTrigger.gd"))
		trigger.next_level = String(exit_data.get("next", "level1"))
		trigger.exited.connect(_on_exit)
		level.add_child(trigger)

func _spawn_pickups(level: Node3D, data: Dictionary) -> void:
	var bonus: float = float(data.get("pickupBonus", 45.0))
	for pickup_data in data.get("pickups", []):
		var trigger := Area3D.new()
		var shape := CollisionShape3D.new()
		var sphere := SphereShape3D.new()
		sphere.radius = 1.2
		shape.shape = sphere
		trigger.add_child(shape)
		trigger.position = Vector3(float(pickup_data.get("x", 0.0)), 1.7, float(pickup_data.get("z", 0.0)))
		trigger.set_script(load("res://scripts/PickupTrigger.gd"))
		trigger.bonus = bonus
		trigger.collected.connect(_on_pickup)
		level.add_child(trigger)

func _on_exit(next_level: String) -> void:
	if next_level == _current_level:
		return
	_load_level(next_level)

func _on_pickup(bonus: float) -> void:
	player.stamina = minf(player.stamina + bonus, player.stamina_max)
	ui.show_toast("💧 杏仁水 +%d 秒" % int(bonus))
