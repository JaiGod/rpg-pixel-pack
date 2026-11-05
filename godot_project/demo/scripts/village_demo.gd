extends Node2D
## Playable village: terrain-painted TileMapLayer, buildings, props, animated set dressing,
## wandering NPCs (talk with E) and monsters (attack with Space).

const MAP := Vector2i(44, 26)
const NPCS := [
	["merchant_trader", "male", "Trader Amir", ["Fresh wares from the desert!", "Gold talks, friend."]],
	["farmer_homesteader", "female", "Farmer Hilde", ["Slimes keep eating my turnips...", "The well water is the best around."]],
	["knight_royal_guard", "male", "Guard Bram", ["Stay out of the meadow after dark.", "The castle is north of here."]],
	["mage_apprentice", "female", "Apprentice Lin", ["The tower door is stuck again.", "Have you seen my wand?"]],
	["pirate_deckhand", "male", "Sailor Pip", ["Arr. Wrong biome, I know."]],
	["scientist_biologist", "female", "Dr. Vale", ["These slimes are fascinating!"]],
]
const MONSTERS := [["slime_green", Vector2(33, 20)], ["slime_blue", Vector2(36, 22)], ["slime_forest", Vector2(31, 23)],
	["goblin_grunt", Vector2(38, 19)], ["shadow_bat", Vector2(6, 22)]]

@onready var ground: TileMapLayer = $Ground
@onready var world: Node2D = $World
@onready var player: PlayerController = $World/Player

var _hud: Label
var _talk: Label


func _ready() -> void:
	_paint_ground()
	_place_town()
	_spawn_npcs()
	_spawn_monsters()
	_build_hud()
	player.global_position = Vector2(21 * 32, 13 * 32)
	player.health_changed.connect(_on_health)
	var cam: Camera2D = player.get_node("Camera2D")
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = MAP.x * 32
	cam.limit_bottom = MAP.y * 32


func _paint_ground() -> void:
	var c := RPGTerrain.empty_corners(MAP.x, MAP.y)
	RPGTerrain.fill_rect(c, Rect2i(0, 12, MAP.x, 1))          # main east-west road
	RPGTerrain.fill_rect(c, Rect2i(21, 0, 1, MAP.y))          # north-south road
	RPGTerrain.fill_ellipse(c, Vector2(21.5, 12.5), Vector2(4.5, 3.2))   # plaza
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	RPGTerrain.paint(ground, c, rng)
	# map border: fence obstacle tiles
	for x in MAP.x:
		if x < 20 or x > 23:
			RPGTerrain.obstacle(ground, Vector2i(x, 0), 1)
			RPGTerrain.obstacle(ground, Vector2i(x, MAP.y - 1), 1)


func _place_town() -> void:
	DemoWorld.add_building(world, "house_small_cottage", Vector2(6 * 32, 11 * 32))
	DemoWorld.add_building(world, "shop_general", Vector2(11 * 32, 11 * 32))
	DemoWorld.add_building(world, "inn_tavern", Vector2(29 * 32, 11 * 32))
	DemoWorld.add_building(world, "blacksmith_forge", Vector2(37 * 32, 11 * 32))
	DemoWorld.add_building(world, "shop_potion", Vector2(16 * 32, 11 * 32))
	DemoWorld.add_building(world, "tower_arcane", Vector2(41 * 32, 24 * 32))
	DemoWorld.add_building(world, "house_small_thatch", Vector2(6 * 32, 19 * 32))
	DemoWorld.add_building(world, "farm_red_barn", Vector2(13 * 32, 21 * 32))
	DemoWorld.add_prop(world, "well", Vector2(21.5 * 32, 15 * 32))
	DemoWorld.add_prop(world, "lamp_post", Vector2(19 * 32, 12 * 32))
	DemoWorld.add_prop(world, "lamp_post", Vector2(24 * 32, 12 * 32))
	DemoWorld.add_animation(world, "campfire", Vector2(25 * 32, 15.5 * 32))
	DemoWorld.add_animation(world, "flag_red", Vector2(26 * 32, 11 * 32))
	DemoWorld.add_animation(world, "windmill", Vector2(17 * 32, 22 * 32))
	var trees := ["tree_oak", "tree_cherry", "tree_autumn", "tree_big", "tree_pine"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in 26:
		var p := Vector2(rng.randi_range(1, MAP.x - 2), rng.randi_range(2, MAP.y - 2))
		if abs(p.y - 12.5) < 3.5 or abs(p.x - 21.5) < 3 or (p.y < 12 and p.x > 3 and p.x < 40) or (p.x > 3 and p.x < 17 and p.y > 15 and p.y < 22) or (p.x > 29 and p.y > 17):
			continue
		DemoWorld.add_prop(world, trees[i % trees.size()], p * 32)
	for x in [3, 4, 8, 9]:
		DemoWorld.add_furniture(world, "crate_wood" if x % 2 else "barrel_wood", Vector2(x * 32 + 16, 14 * 32))


func _spawn_npcs() -> void:
	var scn: PackedScene = load("res://rpg_pixel_pack/prefabs/npc.tscn")
	for i in NPCS.size():
		var d: Array = NPCS[i]
		var npc: NPCController = scn.instantiate()
		npc.npc_name = d[2]
		npc.lines = PackedStringArray(d[3])
		npc.position = Vector2((8 + i * 5) * 32, (13 + (i % 2) * 2) * 32)
		world.add_child(npc)
		var vis: CharacterSprite = npc.get_node("Visual")
		vis.sheet = DemoWorld.preset_sheet(d[0], d[1])
		vis.play_anim("idle", true)
		npc.talked.connect(_on_talk)


func _spawn_monsters() -> void:
	var scn: PackedScene = load("res://rpg_pixel_pack/prefabs/monster.tscn")
	for m in MONSTERS:
		var mon: MonsterController = scn.instantiate()
		mon.monster_id = m[0]
		mon.position = m[1] * 32
		world.add_child(mon)


func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hud = DemoWorld.make_label("", 8)
	_hud.position = Vector2(8, 6)
	layer.add_child(_hud)
	var help := DemoWorld.make_label("WASD move · Shift run · Space attack · E talk · Esc menu", 8, Color(0.85, 0.85, 0.95))
	help.position = Vector2(8, 344)
	layer.add_child(help)
	_talk = DemoWorld.make_label("", 8, Color(1, 0.9, 0.5))
	_talk.position = Vector2(8, 18)
	layer.add_child(_talk)
	_on_health(player.max_hp, player.max_hp)


func _on_health(hp: int, max_hp: int) -> void:
	_hud.text = "HP %d / %d" % [hp, max_hp]


func _on_talk(npc_name: String, line: String) -> void:
	_talk.text = "%s: %s" % [npc_name, line]
