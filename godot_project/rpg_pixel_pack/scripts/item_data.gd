class_name ItemData
extends Resource
## One equippable item. 62 ready-made items live in rpg_pixel_pack/resources/items/.
##
## slot: weapon | offhand | head | torso | cape
## layer_style: which character layer style to show when equipped (e.g. "plate", "knight_helm", "bow")
## primary_ramp / secondary_ramp: palette ramps applied to that layer (see assets/palette/ramps.json)

@export var id: String = ""
@export var name: String = ""
@export var category: String = ""
@export var icon: Texture2D
@export_enum("weapon", "offhand", "head", "torso", "cape") var slot: String = "weapon"
@export var layer_style: String = ""
@export var primary_ramp: String = ""
@export var secondary_ramp: String = ""
@export var attack: int = 0
@export var defense: int = 0
@export var magic: int = 0
@export var value: int = 0
@export var stackable: bool = false


func describe() -> String:
	var parts: PackedStringArray = []
	if attack:
		parts.append("ATK +%d" % attack)
	if defense:
		parts.append("DEF +%d" % defense)
	if magic:
		parts.append("MAG +%d" % magic)
	parts.append("%d gold" % value)
	return "%s\n%s" % [name, "  ".join(parts)]
