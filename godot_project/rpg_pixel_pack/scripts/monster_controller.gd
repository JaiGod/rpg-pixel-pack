class_name MonsterController
extends CharacterBody2D
## Simple monster AI: wander -> chase the player inside aggro range -> attack -> hurt/death.
## Set `monster_id` (see monsters/monsters.json) and it loads the right sheet + layout.

signal killed(monster_id: String)

@export var monster_id: String = "slime_green"
@export var max_hp: int = 3
@export var speed: float = 32.0
@export var aggro_range: float = 90.0
@export var attack_range: float = 18.0
@export var damage: int = 1

var hp: int
var state := "wander"
var _layout := "creature"
var _sprite: AnimatedSprite2D
var _dir := "side"
var _home: Vector2
var _target: Vector2
var _t := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	add_to_group("monsters")
	_rng.randomize()
	hp = max_hp
	_home = global_position
	_target = _home
	_sprite = AnimatedSprite2D.new()
	add_child(_sprite)
	load_monster(monster_id)
	_sprite.animation_finished.connect(_on_anim_finished)


func load_monster(id: String) -> void:
	monster_id = id
	var cat: Dictionary = RPGSheet.catalog("monsters/monsters.json")
	for m in cat.get("monsters", []):
		if m["id"] == id:
			var tex: Texture2D = load(RPGSheet.res_path(m["file"]))
			_layout = m["layout"]
			var size: int = int(m["frame_size"][0])
			if _layout == "character":
				_sprite.sprite_frames = RPGSheet.character_frames(tex)
				_sprite.position = Vector2(0, -14)
			else:
				_sprite.sprite_frames = RPGSheet.creature_frames(tex, size)
				_sprite.position = Vector2(0, -size / 2.0 + 2.0)
			_play("idle")
			return
	push_warning("MonsterController: unknown monster " + id)


func _anim_name(base: String) -> String:
	if _layout == "character":
		var b := "walk" if base == "move" else base
		return "%s_%s" % [b, _dir]
	return base


func _play(base: String, restart := false) -> void:
	var a := _anim_name(base)
	if _sprite.sprite_frames == null or not _sprite.sprite_frames.has_animation(a):
		return
	if _sprite.animation != a or restart or not _sprite.is_playing():
		_sprite.play(a)
		if restart:
			_sprite.frame = 0


func _face(v: Vector2) -> void:
	if _layout == "character":
		var d: Array = RPGSheet.dir_from_vector(v)
		_dir = d[0]
		_sprite.flip_h = d[1]
	elif absf(v.x) > 0.01:
		_sprite.flip_h = v.x < 0.0


func _physics_process(delta: float) -> void:
	if state == "dead" or state == "attack" or state == "hurt":
		if state == "hurt":
			move_and_slide()
			velocity = velocity.move_toward(Vector2.ZERO, 500 * delta)
		return
	var player := _find_player()
	if player != null:
		var to: Vector2 = player.global_position - global_position
		if to.length() < attack_range:
			_face(to)
			state = "attack"
			_play("attack", true)
			_t = 0.0
			return
		if to.length() < aggro_range:
			state = "chase"
			velocity = to.normalized() * speed * 1.4
			_face(velocity)
			move_and_slide()
			_play("move")
			return
	state = "wander"
	_t -= delta
	if _t <= 0.0:
		_t = _rng.randf_range(1.0, 3.0)
		var a := _rng.randf() * TAU
		_target = _home + Vector2(cos(a), sin(a)) * _rng.randf_range(0.0, 40.0)
	var tw := _target - global_position
	if tw.length() > 3.0:
		velocity = tw.normalized() * speed
		_face(velocity)
		move_and_slide()
		_play("move")
	else:
		_play("idle")


func _find_player() -> Node2D:
	var ps := get_tree().get_nodes_in_group("player")
	if ps.is_empty():
		return null
	if ps[0].get("dead") == true:
		return null
	return ps[0]


func take_damage(amount: int, knockback: Vector2 = Vector2.ZERO) -> void:
	if state == "dead":
		return
	hp -= amount
	_sprite.modulate = Color(3, 3, 3)
	get_tree().create_timer(0.08).timeout.connect(_clear_flash)
	if hp <= 0:
		state = "dead"
		_play("death", true)
		killed.emit(monster_id)
		return
	state = "hurt"
	velocity = knockback * 120.0
	_play("hurt", true)


func _clear_flash() -> void:
	if is_instance_valid(_sprite):
		_sprite.modulate = Color.WHITE


func _on_anim_finished() -> void:
	match state:
		"attack":
			var p := _find_player()
			if p != null and (p.global_position - global_position).length() < attack_range + 6.0 and p.has_method("take_damage"):
				p.call("take_damage", damage, (p.global_position - global_position).normalized())
			state = "wander"
			_t = 0.4
		"hurt":
			state = "wander"
		"dead":
			var tw := create_tween()
			tw.tween_property(self, "modulate:a", 0.0, 0.6)
			tw.tween_callback(queue_free)
