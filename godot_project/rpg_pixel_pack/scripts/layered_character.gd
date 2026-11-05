@tool
class_name LayeredCharacter
extends Node2D
## A character assembled from independent, palette-swappable layers.
##
## Every layer is an AnimatedSprite2D using the same 18-animation layout, so any mix
## of body / hair / clothing / headgear / cape / weapon lines up frame-perfectly.
##
##   $Hero.set_layer("torso", "plate", "cloth_blue", "cloth_yellow")
##   $Hero.set_hair("ponytail", "hair_red")
##   $Hero.face(Vector2.LEFT); $Hero.play_anim("walk")

signal action_finished(anim: String)

const LAYER_ORDER := ["hair_back", "body", "legs", "torso", "cape", "hair", "head", "accessory", "offhand", "weapon"]
const HAIR_HIDING_HEADGEAR := ["knight_helm", "space_helmet", "hood", "necro_cowl"]
const SWAP_SHADER := preload("res://rpg_pixel_pack/shaders/palette_swap.gdshader")

@export_enum("male", "female") var sex: String = "male":
	set(v):
		sex = v
		_refresh_all()
@export var skin: String = "skin_light":
	set(v):
		skin = v
		if is_inside_tree():
			set_layer("body", skin)
@export var hair_style: String = "short"
@export var hair_color: String = "hair_brown"
@export var torso_style: String = "tunic"
@export var torso_colors: PackedStringArray = PackedStringArray(["cloth_blue", "cloth_yellow"])
@export var legs_style: String = "pants"
@export var legs_colors: PackedStringArray = PackedStringArray(["cloth_brown", "leather"])
@export var head_style: String = ""
@export var head_colors: PackedStringArray = PackedStringArray(["cloth_red", "cloth_red"])
@export var cape_style: String = ""
@export var cape_colors: PackedStringArray = PackedStringArray(["cloth_red", "gold"])
@export var accessory_style: String = ""
@export var weapon: String = ""
@export var offhand: String = ""
@export var start_direction: String = "down"

var layers: Dictionary = {}        # kind -> AnimatedSprite2D
var styles: Dictionary = {}        # kind -> [style, primary, secondary]
var direction: String = "down"
var current_anim: String = "idle"
var flipped: bool = false
var _flash_t: float = 0.0


func _ready() -> void:
	direction = start_direction
	_build_from_exports()
	play_anim("idle")


func _process(delta: float) -> void:
	if _flash_t > 0.0:
		_flash_t = maxf(_flash_t - delta, 0.0)
		_set_param("flash", clampf(_flash_t * 6.0, 0.0, 1.0))


func _build_from_exports() -> void:
	set_layer("body", skin)
	set_hair(hair_style, hair_color)
	set_layer("torso", torso_style, _c(torso_colors, 0), _c(torso_colors, 1))
	set_layer("legs", legs_style, _c(legs_colors, 0), _c(legs_colors, 1))
	set_layer("head", head_style, _c(head_colors, 0), _c(head_colors, 1))
	set_layer("cape", cape_style, _c(cape_colors, 0), _c(cape_colors, 1))
	set_layer("accessory", accessory_style, hair_color if accessory_style == "beard" else _c(torso_colors, 0), _c(torso_colors, 1))
	set_layer("weapon", weapon)
	set_layer("offhand", offhand, _c(torso_colors, 0), _c(torso_colors, 1))


func _c(arr: PackedStringArray, i: int) -> String:
	return arr[i] if arr.size() > i else ""


func _refresh_all() -> void:
	if not is_inside_tree():
		return
	for kind in styles.keys():
		var s: Array = styles[kind]
		set_layer(kind, s[0], s[1], s[2])


static func layer_path(sex_name: String, kind: String, style: String) -> String:
	return "%s/characters/layers/%s/%s/%s.png" % [RPGSheet.PACK, sex_name, kind, style]


## Set (or clear with style = "") one layer. primary/secondary are ramp names from ramps.json.
func set_layer(kind: String, style: String, primary: String = "", secondary: String = "") -> void:
	if style == "":
		clear_layer(kind)
		return
	var path := layer_path(sex, kind, style)
	if not ResourceLoader.exists(path):
		push_warning("LayeredCharacter: no layer " + path)
		clear_layer(kind)
		return
	var spr := _get_sprite(kind)
	spr.sprite_frames = RPGSheet.character_frames(load(path))
	var mat := spr.material as ShaderMaterial
	mat.set_shader_parameter("swap_enabled", kind != "body" and kind != "weapon")
	_apply_ramp(mat, "primary", primary)
	_apply_ramp(mat, "secondary", secondary)
	styles[kind] = [style, primary, secondary]
	spr.visible = true
	if kind == "head":
		_update_hair_visibility()
	_sync(spr)


func clear_layer(kind: String) -> void:
	styles.erase(kind)
	if layers.has(kind):
		layers[kind].visible = false
		layers[kind].sprite_frames = null
	if kind == "head":
		_update_hair_visibility()


func get_layer_style(kind: String) -> String:
	return styles[kind][0] if styles.has(kind) else ""


func set_hair(style: String, color: String) -> void:
	hair_color = color
	set_layer("hair", style, color)
	var back := layer_path(sex, "hair_back", style)
	if style != "" and ResourceLoader.exists(back):
		set_layer("hair_back", style, color)
	else:
		clear_layer("hair_back")
	_update_hair_visibility()


func _update_hair_visibility() -> void:
	var hide_hair := styles.has("head") and HAIR_HIDING_HEADGEAR.has(styles["head"][0])
	for k in ["hair", "hair_back"]:
		if layers.has(k) and styles.has(k):
			layers[k].visible = not hide_hair


func _apply_ramp(mat: ShaderMaterial, channel: String, ramp_name: String) -> void:
	var cols: Array = RPGSheet.ramp(ramp_name) if ramp_name != "" else []
	var keys := {
		"primary": [Color8(60, 60, 60), Color8(110, 110, 110), Color8(165, 165, 165), Color8(220, 220, 220)],
		"secondary": [Color8(52, 40, 92), Color8(92, 72, 152), Color8(140, 120, 204), Color8(190, 176, 236)],
	}
	for i in 4:
		var c: Color = cols[i] if cols.size() == 4 else keys[channel][i]
		mat.set_shader_parameter("%s_%d" % [channel, i], c)


func _get_sprite(kind: String) -> AnimatedSprite2D:
	if layers.has(kind):
		return layers[kind]
	var spr := AnimatedSprite2D.new()
	spr.name = kind.capitalize().replace(" ", "")
	spr.position = Vector2(0, -14)   # feet at the node origin
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var mat := ShaderMaterial.new()
	mat.shader = SWAP_SHADER
	spr.material = mat
	add_child(spr)
	layers[kind] = spr
	# keep draw order
	var idx := 0
	for k in LAYER_ORDER:
		if layers.has(k):
			move_child(layers[k], idx)
			idx += 1
	if kind == "body":
		spr.animation_finished.connect(_on_body_finished)
	return spr


func _master() -> AnimatedSprite2D:
	for k in ["body", "torso", "legs"]:
		if layers.has(k) and layers[k].sprite_frames != null:
			return layers[k]
	return null


func _sync(spr: AnimatedSprite2D) -> void:
	var m := _master()
	var anim := "%s_%s" % [current_anim, direction]
	if spr.sprite_frames == null or not spr.sprite_frames.has_animation(anim):
		return
	spr.flip_h = flipped
	spr.play(anim)
	if m != null and m != spr and m.animation == anim:
		spr.frame = m.frame
		spr.frame_progress = m.frame_progress


## Play an animation ("idle", "walk", "run", "attack", "hurt", "death") in the current direction.
func play_anim(anim: String, restart: bool = false) -> void:
	var full := "%s_%s" % [anim, direction]
	if anim == current_anim and not restart:
		var m := _master()
		if m != null and m.animation == full and m.is_playing():
			return
	current_anim = anim
	for k in layers:
		var spr: AnimatedSprite2D = layers[k]
		if spr.sprite_frames != null and spr.sprite_frames.has_animation(full):
			spr.flip_h = flipped
			spr.play(full)
			spr.frame = 0
			spr.frame_progress = 0.0


## Turn toward a direction vector (4-way). Returns true if the facing changed.
func face(v: Vector2) -> bool:
	if v == Vector2.ZERO:
		return false
	var d: Array = RPGSheet.dir_from_vector(v)
	if d[0] == direction and d[1] == flipped:
		return false
	direction = d[0]
	flipped = d[1]
	play_anim(current_anim, true)
	return true


func flash(seconds: float = 0.18) -> void:
	_flash_t = seconds


func _set_param(p: String, v: Variant) -> void:
	for k in layers:
		var mat := (layers[k] as AnimatedSprite2D).material as ShaderMaterial
		if mat:
			mat.set_shader_parameter(p, v)


func _on_body_finished() -> void:
	action_finished.emit(current_anim)
