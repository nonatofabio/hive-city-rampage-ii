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
	game.level=2
	game.reset()
func _process(_dt: float) -> bool:
	if stopping or not is_instance_valid(game) or not is_instance_valid(game.player):
		return false
	var alive:=game.enemies.filter(func(e):return e.hp>0)
	var target:Vector2=alive[0].world_pos if not alive.is_empty() else game.relays[0].world_pos
	var waypoint:Vector2=game.relays[0 if game.relays[0].hp>0 else 1].world_pos+Vector2(80,0)
	var movement:=Iso.project(waypoint-game.player.world_pos).normalized() if game.player.world_pos.distance_to(waypoint)>10 else Vector2.ZERO
	if frame in [90,210,360] and target.distance_to(game.player.world_pos)>150:
		game.grenade(target)
	for step in 2:
		game.tick(1.0/60,movement,target,true,false)
	game.refresh_visuals(1.0/30)
	frame += 1
	if frame >= 480:
		print("RECORD PASS: 16 seconds, %d kills, %d relays, %d wrecks" % [game.kills,game.relays_down(),game.cover.filter(func(p): return p.hp<=0).size()])
		stopping = true
		finish.call_deferred()
	return false

func finish() -> void:
	game.queue_free()
	await process_frame
	game = null
	quit()
