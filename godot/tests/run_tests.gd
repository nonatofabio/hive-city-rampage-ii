extends SceneTree
var checks := 0
var failures: Array[String] = []
var game: SiegeGame

func _initialize() -> void:
	run.call_deferred()

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)
		push_error(label)

func near(a: Vector2, b: Vector2, label: String) -> void:
	check(a.distance_to(b) < 0.001,label + " expected %s got %s" % [b,a])

func clean_arena() -> void:
	game.reset()
	for actor: SiegeActor in game.enemies + game.cover + game.relays:
		actor.queue_free()
	game.enemies.clear()
	game.cover.clear()
	game.relays.clear()
	game.spawn_timer = 10000.0
	game.player.world_pos = Vector2(320,360)
	game.muted = true

func run() -> void:
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.test_mode = true
	game.set_physics_process(false)
	game.muted = true
	var reference: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/pygame_reference.json"))
	for item: Dictionary in reference.poses:
		var key := game.poses.pose(item.kind,item.stride,item.moving,item.angle,item.recoil,item.time)
		check(key.model == item.key[0] and key.clip == item.key[1] and key.index == int(item.key[2]),"Reference pose %s" % str(item.key))
		var geo := game.poses.geometry(item.kind,key,item.facing)
		near(geo.size,Iso.vec(item.size),"Frame size")
		near(geo.anchor,Iso.vec(item.anchor),"Anchor")
		near(geo.muzzle,Iso.vec(item.muzzle),"Muzzle")
		near(geo.ejection-geo.anchor,Iso.vec(item.port),"Ejection")
	for item: Dictionary in reference.gaits:
		var a: Array = item.args
		var actual := PoseLibrary.gait_pose(a[0],a[1],a[2],a[3],a[4])
		check(actual == Vector3i(item.result[0],item.result[1],item.result[2]),"Gait %s" % str(a))
	for item: Dictionary in reference.aims:
		game.player.stride = 0.413
		game.player.recoil = 0.082
		game.player.moving = item.moving
		game.player.facing = int(item.facing)
		near(game.poses.best_aim(game.player,item.view,1.23,Iso.vec(item.target)),Iso.vec(item.result),"Aim solution %s" % str(item))
	for item: Dictionary in reference.movement:
		game.reset()
		var distance := game.move_actor(game.player,Iso.vec(item.delta))
		near(game.player.world_pos,Iso.vec(item.pos),"World movement")
		check(absf(distance-item.distance)<0.001 and absf(game.player.stride-item.stride)<0.001,"Distance and stride")
	for item: Dictionary in reference.layers:
		var actor := game.player
		actor.aim_view = int(item.view)
		actor.aim_angle = float(item.view)
		actor.facing = int(item.facing)
		actor.moving = item.moving
		actor.recoil = item.recoil
		actor.stride = item.stride
		actor.move_angle = -int(item.view)
		actor.move_facing = -int(item.facing)
		var key := actor.pose_key(game.poses,0.0)
		var gait := game.poses.lower_pose(key,actor.facing,actor.stride,actor.moving,actor.move_angle,actor.move_facing)
		check(gait==Vector3i(item.gait[0],item.gait[1],item.gait[2]),"Action/contact pose %s" % str(item))
		near(game.poses.lower_origin(key,actor.facing),Iso.vec(item.origin),"Belt overlap")
		actor.refresh(game.poses,0.0,Vector2(500,400))
		check(actor.lower.visible and actor.body.texture.resource_path.contains("/upper/"),"All actions use unified body layers")
		near(actor.lower.position-actor.body.position,Iso.vec(item.origin),"Actual Sprite2D layer placement")
	for p: Vector2 in [Vector2.ZERO,Vector2(2400,700),Vector2(-20,31),Vector2(320,360)]:
		near(Iso.unproject(Iso.project(p)),p,"Projection round trip")
	check(is_equal_approx(Iso.segment_entry(Vector2.ZERO,Vector2(100,0),Vector2(50,0),10),0.4),"Swept hit entry")
	check(Iso.segment_entry(Vector2.ZERO,Vector2.ZERO,Vector2.ZERO,10)==0.0,"Overlapping stationary shot")
	check(Iso.segment_entry(Vector2.ZERO,Vector2(100,0),Vector2(50,20),10)<0.0,"Shot misses")
	clean_arena()
	var obstacle := game.make_actor({"position":[400,360],"kind":"crate","hp":65,"radius":29})
	game.cover.append(obstacle)
	var enemy := game.spawn(Vector2(450,360),"grunt")
	game.shots.append({"pos":Vector2(320,360),"velocity":Vector2(1000,0),"damage":24,"enemy":false,"life":1.0})
	game.update_shots(0.2)
	check(obstacle.hp==41 and enemy.hp==45,"Nearest cover intercepts projectile before enemy")
	game.player.world_pos = Vector2(360,360)
	game.fire_weapon(game.player,enemy.world_pos,950,24)
	near(game.shots[0].pos,game.player.world_pos,"Muzzle cannot bypass adjacent cover")
	clean_arena()
	game.damage_player(70)
	check(game.shield==0 and game.player.hp==90,"Shield absorbs before health")
	game.damage_player(70)
	check(game.player.hp==90,"Hurt invulnerability")
	game.hurt_timer=0
	game.dash_time=0.1
	game.damage_player(70)
	check(game.player.hp==90,"Dash invulnerability")
	game.dash_time=0
	game.damage_player(100)
	check(game.state=="dead","Player death ends mission")
	clean_arena()
	game.grenade(Vector2(2000,360))
	check(game.grenades==4 and game.grenades_in_flight.size()==1,"Grenade inventory")
	near(game.grenades_in_flight[0].end,Vector2(750,360),"Grenade range clamp")
	game.grenade(Vector2(2000,360))
	check(game.grenades==4,"Grenade cooldown")
	game.update_transients(0.65)
	check(game.grenades_in_flight.is_empty(),"Grenade detonates and is removed")
	clean_arena()
	for x in [600,690,780]:
		game.cover.append(game.make_actor({"position":[x,360],"kind":"barrel","hp":28,"radius":29}))
	game.hit(game.cover[0],40)
	check(game.cover.all(func(a: SiegeActor) -> bool: return a.hp<=0),"Barrel chain reaction terminates")
	game.reset()
	game.muted=true
	game.player.world_pos=Vector2(320,600)
	for relay in game.relays:
		game.hit(relay,1000)
	check(game.relays_down()==3 and game.grenades==9,"Relay destruction and capped rewards")
	game.tick(1.0/60,Vector2.ZERO,Vector2(2000,400),false,false)
	var bosses: Array[SiegeActor] = game.enemies.filter(func(a: SiegeActor) -> bool: return a.kind=="boss")
	check(game.boss_spawned and bosses.size()==1,"Three relays spawn exactly one boss")
	var boss := bosses[0]
	boss.cooldown=0
	game.update_enemies(1.0/60)
	check(boss.phase==1.25,"Boss telegraph precedes damage")
	var locked := boss.target
	game.player.world_pos += Vector2(200,0)
	game.update_enemies(0.1)
	near(boss.target,locked,"Boss telegraph locks target")
	game.hit(boss,2000)
	check(game.boss_defeated,"Boss death opens extraction")
	game.player.world_pos=game.extraction
	game.tick(1.0/60,Vector2.ZERO,game.extraction,false,false)
	check(game.state=="won","Extraction completes mission")
	game.reset()
	check(game.state=="playing" and game.player.hp==100 and not game.boss_spawned and game.relays_down()==0,"Restart resets mission")
	game.paused=true
	var pos := game.player.world_pos
	game.tick(1.0,Vector2.RIGHT,Vector2.ZERO,true,true)
	near(game.player.world_pos,pos,"Pause freezes simulation")
	check(game.time==0 and game.shots.is_empty(),"Pause freezes clock and weapons")
	game.paused=false
	# Every exported clip must be importable and have valid frame/socket geometry.
	for model: String in game.poses.models:
		var data: Dictionary = game.poses.models[model]
		for clip_name: String in data.clips:
			var clip: Dictionary = data.clips[clip_name]
			var texture := game.poses.texture(clip.path)
			check(texture != null,"Texture exists " + clip.path)
			check(texture.get_width()==int(data.cell[0])*int(clip.count) and texture.get_height()==int(data.cell[1]),"Sheet dimensions " + clip.path)
			check(clip.muzzles.size()==int(clip.count) and clip.ejections.size()==int(clip.count),"Socket count " + clip_name)
	game.queue_free()
	await process_frame
	if failures.is_empty():
		print("TEST PASS: %d checks; Pygame motion parity, combat, mission, pause/restart, all runtime sheets" % checks)
		quit(0)
	else:
		print("TEST FAIL: %d / %d" % [failures.size(),checks])
		quit(1)
