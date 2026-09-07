extends SceneTree
var game: SiegeGame
var failures := 0
func _initialize() -> void:
	run.call_deferred()
func check(ok: bool, message: String) -> void:
	if not ok:
		failures+=1
		push_error(message)
func arena() -> void:
	game.reset()
	for actor in game.enemies+game.cover+game.relays:
		actor.queue_free()
	game.enemies.clear()
	game.cover.clear()
	game.relays.clear()
	game.player.world_pos=Vector2(320,360)
	game.spawn_timer=1000
func run() -> void:
	game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	arena()
	var enemy:=game.spawn(Vector2(365,360),"brute")
	enemy.cooldown=100
	game.tick(1.0/60,Vector2.ZERO,Vector2(900,360),false,false)
	check(enemy.hp==125,"Nearby enemy is not attacked without fire input")
	game.tick(1.0/60,Vector2.ZERO,Vector2(900,360),true,false)
	check(enemy.hp==55 and game.shots.is_empty() and game.player.melee_time>0,"Fire in reach uses chainsword damage and visible swing instead of bolter")
	game.tick(1.0/60,Vector2.ZERO,Vector2(900,360),true,false)
	check(enemy.hp==55,"Chainsword cooldown prevents per-frame damage")
	check(is_instance_valid(game.player.chainsword),"Chainsword attached to player")
	arena()
	enemy=game.spawn(Vector2(500,360),"brute")
	game.tick(1.0/60,Vector2.ZERO,enemy.world_pos,true,false)
	check(game.player.melee_time==0 and not game.shots.is_empty(),"Distant targets use bolter")
	arena()
	enemy=game.spawn(Vector2(365,360),"brute")
	var wall:=game.make_actor({"kind":"barricade","position":[345,360],"hp":100,"radius":10})
	wall.remains_solid=true
	game.cover.append(wall)
	check(game.melee_target()==null,"Chainsword cannot reach through permanent cover")
	for mode in ["WIDE","NORMAL","CLOSE"]:
		game.set_view(mode)
		var point:=Vector2(700,490)
		var screen:=game.world_to_screen(point,55)
		check(game.cursor_aim(screen).distance_to(point)<0.01,"FOV screen-to-world aiming round trip: "+mode)
		check(game.world.scale==Vector2.ONE*game.view_zoom,"FOV scales world, not HUD")
	game.set_view("NORMAL")
	game.show_title()
	game.title_screen.open_options()
	check(game.title_screen.show_options and not game.title_screen.deploy.visible,"Options hides menu")
	var speed:=game.cursor_speed_index
	game.title_screen.cycle_speed()
	check(game.cursor_speed_index!=(speed),"Cursor speed changes")
	game.title_screen.cycle_view()
	check(game.view_mode=="CLOSE","View selection changes")
	game.save_settings("user://upgrade-test-settings.cfg")
	game.cursor_speed_index=0
	game.set_view("WIDE")
	game.load_settings("user://upgrade-test-settings.cfg")
	check(game.cursor_speed_index!=0 and game.view_mode=="CLOSE","Options persist through save/load")
	DirAccess.remove_absolute("user://upgrade-test-settings.cfg")
	game.title_screen.close_options()
	game.start_mission()
	game.toggle_pause()
	game.title_screen.open_options()
	check(game.paused and game.title_screen.visible and not game.hud.visible,"Options can open during pause")
	game.title_screen.close_options()
	check(game.paused and not game.title_screen.visible and game.hud.visible,"Closing options returns to frozen pause screen")
	game.toggle_pause()
	game.muted=false
	game.sfx_volume=0.8
	game.play_shot()
	game.play_sound("grenade",3)
	game.play_sound("relay",2)
	game.play_sound("chainsword",3)
	check(game.audio_voices[0].stream.resource_path.contains("bolter"),"Bolter sound routed to gun voice pool")
	check(game.audio_voices[8].stream.resource_path.contains("grenade") and game.audio_voices[9].stream.resource_path.contains("relay"),"Grenade and relay have distinct audio")
	for kind in ["bolter","grenade","relay","chainsword"]:
		var sound: AudioStream=load("res://assets/audio/%s_0.wav"%kind)
		check(sound.get_length()>0.3,"Generated audio imports: "+kind)
	for voice in game.audio_voices:
		voice.stream_paused=false
		voice.stop()
		voice.stream=null
	game.sound_cache.clear()
	await create_timer(0.25).timeout
	game.queue_free()
	await process_frame
	if failures==0:
		print("UPGRADE PASS: chainsword range/cooldown/cover, zoom aiming, options, distinct sound pools")
	quit(1 if failures else 0)
