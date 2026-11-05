class_name NPCController
extends CharacterBody2D
## Wandering NPC with a speech bubble. Press E (interact) next to it to talk.

signal talked(npc_name: String, line: String)

@export var npc_name: String = "Villager"
@export var lines: PackedStringArray = PackedStringArray(["Lovely day, isn't it?"])
@export var wander_radius: float = 48.0
@export var speed: float = 28.0
@export var idle_time_range: Vector2 = Vector2(1.0, 3.5)

@onready var visual = $Visual

var _home: Vector2
var _target: Vector2
var _idle_t := 0.0
var _line_idx := 0
var _bubble: Label
var _bubble_t := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	add_to_group("interactable")
	add_to_group("npcs")
	_rng.randomize()
	_home = global_position
	_target = _home
	_idle_t = _rng.randf_range(idle_time_range.x, idle_time_range.y)
	_bubble = Label.new()
	_bubble.position = Vector2(-60, -52)
	_bubble.size = Vector2(120, 16)
	_bubble.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_bubble.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bubble.add_theme_font_size_override("font_size", 8)
	_bubble.add_theme_color_override("font_color", Color(1, 1, 0.92))
	_bubble.add_theme_color_override("font_outline_color", Color(0.1, 0.08, 0.15))
	_bubble.add_theme_constant_override("outline_size", 4)
	_bubble.visible = false
	_bubble.z_index = 50
	add_child(_bubble)


func _physics_process(delta: float) -> void:
	if _bubble_t > 0.0:
		_bubble_t -= delta
		if _bubble_t <= 0.0:
			_bubble.visible = false
	if _idle_t > 0.0:
		_idle_t -= delta
		velocity = Vector2.ZERO
		visual.play_anim("idle")
		if _idle_t <= 0.0:
			var a := _rng.randf() * TAU
			_target = _home + Vector2(cos(a), sin(a)) * _rng.randf_range(8.0, wander_radius)
		return
	var to := _target - global_position
	if to.length() < 3.0 or _bubble.visible:
		_idle_t = _rng.randf_range(idle_time_range.x, idle_time_range.y)
		return
	velocity = to.normalized() * speed
	move_and_slide()
	if get_slide_collision_count() > 0:
		_idle_t = 0.6
	visual.face(velocity)
	visual.play_anim("walk")


func interact(by: Node2D) -> void:
	visual.face(by.global_position - global_position)
	var line := lines[_line_idx % lines.size()] if lines.size() > 0 else "..."
	_line_idx += 1
	_bubble.text = line
	_bubble.visible = true
	_bubble_t = 3.0
	_idle_t = 3.0
	talked.emit(npc_name, line)
