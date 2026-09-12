class_name PickupTrigger
extends Area3D

signal collected(bonus: float)

@export var bonus: float = 45.0
@export var respawn_seconds: float = 0.0

func _ready() -> void:
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node3D) -> void:
	if body is Player:
		collected.emit(bonus)
		queue_free()
