extends SceneTree
## Render reproducible review scenes without adding cheats to the shipped mission.
var game: SiegeGame

func _initialize() -> void:
	run.call_deferred()

func save_frame(name_key: String) -> void:
	game.refresh_visuals(0.0)
	await process_frame
	await RenderingServer.frame_post_draw
	var path := "res://artifacts/" + name_key + ".png"
	var error := root.get_texture().get_image().save_png(path)
	if error != OK:
		push_error("Capture failed: " + error_string(error))
		quit(1)
	print("CAPTURE " + ProjectSettings.globalize_path(path))

func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Scenario captures require a rendering display")
		quit(1)
		return
	root.size = Vector2i(960,540)
	root.content_scale_size = Vector2i(960,540)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	DirAccess.make_dir_recursive_absolute("res://artifacts")
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.test_mode = true
	game.set_physics_process(false)
	game.muted = true
	await save_frame("opening")
	game.paused = true
	await save_frame("pause")
	game.paused = false
	for enemy in game.enemies:
		enemy.queue_free()
	game.enemies.clear()
	for relay in game.relays:
		relay.hp = 0
	game.boss_spawned = true
	game.player.world_pos = Vector2(1920,370)
	game.camera_offset = Iso.project(game.player.world_pos)-Vector2(365,259)
	var boss := game.spawn(Vector2(2180,370),"boss")
	boss.phase = 0.7
	boss.target = game.player.world_pos+Vector2(80,0)
	game.aim = boss.world_pos
	game.player.moving = true
	game.player.stride = 0.51
	game.player.move_angle = -45
	game.aim_weapon(game.player,game.aim)
	game.message = "WARNING // SIEGE WALKER INBOUND"
	game.message_timer = 5
	await save_frame("boss")
	var blast := game.add_effect("explosion",game.player.world_pos+Vector2(150,0))
	blast.age = 0.15
	var death := game.add_effect("death",game.player.world_pos+Vector2(-90,70))
	death.age = 0.6
	death.actor_kind = "rifle"
	await save_frame("effects")
	game.hit(boss,2000)
	boss.phase = 0
	game.player.world_pos = game.extraction
	game.tick(1.0/60,Vector2.ZERO,game.extraction,false,false)
	await save_frame("victory")
	# Exercise every player movement/view combination through real Sprite2D nodes.
	for view: int in PoseLibrary.VIEWS:
		for facing in [-1,1]:
			game.reset()
			game.player.moving = true
			game.player.stride = 0.51
			game.player.aim_view = view
			game.player.aim_angle = view
			game.player.facing = facing
			game.player.move_angle = -view
			game.player.move_facing = -facing
			game.refresh_visuals(0.0)
			await process_frame
			await RenderingServer.frame_post_draw
	print("CAPTURE PASS: opening, pause, boss, effects, victory, directional animation")
	game.queue_free()
	await process_frame
	quit()
