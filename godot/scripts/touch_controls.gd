extends Control
## Two independent touch sticks; firing follows the right stick beyond its dead zone.
const MOVE_CENTER := Vector2(110,388)
const AIM_CENTER := Vector2(830,388)
const STICK_RADIUS := 62.0
const DEAD_ZONE := 12.0
const GRENADE_CENTER := Vector2(680,365)
const DASH_CENTER := Vector2(680,444)
const PAUSE_RECT := Rect2(860,110,88,40)
var enabled := false
var move_finger := -1
var aim_finger := -1
var move_offset := Vector2.ZERO
var aim_offset := Vector2.ZERO
var aim_direction := Vector2.RIGHT
var dash_requested := false
@onready var game: SiegeGame = get_parent().get_parent()

func _ready() -> void:
	enabled = OS.has_feature("android") or "--touch" in OS.get_cmdline_user_args()
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	visible = enabled
	set_process_input(enabled)

func movement() -> Vector2:
	return move_offset / STICK_RADIUS if move_offset.length()>DEAD_ZONE else Vector2.ZERO

func firing() -> bool:
	return aim_finger>=0 and aim_offset.length()>DEAD_ZONE

func consume_dash() -> bool:
	var requested := dash_requested
	dash_requested = false
	return requested

func clear_touches() -> void:
	move_finger = -1
	aim_finger = -1
	move_offset = Vector2.ZERO
	aim_offset = Vector2.ZERO
	dash_requested = false
	queue_redraw()

func _input(event: InputEvent) -> void:
	if game.at_title:
		return
	if event is InputEventScreenTouch:
		if not event.pressed or event.canceled:
			if event.index == move_finger:
				move_finger = -1
				move_offset = Vector2.ZERO
			if event.index == aim_finger:
				aim_finger = -1
				aim_offset = Vector2.ZERO
		elif PAUSE_RECT.has_point(event.position):
			game.toggle_pause()
		elif game.paused or game.state != "playing":
			if Rect2(240,373,480,58).has_point(event.position):
				game.muted = not game.muted
				for voice in game.audio_voices:
					voice.stop()
			elif Rect2(240,175,480,185).has_point(event.position):
				if game.state != "playing":
					game.reset()
				else:
					game.toggle_pause()
		elif event.position.distance_to(GRENADE_CENTER)<32:
			game.grenade(game.aim)
		elif event.position.distance_to(DASH_CENTER)<32:
			dash_requested = true
		elif move_finger<0 and event.position.distance_to(MOVE_CENTER)<STICK_RADIUS+25:
			move_finger = event.index
			move_offset = (event.position-MOVE_CENTER).limit_length(STICK_RADIUS)
		elif aim_finger<0 and event.position.distance_to(AIM_CENTER)<STICK_RADIUS+25:
			aim_finger = event.index
			update_aim(event.position)
	elif event is InputEventScreenDrag and not game.paused and game.state == "playing":
		if event.index == move_finger:
			move_offset = (event.position-MOVE_CENTER).limit_length(STICK_RADIUS)
		if event.index == aim_finger:
			update_aim(event.position)
	queue_redraw()

func update_aim(point: Vector2) -> void:
	aim_offset = (point-AIM_CENTER).limit_length(STICK_RADIUS)
	if aim_offset.length()>DEAD_ZONE:
		aim_direction = aim_offset.normalized()

func label_at(value: String, point: Vector2, size: int = 12) -> void:
	var width := preload("res://assets/fonts/Rajdhani-SemiBold.ttf").get_string_size(value,HORIZONTAL_ALIGNMENT_LEFT,-1,size).x
	draw_string(preload("res://assets/fonts/Rajdhani-SemiBold.ttf"),point-Vector2(width/2,0),value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,Color("ebcf95"))

func _draw() -> void:
	if not enabled or not is_instance_valid(game.player):
		return
	draw_style_box(make_panel(),PAUSE_RECT)
	label_at("RESUME" if game.paused else "PAUSE",PAUSE_RECT.get_center()+Vector2(0,4))
	if game.paused or game.state != "playing":
		return
	for pair: Array in [[MOVE_CENTER,move_offset,"MOVE"],[AIM_CENTER,aim_offset,"AIM / FIRE"]]:
		draw_circle(pair[0],STICK_RADIUS,Color(0.04,0.06,0.08,0.45))
		draw_circle(pair[0],STICK_RADIUS,Color(0.8,0.7,0.5,0.6),false,2)
		draw_circle(pair[0]+pair[1],22,Color(0.7,0.65,0.5,0.55))
		label_at(pair[2],pair[0]+Vector2(0,STICK_RADIUS+17),11)
	for pair: Array in [[GRENADE_CENTER,"FRAG"],[DASH_CENTER,"DASH"]]:
		draw_circle(pair[0],30,Color(0.04,0.06,0.08,0.7))
		draw_circle(pair[0],30,Color(0.8,0.7,0.5,0.7),false,2)
		label_at(pair[1],pair[0]+Vector2(0,4),11)

func make_panel() -> StyleBoxFlat:
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(0.04,0.06,0.08,0.7)
	return panel
