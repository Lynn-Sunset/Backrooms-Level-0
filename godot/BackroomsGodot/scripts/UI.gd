extends CanvasLayer

@onready var bar: ProgressBar = $Control/StaminaBar
@onready var label: Label = $Control/StaminaLabel

func set_stamina(ratio: float, sprinting: bool) -> void:
	bar.value = ratio * 100.0
	label.text = ("冲刺中 ⚡ " if sprinting else "") + "体力 %d%%" % int(ratio * 100.0)
