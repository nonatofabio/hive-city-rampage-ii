extends SceneTree
var failures := 0

func _initialize() -> void:
	run.call_deferred()

func check(value: bool, message: String) -> void:
	if not value:
		failures+=1
		push_error(message)

func touch(index: int, point: Vector2, pressed: bool = true) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = point
	event.pressed = pressed
	# Inject viewport coordinates, matching touch events after window stretch mapping.
	root.push_input(event,true)

func run() -> void:
	var game: SiegeGame = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.test_mode = true
	game.muted = true
	var controls: Control = game.touch_controls
	check(controls.enabled,"Touch enabled in mobile preview")
	touch(0,Vector2(172,388))
	touch(1,Vector2(830,326))
	await process_frame
	check(controls.movement().x>0.9 and controls.firing(),"Simultaneous move and fire")
	check(controls.aim_direction.distance_to(Vector2.UP)<0.01,"Touch aiming direction")
	touch(0,Vector2(172,388),false)
	await process_frame
	check(controls.movement()==Vector2.ZERO and controls.firing(),"Independent finger release")
	touch(2,Vector2(680,365))
	await process_frame
	check(game.grenades==4,"Touch grenade")
	touch(2,Vector2(680,365),false)
	touch(3,Vector2(680,444))
	await process_frame
	check(controls.consume_dash() and not controls.consume_dash(),"Touch dash consumed once")
	touch(3,Vector2(680,444),false)
	touch(4,Vector2(900,130))
	await process_frame
	check(game.paused and not controls.firing(),"Touch pause clears held fire")
	touch(7,Vector2(480,400))
	await process_frame
	check(not game.muted,"Touch audio toggle")
	game.muted=true
	touch(4,Vector2(900,130),false)
	touch(5,Vector2(480,250))
	await process_frame
	check(not game.paused,"Touch resume")
	game.state="dead"
	touch(6,Vector2(480,250))
	await process_frame
	check(game.state=="playing" and game.player.hp==100,"Touch restart")
	touch(8,Vector2(830,326))
	await process_frame
	game.test_mode=false
	game._notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	check(game.paused and not controls.firing(),"Backgrounding releases touch inputs and pauses")
	game.queue_free()
	await process_frame
	if failures==0:
		print("TOUCH PASS: multitouch, aiming, release, grenade, dash, pause, resume, restart")
	quit(1 if failures else 0)
