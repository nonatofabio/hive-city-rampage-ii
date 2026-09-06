extends SceneTree
var game: SiegeGame
var failures := 0
func _initialize() -> void:
	run.call_deferred()
func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)
func run() -> void:
	root.size = Vector2i(960,540)
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.test_mode = true
	game.show_title()
	await process_frame
	check(game.at_title and not game.hud.visible and not game.touch_controls.visible,"Title hides gameplay UI")
	game._physics_process(1.0)
	check(game.time == 0.0,"Mission must not advance behind title")
	game.title_screen.toggle_orders()
	check(game.title_screen.show_orders,"Field orders open")
	game.title_screen.toggle_orders()
	var muted := game.muted
	game.title_screen.toggle_audio()
	check(game.muted != muted,"Audio toggle persists into deployment")
	game.title_screen.toggle_audio()
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://artifacts/title-screen.png")
	# Route actual GUI mouse events through the viewport, rather than emitting a signal.
	var motion := InputEventMouseMotion.new()
	motion.position = Vector2(480,360)
	root.push_input(motion,true)
	await process_frame
	for pressed in [true,false]:
		var event := InputEventMouseButton.new()
		event.position = Vector2(480,360)
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		event.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
		root.push_input(event,true)
		await process_frame
	check(not game.at_title and game.hud.visible,"Deploy mouse button starts mission")
	check(game.grenades == 5 and game.time == 0.0,"Menu input must not consume grenades or advance mission")
	game.show_title()
	# Android uses the same native GUI via touch-to-mouse emulation.
	for pressed in [true,false]:
		var event := InputEventScreenTouch.new()
		event.index = 0
		event.position = Vector2(480,360)
		event.pressed = pressed
		Input.parse_input_event(event)
		await process_frame
	check(not game.at_title,"Touch deploy starts mission")
	game.toggle_pause()
	check(game.paused,"Pause works after title deployment")
	game.reset()
	check(not game.paused and game.state == "playing","Restart still works")
	if failures > 0:
		quit(1)
		return
	print("TITLE PASS: frozen menu, orders, audio, mouse/touch deployment, pause and restart")
	quit()
