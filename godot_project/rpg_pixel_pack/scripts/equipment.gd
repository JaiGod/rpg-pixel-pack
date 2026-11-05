class_name EquipmentComponent
extends Node
## Equipment slots that drive a LayeredCharacter's visual layers + combined stats.
##
##   $Equipment.equip(load("res://rpg_pixel_pack/resources/items/sword_flame.tres"))

signal equipment_changed(slot: String, item: ItemData)

const SLOTS := ["weapon", "offhand", "head", "torso", "cape"]

@export var character_path: NodePath

var equipped: Dictionary = {}   # slot -> ItemData
var _base: Dictionary = {}      # slot -> [style, primary, secondary] shown when unequipped


func _ready() -> void:
	var ch := _character()
	if ch == null:
		return
	# remember the character's own outfit so unequipping restores it
	await get_tree().process_frame
	for s in SLOTS:
		if ch.styles.has(s):
			_base[s] = ch.styles[s].duplicate()


func _character() -> LayeredCharacter:
	if character_path.is_empty():
		return null
	return get_node_or_null(character_path) as LayeredCharacter


## Equip an item; returns the item it replaced (or null).
func equip(item: ItemData) -> ItemData:
	if item == null:
		return null
	var prev: ItemData = equipped.get(item.slot)
	equipped[item.slot] = item
	_apply(item.slot)
	equipment_changed.emit(item.slot, item)
	return prev


func unequip(slot: String) -> ItemData:
	var prev: ItemData = equipped.get(slot)
	equipped.erase(slot)
	_apply(slot)
	equipment_changed.emit(slot, null)
	return prev


func get_item(slot: String) -> ItemData:
	return equipped.get(slot)


func total(stat: String) -> int:
	var t := 0
	for s in equipped:
		t += int(equipped[s].get(stat))
	return t


func _apply(slot: String) -> void:
	var ch := _character()
	if ch == null:
		return
	var item: ItemData = equipped.get(slot)
	if item != null and item.layer_style != "":
		ch.set_layer(slot, item.layer_style, item.primary_ramp, item.secondary_ramp)
	elif _base.has(slot):
		var b: Array = _base[slot]
		ch.set_layer(slot, b[0], b[1], b[2])
	else:
		ch.clear_layer(slot)
