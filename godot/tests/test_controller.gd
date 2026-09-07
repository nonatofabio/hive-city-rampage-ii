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
	var cursor_start := game.controller_cursor
	axis(JOY_AXIS_LEFT_X,1.0)
	axis(JOY_AXIS_RIGHT_Y,-1.0)
	step()
	check(game.player.world_pos.distance_to(origin)>1.0,"Physical left stick moves with touch enabled")
	check(game.shots.is_empty(),"Physical right stick aims without firing with touch enabled")
	check(game.controller_cursor.x == cursor_start.x and game.controller_cursor.y < cursor_start.y,"Right stick moves cursor up from its previous screen position")
	axis(JOY_AXIS_LEFT_X,0.0)
	axis(JOY_AXIS_RIGHT_Y,0.0)
	game.player.cooldown = 0.0
	step()
	check(game.player.cooldown == 0.0,"Neutral right stick does not fire")
	var held_cursor := game.controller_cursor
	axis(JOY_AXIS_LEFT_X,1.0)
	step()
	check(game.controller_cursor == held_cursor,"Cursor stays at its screen position while player/camera move")
	axis(JOY_AXIS_LEFT_X,0.0)
	axis(JOY_AXIS_RIGHT_X,1.0)
	for i in range(100):
		step()
	check(game.controller_cursor.x == 948.0,"Cursor reaches and clamps to screen edge instead of orbiting player")
	axis(JOY_AXIS_RIGHT_X,-0.5)
	step()
	check(game.controller_cursor.x < 948.0 and game.controller_cursor.x > 940.0,"Partial stick deflection moves cursor precisely back from edge")
	axis(JOY_AXIS_RIGHT_X,0.0)
	axis(JOY_AXIS_TRIGGER_RIGHT,1.0)
	step()
	check(game.player.cooldown>0.0,"R2 fires along retained aim")
	for released_value in [0.0,0.5,0.51,-1.0]:
		axis(JOY_AXIS_TRIGGER_RIGHT,1.0)
		step()
		check(game.controller_fire_pressed,"R2 press starts firing")
		axis(JOY_AXIS_TRIGGER_RIGHT,released_value)
		game.player.cooldown = 0.0
		step()
		check(game.player.cooldown == 0.0 and not game.controller_fire_pressed,"R2 releases for centered and zero-based Android trigger mappings")
	axis(JOY_AXIS_TRIGGER_LEFT,0.5)
	check(game.grenades == 5,"L2 dead zone ignores trigger noise")
	axis(JOY_AXIS_TRIGGER_LEFT,1.0)
	check(game.grenades == 4,"L2 throws one grenade")
	game.grenade_cd = 0.0
	axis(JOY_AXIS_TRIGGER_LEFT,0.9)
	check(game.grenades == 4,"Holding L2 never repeats grenades after cooldown")
	axis(JOY_AXIS_TRIGGER_LEFT,0.5)
	axis(JOY_AXIS_TRIGGER_LEFT,1.0)
	check(game.grenades == 3,"Releasing and pressing L2 throws another grenade")
	axis(JOY_AXIS_TRIGGER_LEFT,0.0)
	tap(JOY_BUTTON_LEFT_SHOULDER)
	button(JOY_BUTTON_DPAD_RIGHT)
	button(JOY_BUTTON_RIGHT_SHOULDER)
	step()
	check(game.grenades == 3 and game.dash_cd == 0.0,"Shoulders no longer throw or dash")
	button(JOY_BUTTON_RIGHT_SHOULDER,false)
	button(JOY_BUTTON_LEFT_STICK)
	step()
	check(game.dash_cd>0.0,"Left stick click dashes with D-pad movement")
	button(JOY_BUTTON_DPAD_RIGHT,false)
	button(JOY_BUTTON_LEFT_STICK,false)
	axis(JOY_AXIS_TRIGGER_RIGHT,1.0)
	tap(JOY_BUTTON_START)
	check(not game.controller_fire_pressed,"Pause clears held trigger firing")
	check(game.paused,"Start pauses")
	game.grenade_cd = 0.0
	var frozen := game.time
	axis(JOY_AXIS_TRIGGER_LEFT,1.0)
	step()
	check(game.time == frozen and game.grenades == 3,"Pause blocks simulation and grenades")
	axis(JOY_AXIS_TRIGGER_LEFT,0.0)
	tap(JOY_BUTTON_A)
	check(not game.paused,"A resumes")
	check(not game.controller_fire_pressed,"Resume requires fresh trigger input")
	axis(JOY_AXIS_TRIGGER_RIGHT,0.5)
	game.state = "dead"
	tap(JOY_BUTTON_A)
	check(game.state == "playing" and game.player.hp == 100,"A retries after death")
	game.level = 1
	game.state = "won"
	tap(JOY_BUTTON_A)
	check(game.level == 2 and game.state == "playing","A advances campaign")
	axis(JOY_AXIS_TRIGGER_RIGHT,1.0)
	game._controller_connection_changed(2,false)
	check(not game.controller_fire_pressed,"Disconnect clears firing")
	check(game.paused,"Disconnect pauses gameplay")
	tap(JOY_BUTTON_B)
	check(game.at_title,"B returns to title from pause")
	game.title_screen.toggle_orders()
	tap(JOY_BUTTON_START)
	check(game.at_title and not game.title_screen.show_orders,"Start closes orders without deploying underneath")
	game.title_screen.toggle_orders()
	tap(JOY_BUTTON_B)
	check(game.at_title and not game.title_screen.show_orders,"B closes orders")
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
