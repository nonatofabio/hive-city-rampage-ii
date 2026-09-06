extends SceneTree
var failures:=0
func _initialize() -> void:
	run.call_deferred()
func check(ok: bool, label: String) -> void:
	if not ok: failures+=1; push_error(label)
func run() -> void:
	var game: SiegeGame=load("res://scenes/main.tscn").instantiate()
	root.add_child(game); game.test_mode=true; game.set_physics_process(false)
	game.level=2; game.reset(); game.spawn_timer=10000
	check(game.enemies.all(func(e):return not e.custom_sheet.is_empty()),"Iron Belly uses Ork sheets")
	var pump:=game.relays[0]
	game.hit(pump,100000)
	check(pump.hp>0,"Pumps require securing rather than shooting")
	game.player.world_pos=pump.world_pos+Vector2(70,0)
	var contest:=game.spawn(pump.world_pos+Vector2(0,40),"grunt")
	game.update_level_two(1)
	check(game.capture_progress[0]==0,"Nearby Orks contest capture")
	for enemy in game.enemies: enemy.queue_free()
	game.enemies.clear()
	for i in 3:
		game.player.world_pos=game.relays[i].world_pos+Vector2(70,0)
		for frame in 481: game.update_level_two(1.0/60)
	check(game.relays_down()==3,"All three pumps can be secured")
	game.tick(1.0/60,Vector2.ZERO,Vector2.ZERO,false,false)
	check(game.boss_spawned,"Securing pumps summons Warboss")
	var boss:SiegeActor=game.enemies.filter(func(e):return e.kind=="boss")[0]
	check(boss.custom_sheet.ends_with("warboss.png"),"Warboss uses dedicated art")
	game.hit(boss,10000); game.player.world_pos=game.extraction
	game.tick(1.0/60,Vector2.ZERO,game.extraction,false,false)
	check(game.state=="won","Level two can be completed")
	game.level=1; game.reset(); game.state="won"
	var next:=InputEventKey.new(); next.physical_keycode=KEY_N; next.pressed=true
	game._unhandled_input(next)
	check(game.level==2 and game.state=="playing","Campaign advances from Ashgate to Iron Belly")
	game.reset(); game.hurt_timer=0; game.time=0; game.hazard_cooldown=0
	game.player.world_pos=Iso.vec(game.hazards[0]); var shield:=game.shield
	game.update_level_two(0.1)
	check(game.shield<shield,"Active hazard damages player")
	game.reset(); check(game.capture_progress==[0.0,0.0,0.0],"Restart clears pump progress")
	if failures: quit(1)
	else: print("LEVEL TWO PASS: Orks, capture/contest, hazards, Warboss, extraction, campaign, reset"); quit()
