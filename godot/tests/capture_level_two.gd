extends SceneTree
var game:SiegeGame
func _initialize() -> void: run.call_deferred()
func save(name_key:String) -> void:
	game.refresh_visuals(0); await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://artifacts/"+name_key+".png")
func run() -> void:
	root.size=Vector2i(960,540); root.content_scale_size=Vector2i(960,540)
	game=load("res://scenes/main.tscn").instantiate(); root.add_child(game); game.test_mode=true; game.set_physics_process(false)
	game.level=2; game.reset()
	await save("iron-belly-opening")
	for i in 420:
		var alive:=game.enemies.filter(func(e):return e.hp>0)
		var target:Vector2=alive[0].world_pos if not alive.is_empty() else game.relays[0].world_pos
		var destination:Vector2=game.relays[0].world_pos+Vector2(80,0)
		var movement:=Iso.project(destination-game.player.world_pos).normalized() if game.player.world_pos.distance_to(destination)>10 else Vector2.ZERO
		game.tick(1.0/60,movement,target,true,false); game.refresh_visuals(1.0/60)
		if i in [180,330]: game.grenade(target)
	await save("iron-belly-combat")
	game.queue_free(); await process_frame; print("LEVEL TWO CAPTURE PASS"); quit()
