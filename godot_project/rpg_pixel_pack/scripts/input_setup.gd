extends Node
## Autoload: registers the demo input actions (WASD/arrows, Shift run, Space/J attack,
## E interact, Tab/I inventory) and Esc to return to the demo menu.

const MENU := "res://demo/main_menu.tscn"

const ACTIONS := {
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"move_up": [KEY_W, KEY_UP],
	"move_down": [KEY_S, KEY_DOWN],
	"run": [KEY_SHIFT],
	"attack": [KEY_SPACE, KEY_J],
	"interact": [KEY_E, KEY_ENTER],
	"inventory": [KEY_TAB, KEY_I],
	"back_to_menu": [KEY_ESCAPE],
}


func _ready() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for key in ACTIONS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("back_to_menu"):
		var cur := get_tree().current_scene
		if cur != null and cur.scene_file_path != MENU:
			get_tree().change_scene_to_file(MENU)
