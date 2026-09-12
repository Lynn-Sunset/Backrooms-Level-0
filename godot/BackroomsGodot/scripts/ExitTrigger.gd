class_name ExitTrigger
extends Area3D

signal exited(next_level: String)

@export var next_level: String = "level1"

func _ready() -> void:
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node3D) -> void:
	if body is Player:
		exited.emit(next_level)
