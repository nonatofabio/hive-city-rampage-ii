extends SceneTree
## Native Sprite2D review: all source views, each gait phase, forward and retreat.
func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Torso review requires a rendering display")
		quit(1)
		return
	root.size = Vector2i(1000,560)
	root.content_scale_size = Vector2i(1000,560)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	var poses := PoseLibrary.new()
	var stage := Node2D.new()
	root.add_child(stage)
	DirAccess.make_dir_recursive_absolute("res://artifacts")
	for step in range(4):
		for row in range(2):
			var column := 0
			for view: int in PoseLibrary.VIEWS:
				var actor: SiegeActor = preload("res://scenes/actor.tscn").instantiate()
				actor.configure({"kind":"player","position":[0,0],"hp":100,"radius":16})
				stage.add_child(actor)
				actor.moving = true
				actor.stride = (step + 0.05) / 4.0
				actor.aim_view = view
				actor.aim_angle = view
				actor.move_angle = view if row == 0 else -view
				actor.move_facing = 1 if row == 0 else -1
				actor.refresh(poses,0,Vector2(200,0))
				actor.position = Vector2(100 + column*200,240 + row*270)
				actor.scale = Vector2(2,2)
				var label := Label.new()
				label.text = "%d° / %s / step %d" % [view,"forward" if row == 0 else "retreat",step]
				label.position = Vector2(20 + column*200,12 + row*270)
				label.add_theme_font_size_override("font_size",14)
				stage.add_child(label)
				column += 1
		await process_frame
		await RenderingServer.frame_post_draw
		var path := "res://artifacts/torso-step-%d.png" % step
		if root.get_texture().get_image().save_png(path) != OK:
			push_error("Could not save torso review")
			quit(1)
			return
		for child in stage.get_children():
			stage.remove_child(child)
			child.queue_free()
	print("TORSO CAPTURE PASS: five views, four gait phases, forward and retreat")
	stage.queue_free()
	await process_frame
	quit()
