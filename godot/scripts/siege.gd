class_name SiegeGame
extends Node2D
## Mission controller. Fixed-step combat deliberately retains the prototype's rules.
const ACTOR_SCENE := preload("res://scenes/actor.tscn")
const EFFECT_SCENE := preload("res://scenes/effect.tscn")
const HP := {"grunt":45.0, "rifle":35.0, "runner":24.0, "brute":125.0, "boss":1800.0}
const SPEED := {"grunt":72.0, "rifle":58.0, "runner":132.0, "brute":48.0, "boss":38.0}
var level := 1
var capture_progress := [0.0,0.0,0.0]
var hazards: Array = []
var hazard_cooldown := 0.0
var boss_salvo := 0.0
var poses := PoseLibrary.new()
var rng := RandomNumberGenerator.new()
var player: SiegeActor
var enemies: Array[SiegeActor] = []
var cover: Array[SiegeActor] = []
var relays: Array[SiegeActor] = []
var shots: Array[Dictionary] = []
var grenades_in_flight: Array[Dictionary] = []
var casings: Array[Dictionary] = []
var particles: Array[Dictionary] = []
var pickups: Array[Dictionary] = []
var marks: Array[Vector2] = []
var effects: Array[SiegeEffect] = []
var shield := 60.0
var hurt_timer := 0.0
var grenades := 5
var grenade_cd := 0.0
var dash_cd := 0.0
var dash_time := 0.0
var dash_direction := Vector2.RIGHT
var time := 0.0
var spawn_timer := 2.0
var score := 0
var kills := 0
var combo := 0
var combo_timer := 0.0
var boss_spawned := false
var boss_defeated := false
var state := "playing"
var paused := false
var camera_offset := Vector2.ZERO
var shake := 0.0
var message := "ASHGATE // BREAK THE SIGNAL"
var message_timer := 4.0
var aim := Vector2.ZERO
var muted := false
var sfx_volume := 0.8
var audio_voices: Array[AudioStreamPlayer] = []
var voice_index := 0
var audio_rng := RandomNumberGenerator.new()
var extraction := Vector2(2280,510)
var smoke_frames := 0
var frame_number := 0
var screenshot_path := ""
var capture_pending := false
var test_mode := false
var grenade_trigger_pressed := false
var controller_active := false
const TRIGGER_THRESHOLD := 0.55
const CURSOR_SPEED := 650.0
var controller_cursor := Vector2(565,304)
var controller_fire_pressed := false
var at_title := false
var seed_value := 7
@onready var world: Node2D = $World
@onready var actors: Node2D = $World/Actors
@onready var ground: Node2D = $World/Ground
@onready var airborne: Node2D = $World/Airborne
@onready var title_screen: Control = $Interface/TitleScreen
@onready var hud: Control = $Interface/HUD
@onready var touch_controls: Control = $Interface/TouchControls

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		match args[i]:
			"--level": level = clampi(int(args[i + 1]),1,2)
			"--seed": seed_value = int(args[i + 1])
			"--smoke-test": smoke_frames = int(args[i + 1])
			"--screenshot": screenshot_path = args[i + 1]
			"--mute": muted = true
			"--validation": test_mode = true
	_install_inputs()
	controller_active = not Input.get_connected_joypads().is_empty()
	Input.joy_connection_changed.connect(_controller_connection_changed)
	for i in range(8):
		var voice := AudioStreamPlayer.new()
		add_child(voice)
		audio_voices.append(voice)
	audio_rng.seed = seed_value + 97
	reset()
	if not test_mode and smoke_frames == 0:
		show_title()
	else:
		title_screen.hide()

func show_title() -> void:
	at_title = true
	controller_fire_pressed = false
	paused = false
	hud.hide()
	touch_controls.hide()
	touch_controls.clear_touches()
	title_screen.close_orders()
	title_screen.show()
	title_screen.sync_level()
	title_screen.deploy.grab_focus()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func start_mission() -> void:
	reset()
	at_title = false
	title_screen.hide()
	hud.show()
	touch_controls.visible = touch_controls.enabled
	if not touch_controls.enabled and not test_mode:
		Input.mouse_mode = Input.MOUSE_MODE_HIDDEN

func _bind(action: String, event: InputEvent) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action,0.2)
	if not InputMap.action_has_event(action,event):
		InputMap.action_add_event(action,event)

func _install_inputs() -> void:
	var bindings := {"move_left":KEY_A, "move_right":KEY_D, "move_up":KEY_W, "move_down":KEY_S, "dash":KEY_SHIFT, "grenade":KEY_SPACE}
	for action: String in bindings:
		var event := InputEventKey.new()
		event.physical_keycode = bindings[action]
		_bind(action,event)
	var buttons := {"ui_left":JOY_BUTTON_DPAD_LEFT, "ui_right":JOY_BUTTON_DPAD_RIGHT, "ui_up":JOY_BUTTON_DPAD_UP, "ui_down":JOY_BUTTON_DPAD_DOWN, "ui_accept":JOY_BUTTON_A, "ui_cancel":JOY_BUTTON_B, "move_left":JOY_BUTTON_DPAD_LEFT, "move_right":JOY_BUTTON_DPAD_RIGHT, "move_up":JOY_BUTTON_DPAD_UP, "move_down":JOY_BUTTON_DPAD_DOWN, "dash":JOY_BUTTON_LEFT_STICK, "pad_pause":JOY_BUTTON_START, "pad_confirm":JOY_BUTTON_A, "pad_back":JOY_BUTTON_B}
	for action: String in buttons:
		var event := InputEventJoypadButton.new()
		event.device = -1
		event.button_index = buttons[action]
		_bind(action,event)
	for binding: Array in [["move_left",JOY_AXIS_LEFT_X,-1.0],["move_right",JOY_AXIS_LEFT_X,1.0],["move_up",JOY_AXIS_LEFT_Y,-1.0],["move_down",JOY_AXIS_LEFT_Y,1.0],["aim_left",JOY_AXIS_RIGHT_X,-1.0],["aim_right",JOY_AXIS_RIGHT_X,1.0],["aim_up",JOY_AXIS_RIGHT_Y,-1.0],["aim_down",JOY_AXIS_RIGHT_Y,1.0],["pad_fire",JOY_AXIS_TRIGGER_RIGHT,1.0],["pad_grenade",JOY_AXIS_TRIGGER_LEFT,1.0]]:
		var event := InputEventJoypadMotion.new()
		event.device = -1
		event.axis = binding[1]
		event.axis_value = binding[2]
		_bind(binding[0],event)
	# Android full-axis mappings can normalize a released trigger to 0.5.
	for action: String in ["pad_fire","pad_grenade"]:
		InputMap.action_set_deadzone(action,TRIGGER_THRESHOLD)

func _controller_connection_changed(_device: int, connected: bool) -> void:
	controller_active = not Input.get_connected_joypads().is_empty()
	if not connected:
		grenade_trigger_pressed = false
		controller_fire_pressed = false
		toggle_pause_if_playing()
	if at_title:
		title_screen.deploy.grab_focus()
	title_screen.queue_redraw()

func toggle_pause_if_playing() -> void:
	if not paused and state == "playing" and not at_title:
		toggle_pause()

func _input(event: InputEvent) -> void:
	if (event is InputEventJoypadButton and event.pressed) or (event is InputEventJoypadMotion and absf(event.axis_value)>(TRIGGER_THRESHOLD if event.axis in [JOY_AXIS_TRIGGER_LEFT,JOY_AXIS_TRIGGER_RIGHT] else 0.2)):
		controller_active = true
	elif event is InputEventScreenTouch or event is InputEventScreenDrag or event is InputEventKey or (event is InputEventMouseMotion and event.relative.length()>1.0):
		controller_active = false
	if event is InputEventJoypadMotion and event.axis == JOY_AXIS_TRIGGER_RIGHT:
		controller_fire_pressed = event.axis_value > TRIGGER_THRESHOLD and not paused and not at_title and state == "playing"
	# Analog triggers emit repeated motion events while held. Throw only on
	# crossing the dead zone, and require release before another grenade.
	if event is InputEventJoypadMotion and event.axis == JOY_AXIS_TRIGGER_LEFT:
		var pressed: bool = event.axis_value > InputMap.action_get_deadzone("pad_grenade")
		if pressed and not grenade_trigger_pressed and not at_title:
			grenade(cursor_aim(controller_cursor))
		grenade_trigger_pressed = pressed
	title_screen.queue_redraw()

func stick_target(direction: Vector2) -> Vector2:
	return cursor_aim(Iso.project(player.world_pos)-camera_offset-Vector2(0,55)+direction*300)

func reset() -> void:
	controller_fire_pressed = false
	capture_progress = [0.0,0.0,0.0]
	hazard_cooldown = 0.0
	boss_salvo = 0.0
	touch_controls.clear_touches()
	for child in actors.get_children():
		actors.remove_child(child)
		child.queue_free()
	enemies.clear()
	cover.clear()
	relays.clear()
	effects.clear()
	shots.clear()
	grenades_in_flight.clear()
	casings.clear()
	particles.clear()
	pickups.clear()
	marks.clear()
	rng.seed = seed_value
	shield = 60.0
	grenades = 5
	hurt_timer = 0.0
	grenade_cd = 0.0
	dash_cd = 0.0
	dash_time = 0.0
	time = 0.0
	spawn_timer = 2.0
	score = 0
	kills = 0
	combo = 0
	combo_timer = 0.0
	boss_spawned = false
	boss_defeated = false
	state = "playing"
	paused = false
	shake = 0.0
	message = "ASHGATE // BREAK THE SIGNAL"
	message_timer = 4.0
	var mission: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/mission_2.json" if level == 2 else "res://assets/data/mission.json"))
	hazards = mission.get("hazards",[])
	if level == 2:
		message = "IRON BELLY // SECURE THE THREE PUMPS"
	extraction = Iso.vec(mission.extraction)
	player = make_actor(mission.player)
	for data: Dictionary in mission.cover:
		cover.append(make_actor(data))
	for data: Dictionary in mission.relays:
		relays.append(make_actor(data))
	for data: Dictionary in mission.enemies:
		spawn(Iso.vec(data.position), data.kind)
	for data: Dictionary in mission.facades:
		var building := Node2D.new()
		building.name = "Facade%d" % actors.get_child_count()
		building.position = Iso.project(Iso.vec(data.position))
		var sprite := Sprite2D.new()
		sprite.texture = poses.texture("res://assets/baked/facade_%d.png" % int(data.variant))
		sprite.centered = false
		sprite.position = -Iso.vec(data.anchor)
		building.add_child(sprite)
		actors.add_child(building)
	for i in range(mission.fires.size()):
		var fire := add_effect("fire", Iso.vec(mission.fires[i]))
		fire.variant = i
	camera_offset = Iso.project(player.world_pos) - Vector2(960 * 0.38, 540 * 0.48)
	aim = player.world_pos + Vector2(200,0)
	controller_cursor = Iso.project(aim)-camera_offset-Vector2(0,55)
	for voice in audio_voices:
		voice.stop()
		voice.stream_paused = false
	refresh_visuals(0.0)

func make_actor(data: Dictionary) -> SiegeActor:
	var actor: SiegeActor = ACTOR_SCENE.instantiate()
	actor.configure(data)
	if level == 2 and data.kind == "relay":
		actor.prop_texture = "res://assets/industry/pump.png"
		actor.secured_texture = "res://assets/industry/pump_secured.png"
		actor.objective_label = "PURGE PUMP"
		actor.remains_solid = true
	if level == 2 and data.kind in ["grunt","runner","rifle","brute","boss"]:
		actor.custom_sheet = "res://assets/orks/" + ("warboss" if data.kind == "boss" else "shoota" if data.kind in ["rifle","brute"] else "boy") + ".png"
	actors.add_child(actor)
	return actor

func spawn(pos: Vector2, kind: String) -> SiegeActor:
	var enemy := make_actor({"position":[pos.x,pos.y], "kind":kind, "hp":HP[kind], "radius":52 if kind == "boss" else 18})
	enemy.cooldown = rng.randf_range(0.5,2.0)
	enemy.stride = rng.randf()
	enemies.append(enemy)
	return enemy

func relays_down() -> int:
	var count := 0
	for relay in relays:
		if relay.hp <= 0.0:
			count += 1
	return count

func move_actor(actor: SiegeActor, delta: Vector2) -> float:
	var start := actor.world_pos
	for axis in range(2):
		var old := actor.world_pos[axis]
		actor.world_pos[axis] += delta[axis]
		actor.world_pos.x = clampf(actor.world_pos.x,35,2365)
		actor.world_pos.y = clampf(actor.world_pos.y,85,645)
		for obstacle: SiegeActor in cover + relays:
			if (obstacle.hp > 0.0 or obstacle.remains_solid) and actor.world_pos.distance_squared_to(obstacle.world_pos) < pow(actor.radius + obstacle.radius,2):
				actor.world_pos[axis] = old
				break
	var displacement := actor.world_pos - start
	var distance := displacement.length()
	if actor.kind == "player" and distance > 0.001:
		var travel := Iso.project(displacement)
		actor.move_facing = 1 if travel.x >= 0.0 else -1
		actor.move_angle = PoseLibrary.direction_angle(rad_to_deg(atan2(travel.y, absf(travel.x))))
	actor.stride += distance / (108.0 if actor.kind == "boss" else (132.0 if actor.kind == "player" else 64.0))
	return distance

func burst(pos: Vector2, count: int = 15, color: Color = Color("ffa134"), force: float = 140.0) -> void:
	for i in range(count):
		var velocity := Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(20.0,force)
		particles.append({"pos":pos, "velocity":velocity, "life":rng.randf_range(0.18,0.65), "color":color, "size":rng.randi_range(1,4)})

func damage_player(amount: float) -> void:
	if hurt_timer > 0.0 or dash_time > 0.0 or state != "playing":
		return
	var absorbed := minf(shield, amount)
	shield -= absorbed
	player.hp -= amount - absorbed
	hurt_timer = 0.35
	player.flash = 0.15
	shake = 5.0
	if player.hp <= 0.0:
		state = "dead"

func hit(target: SiegeActor, damage: float) -> void:
	if level == 2 and target in relays:
		return
	if target.kind in SiegeActor.PERMANENT:
		burst(target.world_pos,3,Color("b9b09b"),65)
		return
	if target.hp <= 0.0:
		return
	target.hp -= damage
	target.flash = 0.10
	burst(target.world_pos, 5, Color("da9e58"), 90)
	if target.hp > 0.0:
		return
	if target.kind in SiegeActor.BREAKABLES:
		target.destroyed_at = time
		marks.append(target.world_pos)
	if target.kind == "barrel":
		explode(target.world_pos,155,140)
	elif target.kind == "relay":
		explode(target.world_pos,120,85)
		score += 750
		grenades = mini(9,grenades + 2)
		shield = minf(60,shield + 25)
		message = "SIGNAL RELAY %d/3 SILENCED // +2 FRAGS" % relays_down()
		message_timer = 3.0
	elif target in enemies:
		var death := add_effect("death",target.world_pos)
		death.actor_kind = target.kind
		death.facing = target.facing
		death.custom_sheet = target.custom_sheet
		combo = combo + 1 if combo_timer > 0.0 else 1
		combo_timer = 2.4
		score += (5000 if target.kind == "boss" else 100) * mini(5,combo)
		kills += 1
		if target.kind == "boss":
			boss_defeated = true
			message = "WARBOSS DEFEATED // REACH EXTRACTION" if level == 2 else "SIEGE WALKER DESTROYED // REACH EXTRACTION"
			message_timer = 5.0
			explode(target.world_pos,210,200)
		elif rng.randf() < 0.25:
			pickups.append({"pos":target.world_pos,"kind":["health","shield","frag"][rng.randi_range(0,2)]})

func add_effect(kind: String, pos: Vector2, radius: float = 160.0) -> SiegeEffect:
	var effect: SiegeEffect = EFFECT_SCENE.instantiate()
	effect.effect_kind = kind
	effect.world_pos = pos
	effect.radius = radius
	actors.add_child(effect)
	effects.append(effect)
	# Bound retained corpses and simultaneous blasts like the reference renderer.
	var matching: Array[SiegeEffect] = []
	for item in effects:
		if is_instance_valid(item) and not item.is_queued_for_deletion() and item.effect_kind == kind:
			matching.append(item)
	var limit := 64 if kind == "death" else 32
	if matching.size() > limit:
		matching[0].queue_free()
	return effect

func explode(pos: Vector2, radius: float = 160.0, damage: float = 140.0) -> void:
	add_effect("explosion",pos,radius)
	burst(pos,24,Color("ffb142"),240)
	shake = 10.0
	for target: SiegeActor in enemies + cover + relays:
		var distance := target.world_pos.distance_to(pos)
		if target.hp > 0.0 and distance < radius + target.radius:
			hit(target,damage * maxf(0.3,1.0 - distance / (radius + target.radius)))
	if player.world_pos.distance_to(pos) < radius * 0.55:
		damage_player(18)
	marks.append(pos)

func grenade(target: Vector2) -> void:
	if grenades <= 0 or grenade_cd > 0.0 or state != "playing" or paused:
		return
	var delta := (target - player.world_pos).limit_length(430)
	grenades_in_flight.append({"start":player.world_pos, "end":player.world_pos + delta, "age":0.0})
	grenades -= 1
	grenade_cd = 0.8

func aim_weapon(actor: SiegeActor, target: Vector2) -> void:
	var projected := Iso.project(target - actor.world_pos)
	if absf(projected.x) >= 3.0:
		actor.facing = 1 if projected.x >= 0.0 else -1
	var raw := rad_to_deg(atan2(projected.y,absf(projected.x)))
	if actor.kind != "player":
		actor.aim_angle = raw
		return
	actor.aim_view = PoseLibrary.direction_angle(raw,actor.aim_view)
	var solution := poses.best_aim(actor,actor.aim_view,time,projected - Vector2(0,55))
	actor.aim_view = int(solution.x)
	actor.aim_angle = solution.y

func fire_weapon(actor: SiegeActor, target: Vector2, speed: float, damage: float, enemy: bool = false) -> void:
	aim_weapon(actor,target)
	var offset := actor.socket(poses,time,"muzzle")
	var start := actor.world_pos + Iso.unproject(offset + Vector2(0,55))
	for obstacle: SiegeActor in cover + relays:
		if (obstacle.hp > 0.0 or obstacle.remains_solid) and Iso.segment_entry(actor.world_pos,start,obstacle.world_pos,obstacle.radius) >= 0.0:
			start = actor.world_pos
			break
	shots.append({"pos":start,"velocity":Iso.unit(target-start)*speed,"damage":damage,"enemy":enemy,"life":2.0 if enemy else 1.1})

func eject_casing() -> void:
	var port := player.socket(poses,time,"ejection")
	var direction := Iso.unit(Iso.project(aim-player.world_pos) - Vector2(0,55) - port)
	var normal := Vector2(-direction.y,direction.x)
	casings.append({"pos":player.world_pos + Iso.unproject(port + Vector2(0,55)),"velocity":Iso.unproject(normal * 75 + direction * 15),"age":0.0,"height":55.0,"vz":100.0})

func play_shot() -> void:
	if muted or sfx_volume <= 0.0:
		return
	var voice := audio_voices[voice_index % audio_voices.size()]
	voice_index += 1
	voice.stream = load("res://assets/audio/bolter_%d.wav" % audio_rng.randi_range(0,3))
	voice.volume_db = linear_to_db(maxf(0.001,sfx_volume))
	voice.play()

func tick(dt: float, movement: Vector2, target: Vector2, shooting: bool, dash: bool) -> void:
	if state != "playing" or paused:
		return
	time += dt
	if level == 2:
		update_level_two(dt)
	aim = target
	for property: String in ["hurt_timer","grenade_cd","dash_cd","dash_time","combo_timer","message_timer"]:
		set(property,maxf(0.0,float(get(property)) - dt))
	player.flash = maxf(0.0,player.flash-dt)
	player.recoil = maxf(0.0,player.recoil-dt)
	player.cooldown = maxf(0.0,player.cooldown-dt)
	if hurt_timer == 0.0:
		shield = minf(60.0,shield + dt * 3.0)
	var traveled := 0.0
	if movement.length_squared() > 0.0:
		var direction := Iso.unit(Iso.unproject(movement.normalized()))
		if dash and dash_cd <= 0.0:
			dash_direction = direction
			dash_time = 0.16
			dash_cd = 2.2
		traveled += move_actor(player,direction * 180 * dt)
	if dash_time > 0.0:
		traveled += move_actor(player,dash_direction * 500 * dt)
	player.moving = traveled > 0.001
	aim_weapon(player,aim)
	if shooting and player.cooldown <= 0.0:
		player.cooldown = 0.105
		player.recoil = 0.105
		fire_weapon(player,aim,950,24)
		eject_casing()
		shake = maxf(shake,1.5)
		play_shot()
	spawn_timer -= dt
	if spawn_timer <= 0.0 and enemies.size() < 32 and not boss_defeated:
		spawn_timer = maxf(0.65,2.2 - relays_down() * 0.35 - time / 180.0)
		var x := clampf(player.world_pos.x + (-1 if rng.randf() < 0.5 else 1) * rng.randf_range(470,620),160,2280)
		spawn(Vector2(x,rng.randf_range(100,620)),["grunt","grunt","rifle","runner","brute"][rng.randi_range(0,4)])
	if relays_down() == 3 and not boss_spawned:
		boss_spawned = true
		spawn(Vector2(2180,370),"boss")
		message = "WARNING // ORK WARBOSS INBOUND" if level == 2 else "WARNING // SIEGE WALKER INBOUND"
		message_timer = 5.0
	update_enemies(dt)
	update_shots(dt)
	for i in range(enemies.size()-1,-1,-1):
		if enemies[i].hp <= 0.0:
			enemies[i].queue_free()
			enemies.remove_at(i)
	update_transients(dt)
	if boss_defeated and player.world_pos.distance_to(extraction) < 80.0 and state == "playing":
		state = "won"
	var camera_target := Iso.project(player.world_pos) - Vector2(960 * 0.38,540 * 0.48)
	camera_offset = camera_offset.lerp(camera_target,1.0-exp(-dt*7))
	shake *= exp(-dt*15)

func update_enemies(dt: float) -> void:
	for enemy in enemies:
		if enemy.hp <= 0.0:
			continue
		enemy.flash = maxf(0.0,enemy.flash-dt)
		enemy.recoil = maxf(0.0,enemy.recoil-dt)
		enemy.cooldown -= dt
		var delta := player.world_pos - enemy.world_pos
		aim_weapon(enemy,player.world_pos)
		var distance := delta.length()
		var direction := Iso.unit(delta)
		var speed: float = SPEED[enemy.kind]
		if enemy.kind == "boss" and enemy.phase > 0.0:
			enemy.moving = false
			enemy.phase -= dt
			if enemy.phase <= 0.0:
				burst(enemy.target,70,Color("ff5c1e"),260)
				shake = 12.0
				if player.world_pos.distance_to(enemy.target) < 115:
					damage_player(48)
				for obstacle in cover:
					if obstacle.world_pos.distance_to(enemy.target) < 115:
						hit(obstacle,100)
				enemy.cooldown = 2.8
			continue
		if enemy.kind == "boss" and enemy.cooldown <= 0.0:
			enemy.target = player.world_pos
			enemy.phase = 1.25
			continue
		if enemy.kind == "rifle" and distance < 440 and enemy.cooldown <= 0.0:
			enemy.recoil = 0.16
			fire_weapon(enemy,player.world_pos,300,13,true)
			enemy.cooldown = rng.randf_range(1.4,2.2)
		var velocity := direction*speed if distance > (230.0 if enemy.kind == "rifle" else enemy.radius + 14) else Vector2.ZERO
		if enemy.kind == "rifle" and distance < 150:
			velocity = -direction*speed
		for obstacle: SiegeActor in cover + relays:
			var away := enemy.world_pos - obstacle.world_pos
			var d := away.length()
			if (obstacle.hp > 0.0 or obstacle.remains_solid) and d > 0.0 and d < obstacle.radius + enemy.radius + 60:
				var tangent := Vector2(-away.y,away.x)
				if tangent.dot(delta) < 0.0:
					tangent = -tangent
				velocity += Iso.unit(tangent)*90 + Iso.unit(away)*35
		for other in enemies:
			var apart := enemy.world_pos - other.world_pos
			var d2 := apart.length_squared()
			if other != enemy and d2 > 0.0 and d2 < pow(enemy.radius + other.radius + 8,2):
				velocity += Iso.unit(apart)*55
		enemy.moving = move_actor(enemy,velocity*dt) > 0.001
		if distance < enemy.radius + 20 and enemy.cooldown <= 0.0:
			damage_player(24 if enemy.kind == "brute" else 12)
			enemy.cooldown = 0.8

func update_shots(dt: float) -> void:
	for shot in shots:
		var old: Vector2 = shot.pos
		shot.pos += shot.velocity*dt
		shot.life -= dt
		var targets: Array = ([player] if shot.enemy else enemies + relays) + cover
		var nearest := INF
		var contact: SiegeActor = null
		for target: SiegeActor in targets:
			if target.hp <= 0.0 and not target.remains_solid:
				continue
			var fraction := Iso.segment_entry(old,shot.pos,target.world_pos,target.radius)
			if fraction >= 0.0 and fraction < nearest:
				nearest = fraction
				contact = target
		if contact != null:
			if contact == player:
				damage_player(shot.damage)
			else:
				hit(contact,shot.damage)
			shot.life = 0.0
	shots = shots.filter(func(shot: Dictionary) -> bool: return shot.life > 0.0)

func update_transients(dt: float) -> void:
	for flight in grenades_in_flight:
		flight.age += dt
		if flight.age >= 0.65:
			explode(flight.end)
	grenades_in_flight = grenades_in_flight.filter(func(g: Dictionary) -> bool: return g.age < 0.65)
	for casing in casings:
		casing.pos += casing.velocity*dt
		casing.age += dt
		var old_height: float = casing.height
		casing.height = maxf(0,casing.height + casing.vz*dt)
		casing.vz -= 340*dt
		if old_height > 0.0 and casing.height == 0.0 and casing.vz < -100:
			casing.vz = -casing.vz*0.28
			casing.velocity *= 0.6
		elif casing.height == 0.0 and casing.vz <= 0.0:
			casing.vz = 0.0
			casing.velocity *= maxf(0,1-dt*14)
	casings = casings.filter(func(c: Dictionary) -> bool: return c.age < 8.0)
	while casings.size() > 100:
		casings.pop_front()
	for particle in particles:
		particle.pos += particle.velocity*dt
		particle.velocity *= maxf(0,1-dt*3)
		particle.life -= dt
	particles = particles.filter(func(p: Dictionary) -> bool: return p.life > 0.0)
	while particles.size() > 700:
		particles.pop_front()
	while marks.size() > 180:
		marks.pop_front()
	for i in range(pickups.size()-1,-1,-1):
		if player.world_pos.distance_to(pickups[i].pos) < 36:
			match pickups[i].kind:
				"health": player.hp = minf(100,player.hp+28)
				"shield": shield = minf(60,shield+30)
				"frag": grenades = mini(9,grenades+1)
			pickups.remove_at(i)

func cursor_aim(cursor: Vector2) -> Vector2:
	var targets: Array = enemies + relays
	targets.sort_custom(func(a: SiegeActor,b: SiegeActor) -> bool: return a.world_pos.x+a.world_pos.y > b.world_pos.x+b.world_pos.y)
	for actor: SiegeActor in targets:
		if actor.hp <= 0.0:
			continue
		var foot := Iso.project(actor.world_pos)-camera_offset
		var height: float = 150 if actor.kind == "relay" else PoseLibrary.SIZES[actor.kind].y
		if Rect2(foot-Vector2(actor.radius,height),Vector2(actor.radius*2,height)).has_point(cursor):
			return actor.world_pos
	return Iso.unproject(cursor+camera_offset+Vector2(0,55))

func refresh_visuals(dt: float) -> void:
	world.position = -(camera_offset + Vector2(sin(time*83),cos(time*71))*shake).round()
	for actor: SiegeActor in cover + relays + enemies + [player]:
		var illumination := 0.0
		for effect in effects:
			if is_instance_valid(effect) and effect.effect_kind == "explosion":
				illumination = maxf(illumination,maxf(0,1-effect.age/0.28)*maxf(0,1-actor.world_pos.distance_to(effect.world_pos)/220))
		actor.refresh(poses,time,aim if actor == player else player.world_pos,illumination)
	for i in range(effects.size()-1,-1,-1):
		if not is_instance_valid(effects[i]) or effects[i].is_queued_for_deletion():
			effects.remove_at(i)
		else:
			effects[i].refresh(poses,dt)
	ground.queue_redraw()
	airborne.queue_redraw()
	hud.queue_redraw()
	if touch_controls.enabled:
		touch_controls.queue_redraw()

func _physics_process(dt: float) -> void:
	if test_mode or capture_pending or at_title:
		return
	var movement := Input.get_vector("move_left","move_right","move_up","move_down")
	var target := cursor_aim(get_viewport().get_mouse_position())
	var shooting := Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	var dash := Input.is_action_pressed("dash")
	if touch_controls.enabled:
		movement = (movement + touch_controls.movement()).limit_length(1.0)
		if not controller_active:
			target = stick_target(touch_controls.aim_direction)
			shooting = touch_controls.firing()
		dash = dash or touch_controls.consume_dash()
	if controller_active:
		var stick := Input.get_vector("aim_left","aim_right","aim_up","aim_down",0.2)
		if not paused and state == "playing":
			controller_cursor += stick * CURSOR_SPEED * dt
			controller_cursor = controller_cursor.clamp(Vector2(12,12),get_viewport_rect().size-Vector2(12,12))
		target = cursor_aim(controller_cursor)
		shooting = controller_fire_pressed
	if smoke_frames > 0:
		movement = Vector2(cos(frame_number*0.015),sin(frame_number*0.015))
		target = enemies[0].world_pos if not enemies.is_empty() else relays[0].world_pos
		shooting = true
		dash = frame_number % 180 == 0
		if frame_number % 120 == 0:
			grenade(target)
		frame_number += 1
	var active := not paused and state == "playing"
	tick(dt,movement,target,shooting,dash)
	refresh_visuals(dt if active else 0.0)
	if smoke_frames > 0 and frame_number >= smoke_frames:
		capture_pending = true
		finish_smoke.call_deferred()

func finish_smoke() -> void:
	if not screenshot_path.is_empty() and DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		var err := get_viewport().get_texture().get_image().save_png(screenshot_path)
		if err != OK:
			push_error("Screenshot failed: %s" % error_string(err))
			get_tree().quit(1)
			return
	print("SMOKE PASS frames=%d kills=%d relays=%d state=%s" % [frame_number,kills,relays_down(),state])
	get_tree().quit()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventJoypadButton and event.pressed:
		if at_title:
			if event.is_action_pressed("pad_pause"):
				if title_screen.show_orders:
					title_screen.close_orders()
				else:
					start_mission()
			elif event.is_action_pressed("pad_back") and title_screen.show_orders:
				title_screen.toggle_orders()
		elif event.is_action_pressed("pad_pause"):
			toggle_pause()
		elif event.is_action_pressed("pad_confirm") and (paused or state != "playing"):
			if state != "playing":
				if state == "won" and level == 1:
					level = 2
				reset()
			else:
				toggle_pause()
		elif event.is_action_pressed("pad_back") and (paused or state != "playing"):
			show_title()
		return
	if at_title:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_ESCAPE:
				if state != "playing":
					get_tree().quit()
				else:
					toggle_pause()
			KEY_N:
				if state == "won" and level == 1:
					level = 2
					reset()
			KEY_R:
				if state != "playing":
					reset()
			KEY_M:
				muted = not muted
				if muted:
					for voice in audio_voices:
						voice.stop()
			KEY_MINUS: sfx_volume = maxf(0.0,sfx_volume-0.1)
			KEY_EQUAL: sfx_volume = minf(1.0,sfx_volume+0.1)
			KEY_SPACE: grenade(cursor_aim(get_viewport().get_mouse_position()))
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
		grenade(cursor_aim(get_viewport().get_mouse_position()))

func toggle_pause() -> void:
	if state != "playing" or at_title:
		return
	paused = not paused
	controller_fire_pressed = false
	touch_controls.clear_touches()
	for voice in audio_voices:
		voice.stream_paused = paused

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST and is_instance_valid(player):
		if at_title and title_screen.show_orders:
			title_screen.close_orders()
		elif not at_title:
			toggle_pause()
	if what in [NOTIFICATION_WM_WINDOW_FOCUS_OUT,NOTIFICATION_APPLICATION_PAUSED] and is_instance_valid(player) and state == "playing" and not at_title and smoke_frames == 0 and not test_mode:
		paused = true
		controller_fire_pressed = false
		touch_controls.clear_touches()
		for voice in audio_voices:
			voice.stream_paused = true

func update_level_two(dt: float) -> void:
	hazard_cooldown = maxf(0,hazard_cooldown-dt)
	for i in relays.size():
		var pump := relays[i]
		if pump.hp <= 0:
			continue
		var nearby := player.world_pos.distance_to(pump.world_pos)<120
		var contested := enemies.any(func(e): return e.hp>0 and e.world_pos.distance_to(pump.world_pos)<90)
		if nearby:
			message = "PUMP %d // %s" % [i+1,"CLEAR NEARBY ORKS" if contested else "SECURING %d%%" % int(capture_progress[i]/8.0*100)]
			message_timer = 0.2
			if not contested:
				capture_progress[i] += dt
				if capture_progress[i]>=8.0:
					pump.hp = 0
					pump.destroyed_at = time
					score += 750
					grenades = mini(9,grenades+2)
	if fmod(time,5.0)<2.0 and hazard_cooldown<=0:
		for hazard in hazards:
			if player.world_pos.distance_to(Iso.vec(hazard))<75:
				damage_player(10)
				hazard_cooldown = 1.0
	boss_salvo -= dt
	if boss_spawned and not boss_defeated and boss_salvo<=0:
		for enemy in enemies:
			if enemy.kind == "boss" and enemy.hp>0:
				for offset in [-80,0,80]:
					fire_weapon(enemy,player.world_pos+Vector2(0,offset),280,12,true)
		boss_salvo = 3.5
