class_name PlayerController
extends CharacterBody2D
## Top-down 4-direction player: walk, run (Shift), attack (Space / J), interact (E).
## Works with a LayeredCharacter or CharacterSprite child named "Visual".

signal health_changed(hp: int, max_hp: int)
signal died

@export var walk_speed: float = 70.0
@export var run_speed: float = 125.0
@export var max_hp: int = 10
@export var attack_range: float = 26.0
@export var attack_damage: int = 1

@onready var visual = $Visual

var hp: int
var attacking := false
var dead := false
var _hurt_t := 0.0


func _ready() -> void:
	add_to_group("player")
	hp = max_hp
	visual.action_finished.connect(_on_action_finished)


func _physics_process(delta: float) -> void:
	if dead:
		return
	if _hurt_t > 0.0:
		_hurt_t -= delta
		move_and_slide()
		velocity = velocity.move_toward(Vector2.ZERO, 600 * delta)
		return
	if attacking:
		velocity = Vector2.ZERO
		return
	var dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var running := Input.is_action_pressed("run")
	velocity = dir * (run_speed if running else walk_speed)
	move_and_slide()
	if dir != Vector2.ZERO:
		visual.face(dir)
		visual.play_anim("run" if running else "walk")
	else:
		visual.play_anim("idle")
	if Input.is_action_just_pressed("attack"):
		_attack()
	elif Input.is_action_just_pressed("interact"):
		_interact()


func facing_vector() -> Vector2:
	match visual.direction:
		"up":
			return Vector2.UP
		"down":
			return Vector2.DOWN
	return Vector2.LEFT if _is_flipped() else Vector2.RIGHT


func _is_flipped() -> bool:
	if "flipped" in visual:
		return visual.flipped
	return visual.flip_h


func _attack() -> void:
	attacking = true
	visual.play_anim("attack", true)
	var fwd := facing_vector()
	for n in get_tree().get_nodes_in_group("monsters"):
		var m = n
		var to: Vector2 = m.global_position - global_position
		if to.length() <= attack_range and to.normalized().dot(fwd) > 0.3 and m.has_method("take_damage"):
			m.call("take_damage", attack_damage, fwd)


func _interact() -> void:
	var best = null
	var best_d := 30.0
	for n in get_tree().get_nodes_in_group("interactable"):
		var node = n
		var d: float = (node.global_position - global_position).length()
		if d < best_d:
			best_d = d
			best = node
	if best != null and best.has_method("interact"):
		best.call("interact", self)


func take_damage(amount: int, knockback: Vector2 = Vector2.ZERO) -> void:
	if dead:
		return
	hp = max(hp - amount, 0)
	health_changed.emit(hp, max_hp)
	visual.flash()
	if hp == 0:
		dead = true
		visual.play_anim("death", true)
		died.emit()
		return
	attacking = false
	_hurt_t = 0.25
	velocity = knockback * 140.0
	visual.play_anim("hurt", true)


func _on_action_finished(anim: String) -> void:
	if anim == "attack":
		attacking = false
	if anim == "hurt" and not dead:
		visual.play_anim("idle")
