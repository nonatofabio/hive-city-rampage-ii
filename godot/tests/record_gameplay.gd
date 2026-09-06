extends SceneTree
## Real combat, driven by reproducible movement/aim/fire inputs; no scripted damage.
var game: SiegeGame
var frame := 0
var stopping := false
func _initialize() -> void:
	setup.call_deferred()
func setup() -> void:
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.test_mode = true
	game.set_physics_process(false)
func _process(_dt: float) -> bool:
	if stopping or not is_instance_valid(game) or not is_instance_valid(game.player):
		return false
	var target := Vector2(560,210)
	var waypoint := Vector2(450,350)
	if frame >= 75:
		target = Vector2(470,530)
		waypoint = Vector2(560,370)
	if frame >= 135:
		target = game.relays[0].world_pos
		waypoint = Vector2(650,360)
	if frame >= 240:
		var alive := game.enemies.filter(func(e): return e.hp>0)
		if not alive.is_empty():
			alive.sort_custom(func(a,b): return a.world_pos.distance_squared_to(game.player.world_pos)<b.world_pos.distance_squared_to(game.player.world_pos))
			target = alive[0].world_pos
		waypoint = Vector2(780,490)
	var movement := Iso.project(waypoint-game.player.world_pos).normalized() if game.player.world_pos.distance_to(waypoint)>15 else Vector2.ZERO
	if frame in [150,255,330]:
		game.grenade(target)
	for step in 2:
		game.tick(1.0/60,movement,target,true,false)
	game.refresh_visuals(1.0/30)
	frame += 1
	if frame >= 420:
		print("RECORD PASS: 14 seconds, %d kills, %d relays, %d wrecks" % [game.kills,game.relays_down(),game.cover.filter(func(p): return p.hp<=0).size()])
		stopping = true
		finish.call_deferred()
	return false

func finish() -> void:
	game.queue_free()
	await process_frame
	game = null
	quit()
