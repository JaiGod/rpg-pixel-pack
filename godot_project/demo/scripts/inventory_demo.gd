extends Node2D
## Inventory + equipment demo: click items to equip them on the layered hero.

const STARTER := ["sword_iron", "sword_flame", "sword_cyber", "axe_battle", "spear_halberd", "bow_elven", "crossbow_heavy",
	"staff_crystal", "staff_necro", "wand_star", "shield_kite", "shield_royal", "shield_energy", "shield_buckler",
	"helmet_knight", "helmet_wizard", "helmet_space", "helmet_horned", "cape_red", "cape_royal", "cape_shadow",
	"armor_plate", "armor_robe", "armor_cyber"]

var hero: LayeredCharacter
var equipment: EquipmentComponent
var inventory: Inventory


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.2, 0.26, 0.2)
	bg.size = Vector2(640, 360)
	add_child(bg)
	hero = LayeredCharacter.new()
	hero.name = "Hero"
	hero.position = Vector2(110, 230)
	hero.scale = Vector2(5, 5)
	hero.hair_style = "short"
	hero.hair_color = "hair_brown"
	hero.torso_style = "tunic"
	add_child(hero)
	equipment = EquipmentComponent.new()
	equipment.character_path = NodePath("../Hero")
	add_child(equipment)
	inventory = Inventory.new()
	inventory.size = 30
	inventory.load_items(PackedStringArray(STARTER))
	var ui := InventoryUI.new()
	ui.position = Vector2(220, 16)
	var layer := CanvasLayer.new()
	add_child(layer)
	layer.add_child(ui)
	ui.inventory = inventory
	ui.equipment = equipment
	equipment.equipment_changed.connect(_on_equipped)
	hero.action_finished.connect(_on_hero_action_done)
	var help := DemoWorld.make_label("Click an item to equip · click an equipped slot to unequip · arrows turn the hero · Esc menu", 8)
	help.position = Vector2(8, 344)
	layer.add_child(help)


func _on_equipped(_slot: String, _item: ItemData) -> void:
	hero.play_anim("attack", true)


func _on_hero_action_done(anim: String) -> void:
	if anim == "attack":
		hero.play_anim("idle")


func _unhandled_input(event: InputEvent) -> void:
	for pair in [["move_left", Vector2.LEFT], ["move_right", Vector2.RIGHT], ["move_up", Vector2.UP], ["move_down", Vector2.DOWN]]:
		if event.is_action_pressed(pair[0]):
			hero.face(pair[1])
