extends Node2D
## Walk through every furnished interior. Q / R (or PageUp / PageDown) switch rooms.

@onready var room: RoomLoader = $Room
@onready var player: PlayerController = $Player

var rooms: Array = []
var idx := 0
var _label: Label


func _ready() -> void:
	rooms = room.list_rooms()
	var layer := CanvasLayer.new()
	add_child(layer)
	_label = DemoWorld.make_label("", 10, Color(1, 0.88, 0.5))
	_label.position = Vector2(8, 6)
	layer.add_child(_label)
	var help := DemoWorld.make_label("WASD move · Q / R previous / next room · Esc menu", 8)
	help.position = Vector2(8, 344)
	layer.add_child(help)
	# move the player into the y-sorted furniture layer so it sorts with props
	player.reparent(room.props)
	_show(0)


func _show(i: int) -> void:
	idx = posmod(i, rooms.size())
	room.load_room(rooms[idx]["id"])
	player.global_position = room.to_global(room.spawn_point())
	_label.text = "%s  (%d / %d)  ·  %s" % [rooms[idx]["name"], idx + 1, rooms.size(), rooms[idx]["category"].replace("_", " ")]
	var cam: Camera2D = player.get_node("Camera2D")
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = room.room_size.x * 32
	cam.limit_bottom = room.room_size.y * 32


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_R or event.physical_keycode == KEY_PAGEDOWN:
			_show(idx + 1)
		elif event.physical_keycode == KEY_Q or event.physical_keycode == KEY_PAGEUP:
			_show(idx - 1)
