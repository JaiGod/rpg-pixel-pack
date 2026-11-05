class_name CharacterSprite
extends AnimatedSprite2D
## A single pre-baked character / humanoid monster sheet with the same API as LayeredCharacter
## (face, play_anim, flash, action_finished) so controllers work with either.

signal action_finished(anim: String)

## Optional: a baked sheet (characters/presets/... or monsters/...). Builds frames at runtime.
@export var sheet: Texture2D:
	set(v):
		sheet = v
		if v != null:
			sprite_frames = RPGSheet.character_frames(v)
@export var start_direction: String = "down"

var direction: String = "down"
var current_anim: String = "idle"
var _flash_t: float = 0.0


func _ready() -> void:
	direction = start_direction
	position.y = -14 if position == Vector2.ZERO else position.y
	animation_finished.connect(func(): action_finished.emit(current_anim))
	if sprite_frames != null:
		play_anim("idle", true)


func _process(delta: float) -> void:
	if _flash_t > 0.0:
		_flash_t -= delta
		modulate = Color(3, 3, 3) if fmod(_flash_t, 0.1) > 0.05 else Color.WHITE
		if _flash_t <= 0.0:
			modulate = Color.WHITE


func play_anim(anim: String, restart: bool = false) -> void:
	var full := "%s_%s" % [anim, direction]
	if sprite_frames == null or not sprite_frames.has_animation(full):
		return
	if anim == current_anim and animation == full and is_playing() and not restart:
		return
	current_anim = anim
	play(full)
	if restart:
		frame = 0


func face(v: Vector2) -> bool:
	if v == Vector2.ZERO:
		return false
	var d: Array = RPGSheet.dir_from_vector(v)
	if d[0] == direction and d[1] == flip_h:
		return false
	direction = d[0]
	flip_h = d[1]
	play_anim(current_anim, true)
	return true


func flash(seconds: float = 0.2) -> void:
	_flash_t = seconds
