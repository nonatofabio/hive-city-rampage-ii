extends SceneTree
func _initialize() -> void:
	run.call_deferred()
func snapshot(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var error:=root.get_texture().get_image().save_png("res://artifacts/"+name+".png")
	if error!=OK:
		push_error("Capture failed")
		quit(1)
func run() -> void:
	root.size=Vector2i(960,540)
	var game: SiegeGame=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.controller_active=true
	game.muted=true
	game.start_mission()
	var enemy:=game.spawn(game.player.world_pos+Vector2(44,0),"brute")
	game.swing_chainsword(enemy)
	game.player.melee_time=.25
	for mode in ["WIDE","NORMAL","CLOSE"]:
		game.set_view(mode)
		game.refresh_visuals(0)
		await snapshot("upgrade-"+mode.to_lower())
	game.show_title()
	game.title_screen.open_options()
	await snapshot("upgrade-options")
	game.title_screen.close_options()
	game.title_screen.toggle_orders()
	await snapshot("upgrade-orders")
	game.queue_free()
	await process_frame
	print("UPGRADE CAPTURE PASS: three views, chainsword, options and orders")
	quit()
