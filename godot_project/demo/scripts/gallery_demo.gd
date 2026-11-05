extends Node2D
## Scrollable gallery of every monster (cycling animations) and environmental animation.

const CREATURE_CYCLE := ["idle", "move", "attack", "hurt", "death"]
const CHAR_CYCLE := ["idle_side", "walk_side", "attack_side", "hurt_side", "death_side"]

var _sprites: Array = []
var _step := 0
var _cam: Camera2D


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.14, 0.13, 0.21)
	bg.size = Vector2(640, 2400)
	add_child(bg)
	_cam = Camera2D.new()
	_cam.position = Vector2(320, 180)
	add_child(_cam)
	var mon: Dictionary = RPGSheet.catalog("monsters/monsters.json")
	var x := 24.0
	var y := 60.0
	var title := DemoWorld.make_label("Monsters (%d) — animations cycle every 2s · mouse wheel / arrows to scroll" % mon["monsters"].size(), 10)
	title.position = Vector2(12, 10)
	add_child(title)
	for m in mon["monsters"]:
		var s: int = int(m["frame_size"][0])
		var frames: SpriteFrames = load("%s/resources/frames/monsters/%s.tres" % [RPGSheet.PACK, m["id"]])
		var spr := AnimatedSprite2D.new()
		spr.sprite_frames = frames
		if s > 32 and x > 24.0:
			x = 24.0
			y += 70.0
		spr.position = Vector2(x + s / 2.0, y)
		add_child(spr)
		var lab := DemoWorld.make_label(m["name"], 6, Color(0.8, 0.8, 0.92))
		lab.position = Vector2(x - 4, y + s / 2.0 + 1)
		add_child(lab)
		_sprites.append([spr, m["layout"]])
		x += max(s, 32) + 26.0
		if x > 600.0:
			x = 24.0
			y += 70.0 if s <= 32 else 100.0
	y += 110.0
	var anims: Dictionary = RPGSheet.catalog("animations/animations.json")
	var t2 := DemoWorld.make_label("Environmental animations", 10)
	t2.position = Vector2(12, y - 40)
	add_child(t2)
	x = 40.0
	for a in anims["items"]:
		var sp := DemoWorld.add_animation(self, a["id"], Vector2(x, y + 40))
		var lab := DemoWorld.make_label(a["name"], 6, Color(0.8, 0.8, 0.92))
		lab.position = Vector2(x - 20, y + 42)
		add_child(lab)
		x += float(a["frame_size"][0]) + 40.0
		if x > 600.0:
			x = 40.0
			y += 110.0
	_cycle()
	var t := Timer.new()
	t.wait_time = 2.0
	t.autostart = true
	t.timeout.connect(_cycle)
	add_child(t)


func _cycle() -> void:
	for pair in _sprites:
		var spr: AnimatedSprite2D = pair[0]
		var names: Array = CHAR_CYCLE if pair[1] == "character" else CREATURE_CYCLE
		spr.play(names[_step % names.size()])
	_step += 1


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_cam.position.y += 40
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_cam.position.y = max(180.0, _cam.position.y - 40)
	if event.is_action_pressed("move_down"):
		_cam.position.y += 80
	elif event.is_action_pressed("move_up"):
		_cam.position.y = max(180.0, _cam.position.y - 80)
