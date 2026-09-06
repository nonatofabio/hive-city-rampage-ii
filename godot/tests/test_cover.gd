extends SceneTree
var failures := 0
func _initialize() -> void:
	run.call_deferred()
func check(ok: bool, label: String) -> void:
	if not ok:
		failures += 1
		push_error(label)
func run() -> void:
	var game: SiegeGame = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.test_mode = true
	game.set_physics_process(false)
	for kind: String in SiegeActor.BREAKABLES:
		var prop := game.make_actor({"kind":kind,"position":[500,350],"hp":40,"radius":30})
		game.cover.append(prop)
		game.hit(prop,100)
		var score := game.score
		game.hit(prop,100)
		check(game.score == score,"Repeated damage must not repeat destruction rewards")
		prop.refresh(game.poses,game.time+120,Vector2.ZERO)
		check(prop.visible and prop.hp <= 0 and prop.body.texture.resource_path.ends_with(kind+"_wreck.png"),kind+" keeps its wreck after two minutes")
		game.player.world_pos = Vector2(450,350)
		game.move_actor(game.player,Vector2(50,0))
		check(game.player.world_pos.x == 500,kind+" wreck no longer blocks passage")
		game.cover.erase(prop)
		prop.queue_free()
	for kind: String in SiegeActor.PERMANENT:
		game.reset()
		# Isolate a firing lane to verify both teams' bullets stop at permanent cover.
		for prop: SiegeActor in game.cover + game.relays + game.enemies:
			prop.queue_free()
		game.cover.clear()
		game.relays.clear()
		game.enemies.clear()
		var prop := game.make_actor({"kind":kind,"position":[500,350],"hp":1000,"radius":30})
		game.cover.append(prop)
		game.hit(prop,100000)
		game.explode(prop.world_pos,160,100000)
		check(prop.hp == 1000,kind+" survives bullets and explosions")
		game.player.world_pos = Vector2(450,350)
		game.move_actor(game.player,Vector2(30,0))
		check(game.player.world_pos.x == 450,kind+" blocks movement")
		for enemy_shot in [false,true]:
			game.player.world_pos = Vector2(700,350)
			game.shots = [{"pos":Vector2(400,350),"velocity":Vector2(1000,0),"life":1.0,"damage":100000,"enemy":enemy_shot}]
			game.update_shots(0.2)
			check(game.shots.is_empty() and prop.hp == 1000,kind+" stops swept projectiles from either team")
	game.reset()
	game.refresh_visuals(0.0)
	check(game.cover.filter(func(p): return p.kind in SiegeActor.PERMANENT).size()==8,"Mission places eight permanent cover pieces")
	check(game.cover.all(func(p): return p.hp>0 and p.destroyed_at<0),"Restart restores all props")
	if failures:
		quit(1)
	else:
		print("COVER PASS: persistent wrecks, one-shot rewards, permanent cover, collisions, bullets, explosions, reset")
		quit()
