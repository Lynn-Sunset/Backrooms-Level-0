class_name Player
extends CharacterBody3D

@export var walk_speed := 5.5
@export var sprint_speed := 8.5
@export var jump_velocity := 4.8
@export var mouse_sensitivity := 0.002
@export var gravity := 13.0
@export var stamina_max := 120.0
@export var sprint_drain := 22.0
@export var stamina_regen := 8.0

var stamina := stamina_max
var sprinting := false

@onready var camera: Camera3D = $Camera3D
@onready var ui: CanvasLayer = get_node_or_null("/root/Main/UI")

func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _input(event: InputEvent) -> void:
	# 鼠标视角：用 _input 而不是 _unhandled_input，避免被全屏 UI Control 拦截
	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		camera.rotate_x(-event.relative.y * mouse_sensitivity)
		camera.rotation.x = clampf(camera.rotation.x, -1.4, 1.4)

func _unhandled_input(event: InputEvent) -> void:
	if Input.is_action_just_pressed("pause"):
		if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		else:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	var input_vec := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (transform.basis * Vector3(input_vec.x, 0.0, input_vec.y)).normalized()
	sprinting = Input.is_action_pressed("sprint") and input_vec.length() > 0.1 and stamina > 0.0
	var speed := sprint_speed if sprinting else walk_speed

	velocity.x = lerpf(velocity.x, dir.x * speed, 10.0 * delta)
	velocity.z = lerpf(velocity.z, dir.z * speed, 10.0 * delta)

	if sprinting:
		stamina = maxf(stamina - sprint_drain * delta, 0.0)
	else:
		stamina = minf(stamina + stamina_regen * delta, stamina_max)

	if ui:
		ui.set_stamina(stamina / stamina_max, sprinting)

	move_and_slide()
