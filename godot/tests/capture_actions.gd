extends SceneTree
## Offscreen native rendering of the final four action states in all eight directions.
func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1280,2000)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var background := ColorRect.new()
	background.size = Vector2(1280,2000)
	background.color = Color8(98,109,119)
	viewport.add_child(background)
	var stage := Node2D.new()
	viewport.add_child(stage)
	var poses := PoseLibrary.new()
	var directions := [[0,1,"E"],[45,1,"SE"],[90,1,"S"],[45,-1,"SW"],[0,-1,"W"],[-45,-1,"NW"],[-90,1,"N"],[-45,1,"NE"]]
	var actions := [[false,0.0,"IDLE"],[false,0.08,"FIRE"],[true,0.0,"WALK"],[true,0.08,"WALK FIRE"]]
	for row in range(4):
		for col in range(8):
			var direction: Array = directions[col]
			var actor: SiegeActor = preload("res://scenes/actor.tscn").instantiate()
			actor.configure({"kind":"player","position":[0,0],"hp":100,"radius":16})
			stage.add_child(actor)
			actor.aim_view = direction[0]
			actor.aim_angle = direction[0]
			actor.move_angle = direction[0]
			actor.facing = direction[1]
			actor.move_facing = direction[1]
			actor.moving = actions[row][0]
			actor.recoil = actions[row][1]
			actor.refresh(poses,0,Vector2(200,0))
			actor.muzzle_flash.hide()
			actor.shadow.hide()
			actor.position = Vector2(160+(col%4)*320,242+(row+(col/4)*4)*246)
			actor.scale = Vector2(2,2)
			var label := Label.new()
			label.text = "%s / %s" % [actions[row][2],direction[2]]
			label.position = Vector2(12+(col%4)*320,8+(row+(col/4)*4)*246)
			stage.add_child(label)
	await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute("res://artifacts")
	var path := "res://artifacts/actions-godot.png"
	if viewport.get_texture().get_image().save_png(path) != OK:
		push_error("Action capture failed")
		quit(1)
		return
	print("ACTION CAPTURE PASS: all four actions in eight directions")
	viewport.queue_free()
	await process_frame
	quit()
