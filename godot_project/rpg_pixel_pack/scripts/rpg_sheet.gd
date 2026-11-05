class_name RPGSheet
extends RefCounted
## Sprite-sheet layouts, SpriteFrames builders and catalog access for the RPG Pixel Pack.
##
## Character sheets (players, NPCs, humanoid monsters, every customization layer):
##   6 columns x 18 rows of 32x32 frames. Rows = animation x direction:
##   idle_down, idle_up, idle_side, walk_down, ... death_side. "side" faces right.
## Creature sheets (non-humanoid monsters): 5 rows (idle, move, attack, hurt, death) facing right.

const PACK := "res://rpg_pixel_pack"
const FRAME := 32
const DIRS := ["down", "up", "side"]
const ANIMS := [
	{"name": "idle", "frames": 4, "fps": 6.0, "loop": true},
	{"name": "walk", "frames": 6, "fps": 10.0, "loop": true},
	{"name": "run", "frames": 6, "fps": 14.0, "loop": true},
	{"name": "attack", "frames": 4, "fps": 12.0, "loop": false},
	{"name": "hurt", "frames": 2, "fps": 8.0, "loop": false},
	{"name": "death", "frames": 5, "fps": 8.0, "loop": false},
]
const CREATURE_ANIMS := [
	{"name": "idle", "frames": 4, "fps": 6.0, "loop": true},
	{"name": "move", "frames": 4, "fps": 8.0, "loop": true},
	{"name": "attack", "frames": 4, "fps": 10.0, "loop": false},
	{"name": "hurt", "frames": 2, "fps": 8.0, "loop": false},
	{"name": "death", "frames": 5, "fps": 8.0, "loop": false},
]

static var _frames_cache: Dictionary = {}
static var _json_cache: Dictionary = {}
static var _ramps: Dictionary = {}


## SpriteFrames for any character-layout sheet (cached per texture).
static func character_frames(tex: Texture2D) -> SpriteFrames:
	var key := "char:" + tex.resource_path
	if tex.resource_path != "" and _frames_cache.has(key):
		return _frames_cache[key]
	var sf := SpriteFrames.new()
	if sf.has_animation(&"default"):
		sf.remove_animation(&"default")
	var row := 0
	for a in ANIMS:
		for d in DIRS:
			var anim_name := "%s_%s" % [a["name"], d]
			sf.add_animation(anim_name)
			sf.set_animation_speed(anim_name, a["fps"])
			sf.set_animation_loop(anim_name, a["loop"])
			for f in int(a["frames"]):
				var at := AtlasTexture.new()
				at.atlas = tex
				at.region = Rect2(f * FRAME, row * FRAME, FRAME, FRAME)
				sf.add_frame(anim_name, at)
			row += 1
	if tex.resource_path != "":
		_frames_cache[key] = sf
	return sf


## SpriteFrames for a creature-layout monster sheet.
static func creature_frames(tex: Texture2D, size: int) -> SpriteFrames:
	var key := "creature:%s" % tex.resource_path
	if _frames_cache.has(key):
		return _frames_cache[key]
	var sf := SpriteFrames.new()
	if sf.has_animation(&"default"):
		sf.remove_animation(&"default")
	for row in CREATURE_ANIMS.size():
		var a: Dictionary = CREATURE_ANIMS[row]
		var anim_name: String = a["name"]
		sf.add_animation(anim_name)
		sf.set_animation_speed(anim_name, a["fps"])
		sf.set_animation_loop(anim_name, a["loop"])
		for f in int(a["frames"]):
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(f * size, row * size, size, size)
			sf.add_frame(anim_name, at)
	_frames_cache[key] = sf
	return sf


## SpriteFrames for a horizontal strip (environment animations).
static func strip_frames(tex: Texture2D, frame_size: Vector2i, count: int, fps: float, loop: bool) -> SpriteFrames:
	var sf := SpriteFrames.new()
	sf.set_animation_speed(&"default", fps)
	sf.set_animation_loop(&"default", loop)
	for f in count:
		var at := AtlasTexture.new()
		at.atlas = tex
		at.region = Rect2(f * frame_size.x, 0, frame_size.x, frame_size.y)
		sf.add_frame(&"default", at)
	return sf


## Load & cache any of the pack's JSON catalogs, e.g. RPGSheet.catalog("monsters/monsters.json").
## (Remember to add "*.json" to your export preset's non-resource filter when exporting.)
static func catalog(rel_path: String) -> Variant:
	if _json_cache.has(rel_path):
		return _json_cache[rel_path]
	var path := "%s/%s" % [PACK, rel_path]
	if not FileAccess.file_exists(path):
		push_error("RPGSheet: missing catalog " + path)
		return {}
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	_json_cache[rel_path] = data
	return data


## 4 colors (dark -> light) of a named palette ramp, e.g. "cloth_red".
static func ramp(ramp_name: String) -> Array[Color]:
	if _ramps.is_empty():
		var raw: Dictionary = catalog("assets/palette/ramps.json")
		for k in raw:
			var cols: Array[Color] = []
			for h in raw[k]:
				cols.append(Color.html(h))
			_ramps[k] = cols
	var out: Array[Color] = []
	if _ramps.has(ramp_name):
		out.assign(_ramps[ramp_name])
	return out


static func ramp_names(prefix: String = "") -> Array[String]:
	ramp("cloth_red")
	var out: Array[String] = []
	for k in _ramps:
		if prefix == "" or String(k).begins_with(prefix):
			out.append(k)
	return out


## Pick the animation direction suffix + horizontal flip for a movement vector.
static func dir_from_vector(v: Vector2) -> Array:
	if absf(v.x) > absf(v.y):
		return ["side", v.x < 0.0]
	return ["down" if v.y >= 0.0 else "up", false]


static func res_path(rel: String) -> String:
	return "%s/%s" % [PACK, rel]
