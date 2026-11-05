class_name Inventory
extends Resource
## Fixed-size slot inventory of ItemData. Save it with ResourceSaver like any resource.

signal contents_changed

@export var size: int = 24:
	set(v):
		size = v
		slots.resize(size)
@export var slots: Array[ItemData] = []
@export var gold: int = 0


func _init() -> void:
	slots.resize(size)


func add(item: ItemData) -> bool:
	for i in slots.size():
		if slots[i] == null:
			slots[i] = item
			contents_changed.emit()
			return true
	return false


func remove_at(index: int) -> ItemData:
	if index < 0 or index >= slots.size():
		return null
	var it := slots[index]
	slots[index] = null
	contents_changed.emit()
	return it


func swap(a: int, b: int) -> void:
	var t := slots[a]
	slots[a] = slots[b]
	slots[b] = t
	contents_changed.emit()


func count() -> int:
	var n := 0
	for s in slots:
		if s != null:
			n += 1
	return n


func load_items(ids: PackedStringArray) -> void:
	for id in ids:
		var path := "%s/resources/items/%s.tres" % [RPGSheet.PACK, id]
		if ResourceLoader.exists(path):
			add(load(path))
