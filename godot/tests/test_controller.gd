extends SceneTree
var game: SiegeGame
var failures := 0

func _initialize() -> void:
	run.call_deferred()

func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)

func button(index: int, pressed: bool = true) -> void:
	var event := InputEventJoypadButton.new()
	event.device = 2
	event.button_index = index
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func tap(index: int) -> void:
	button(index)
	button(index,false)

func axis(index: int, value: float) -> void:
	var event := InputEventJoypadMotion.new()
	event.device = 2
	event.axis = index
	event.axis_value = value
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func step() -> void:
	game.test_mode = false
	game._physics_process(1.0/60.0)
	game.test_mode = true

func run() -> void:
	root.size = Vector2i(960,540)
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.show_title()
	await process_frame
	check(root.gui_get_focus_owner() == game.title_screen.deploy,"Title initially focuses Deploy")
	tap(JOY_BUTTON_DPAD_UP)
	check(root.gui_get_focus_owner() == game.title_screen.level_button,"D-pad navigates title")
	var old_level := game.level
	tap(JOY_BUTTON_A)
	check(game.level != old_level,"Controller selects mission")
	tap(JOY_BUTTON_DPAD_DOWN)
	tap(JOY_BUTTON_A)
	check(not game.at_title,"Controller deploys through native GUI")
	check(game.grenades == 5,"Deploy does not throw a grenade")
	check(game.touch_controls.enabled,"Test includes Android touch controls")
	var origin := game.player.world_pos
	axis(JOY_AXIS_LEFT_X,0.1)
	axis(JOY_AXIS_RIGHT_Y,-0.1)
	step()
	check(game.player.world_pos == origin and game.shots.is_empty(),"Dead zones prevent drift and firing")
	axis(JOY_AXIS_LEFT_X,1.0)
	axis(JOY_AXIS_RIGHT_Y,-1.0)
	step()
	check(game.player.world_pos.distance_to(origin)>1.0,"Physical left stick moves with touch enabled")
	check(not game.shots.is_empty(),"Physical right stick fires with touch enabled")
	check(Iso.project(game.aim-game.player.world_pos).normalized().dot(Vector2.UP)>0.99,"Physical aim follows screen direction")
	axis(JOY_AXIS_LEFT_X,0.0)
	axis(JOY_AXIS_RIGHT_Y,0.0)
	game.player.cooldown = 0.0
	step()
	check(game.player.cooldown == 0.0,"Releasing right stick stops firing")
	axis(JOY_AXIS_TRIGGER_RIGHT,1.0)
	step()
	check(game.player.cooldown>0.0,"R2 fires along retained aim")
	axis(JOY_AXIS_TRIGGER_RIGHT,0.0)
	tap(JOY_BUTTON_LEFT_SHOULDER)
	check(game.grenades == 4,"L1 throws one grenade")
	button(JOY_BUTTON_DPAD_RIGHT)
	button(JOY_BUTTON_RIGHT_SHOULDER)
	step()
	check(game.dash_cd>0.0,"R1 dashes with D-pad movement")
	button(JOY_BUTTON_DPAD_RIGHT,false)
	button(JOY_BUTTON_RIGHT_SHOULDER,false)
	tap(JOY_BUTTON_START)
	check(game.paused,"Start pauses")
	var frozen := game.time
	tap(JOY_BUTTON_LEFT_SHOULDER)
	step()
	check(game.time == frozen and game.grenades == 4,"Pause blocks simulation and grenades")
	tap(JOY_BUTTON_A)
	check(not game.paused,"A resumes")
	game.state = "dead"
	tap(JOY_BUTTON_A)
	check(game.state == "playing" and game.player.hp == 100,"A retries after death")
	game.level = 1
	game.state = "won"
	tap(JOY_BUTTON_A)
	check(game.level == 2 and game.state == "playing","A advances campaign")
	game._controller_connection_changed(2,false)
	check(game.paused,"Disconnect pauses gameplay")
	tap(JOY_BUTTON_B)
	check(game.at_title,"B returns to title from pause")
	tap(JOY_BUTTON_START)
	check(not game.at_title,"Start deploys from title")
	axis(JOY_AXIS_RIGHT_X,1.0)
	step()
	axis(JOY_AXIS_RIGHT_X,0.0)
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = Vector2(830,326)
	touch.pressed = true
	root.push_input(touch,true)
	game.player.cooldown = 0.0
	step()
	check(not game.controller_active and game.player.cooldown>0.0,"Touch aiming resumes after controller input")
	game.queue_free()
	await process_frame
	if failures == 0:
		print("CONTROLLER PASS: menu, device 2, dead zones, movement, aim/fire, trigger, grenade, dash, pause, retry, progression, disconnect, touch coexistence")
	quit(1 if failures else 0)
