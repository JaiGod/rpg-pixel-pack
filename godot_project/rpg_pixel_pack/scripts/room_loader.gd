class_name RoomLoader
extends Node2D
## Builds a furnished interior from interiors/rooms/<category>/<id>.json:
## a TileMapLayer (floor/walls, with wall collision) + y-sorted furniture sprites with colliders.

const INTERIOR_TILESET := preload("res://rpg_pixel_pack/resources/tilesets/interior.tres")
const NO_COLLIDE := ["rug_", "painting_", "banner_", "wall_", "candles"]

@export var room_id: String = "bedroom_cottage"

var floor_layer: TileMapLayer
var props: Node2D
var room_size := Vector2i.ZERO
var door_tile := Vector2i.ZERO


func _ready() -> void:
	floor_layer = TileMapLayer.new()
	floor_layer.tile_set = INTERIOR_TILESET
	add_child(floor_layer)
	props = Node2D.new()
	props.y_sort_enabled = true
	add_child(props)
	if room_id != "":
		load_room(room_id)


func list_rooms() -> Array:
	var cat: Dictionary = RPGSheet.catalog("interiors/interiors.json")
	return cat.get("rooms", [])


func load_room(id: String) -> void:
	room_id = id
	floor_layer.clear()
	for c in props.get_children():
		c.queue_free()
	var entry: Dictionary = {}
	for r in list_rooms():
		if r["id"] == id:
			entry = r
	if entry.is_empty():
		push_error("RoomLoader: unknown room " + id)
		return
	var lay: Dictionary = RPGSheet.catalog(entry["layout"])
	room_size = Vector2i(lay["size_tiles"][0], lay["size_tiles"][1])
	door_tile = Vector2i(lay["door_tile"][0], lay["door_tile"][1])
	var tiles: Array = lay["tiles"]
	for y in tiles.size():
		for x in tiles[y].size():
			var t: Array = tiles[y][x]
			floor_layer.set_cell(Vector2i(x, y), 0, Vector2i(int(t[0]), int(t[1])))
	var furn := _furniture_index()
	for f in lay["furniture"]:
		var fid: String = f["furniture"]
		if not furn.has(fid):
			continue
		var tex: Texture2D = load(RPGSheet.res_path(furn[fid]["file"]))
		var size := Vector2(f["size"][0], f["size"][1])
		var px := Vector2(f["pixel"][0], f["pixel"][1])
		var body := StaticBody2D.new()
		body.position = px + Vector2(size.x / 2.0, size.y)   # origin = bottom-center (for y-sort)
		var spr := Sprite2D.new()
		spr.texture = tex
		spr.centered = false
		spr.offset = Vector2(-size.x / 2.0, -size.y)
		body.add_child(spr)
		var flat := false
		for p in NO_COLLIDE:
			if fid.begins_with(p):
				flat = true
		if flat:
			body.z_index = -1 if fid.begins_with("rug_") else 0
		else:
			var cs := CollisionShape2D.new()
			var sh := RectangleShape2D.new()
			sh.size = Vector2(size.x - 6.0, 14.0)
			cs.shape = sh
			cs.position = Vector2(0, -9)
			body.add_child(cs)
		props.add_child(body)


func spawn_point() -> Vector2:
	return Vector2(door_tile.x * 32 + 16, door_tile.y * 32 + 8)


func _furniture_index() -> Dictionary:
	var out := {}
	var cat: Dictionary = RPGSheet.catalog("furniture/furniture.json")
	for it in cat.get("items", []):
		out[it["id"]] = it
	return out
