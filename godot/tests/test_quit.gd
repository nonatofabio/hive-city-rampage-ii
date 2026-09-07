extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var game: SiegeGame = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.show_title()
	await process_frame
	game.title_screen.quit_button.grab_focus()
	# The process must exit through the actual GUI callback, before the watchdog.
	create_timer(0.5).timeout.connect(func():
		push_error("Quit button did not exit the application")
		quit(1)
	)
	for pressed in [true,false]:
		var event := InputEventJoypadButton.new()
		event.button_index = JOY_BUTTON_A
		event.device = 2
		event.pressed = pressed
		root.push_input(event,true)
	print("QUIT PASS: controller activates visible Quit button")
