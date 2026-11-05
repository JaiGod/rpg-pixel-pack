class_name InventoryUI
extends PanelContainer
## Inventory grid + equipment column. Click an item to equip it, click an equipped slot to unequip.
## Built entirely in code; just set `inventory` and `equipment`.

signal item_hovered(item: ItemData)

@export var columns: int = 6

var inventory: Inventory:
	set(v):
		inventory = v
		if inventory and not inventory.contents_changed.is_connected(refresh):
			inventory.contents_changed.connect(refresh)
		refresh()
var equipment: EquipmentComponent:
	set(v):
		equipment = v
		if equipment and not equipment.equipment_changed.is_connected(_on_equip_changed):
			equipment.equipment_changed.connect(_on_equip_changed)
		refresh()

var _grid: GridContainer
var _equip_box: VBoxContainer
var _info: Label
var _slot_tex: Texture2D
var _slot_sel_tex: Texture2D


func _ready() -> void:
	_slot_tex = load(RPGSheet.res_path("assets/ui/slot.png"))
	_slot_sel_tex = load(RPGSheet.res_path("assets/ui/slot_selected.png"))
	var sb := StyleBoxTexture.new()
	sb.texture = load(RPGSheet.res_path("assets/ui/panel.png"))
	for side in ["left", "top", "right", "bottom"]:
		sb.set("texture_margin_" + side, 8.0)
		sb.set("content_margin_" + side, 10.0)
	add_theme_stylebox_override("panel", sb)
	var root := HBoxContainer.new()
	root.add_theme_constant_override("separation", 10)
	add_child(root)
	var left := VBoxContainer.new()
	root.add_child(left)
	var title := Label.new()
	title.text = "Inventory"
	_style_label(title, 10)
	left.add_child(title)
	_grid = GridContainer.new()
	_grid.columns = columns
	_grid.add_theme_constant_override("h_separation", 2)
	_grid.add_theme_constant_override("v_separation", 2)
	left.add_child(_grid)
	_info = Label.new()
	_style_label(_info, 8)
	_info.custom_minimum_size = Vector2(0, 24)
	left.add_child(_info)
	_equip_box = VBoxContainer.new()
	_equip_box.add_theme_constant_override("separation", 2)
	root.add_child(_equip_box)
	refresh()


func _style_label(l: Label, size: int) -> void:
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color(0.18, 0.12, 0.1))


func _slot_button(item: ItemData, selected: bool) -> TextureButton:
	var b := TextureButton.new()
	b.texture_normal = _slot_sel_tex if selected else _slot_tex
	b.texture_hover = _slot_sel_tex
	b.custom_minimum_size = Vector2(36, 36)
	if item != null and item.icon != null:
		var icon := TextureRect.new()
		icon.texture = item.icon
		icon.position = Vector2(2, 2)
		icon.size = Vector2(32, 32)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(icon)
		b.tooltip_text = item.describe()
		b.mouse_entered.connect(_on_hover.bind(item))
	return b


func _on_hover(item: ItemData) -> void:
	_info.text = item.describe()
	item_hovered.emit(item)


func refresh() -> void:
	if _grid == null:
		return
	for c in _grid.get_children():
		c.queue_free()
	for c in _equip_box.get_children():
		c.queue_free()
	if inventory != null:
		for i in inventory.slots.size():
			var it: ItemData = inventory.slots[i]
			var b := _slot_button(it, false)
			b.pressed.connect(_on_inventory_pressed.bind(i))
			_grid.add_child(b)
	var t := Label.new()
	t.text = "Equipped"
	_style_label(t, 10)
	_equip_box.add_child(t)
	for slot in EquipmentComponent.SLOTS:
		var row := HBoxContainer.new()
		var it: ItemData = equipment.get_item(slot) if equipment else null
		var b := _slot_button(it, it != null)
		b.pressed.connect(_on_equipped_pressed.bind(slot))
		row.add_child(b)
		var l := Label.new()
		l.text = slot.capitalize()
		_style_label(l, 8)
		row.add_child(l)
		_equip_box.add_child(row)
	if equipment:
		var stats := Label.new()
		stats.text = "ATK %d\nDEF %d\nMAG %d" % [equipment.total("attack"), equipment.total("defense"), equipment.total("magic")]
		_style_label(stats, 8)
		_equip_box.add_child(stats)


func _on_inventory_pressed(i: int) -> void:
	if inventory == null or equipment == null:
		return
	var it := inventory.slots[i]
	if it == null:
		return
	inventory.slots[i] = null
	var prev := equipment.equip(it)
	if prev != null:
		inventory.slots[i] = prev
	inventory.contents_changed.emit()


func _on_equipped_pressed(slot: String) -> void:
	if equipment == null or equipment.get_item(slot) == null:
		return
	var it := equipment.unequip(slot)
	if not inventory.add(it):
		equipment.equip(it)


func _on_equip_changed(_slot: String, _item: ItemData) -> void:
	refresh()
