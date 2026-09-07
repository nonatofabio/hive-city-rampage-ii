extends Control
## Native canvas UI at the original 960x540 logical resolution.
const GOLD := Color("d6b671")
const INK := Color("121419")
const SAYINGS := ["LUX IN TENEBRIS","FERRUM ET FIDES","VIGILA. RESISTE.","OFFICIUM ANTE OMNIA","EX TENEBRIS, SPES"]
@onready var game: SiegeGame = get_parent().get_parent()
var font: Font = preload("res://assets/fonts/Rajdhani-SemiBold.ttf")
var title_font: Font = preload("res://assets/fonts/Cinzel.ttf")

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR

func text(value: String, pos: Vector2, color: Color = Color("d2ccb5"), size: int = 13) -> void:
	var selected_font := title_font if size >= 26 else font
	draw_string(selected_font,pos+Vector2(1,size+1),value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,Color(0.04,0.05,0.06,color.a))
	draw_string(selected_font,pos+Vector2(0,size),value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func panel(rect: Rect2) -> void:
	draw_rect(rect,Color("14171b"))
	draw_rect(rect,Color("756e5e"),false,2)
	draw_rect(rect.grow(-4),Color("2f3030"),false,1)

func map_point(pos: Vector2) -> Vector2:
	return Vector2(824+pos.x/2400*115,37+pos.y/700*52)

func _draw() -> void:
	if not is_instance_valid(game.player):
		return
	draw_texture(game.poses.texture("res://assets/effects/servo_skull.png"),Vector2(14,12+roundf(sin(game.time*2.5))))
	text("%08d" % game.score,Vector2(64,15),Color("e1d0a4"),12)
	var values := [game.player.hp,game.shield]
	for i in range(2):
		var y := 37+i*15
		text("HP" if i == 0 else "SH",Vector2(64,y-5),Color("d3d2c6"),11)
		draw_rect(Rect2(84,y,112,5),Color("1e1f22"))
		draw_rect(Rect2(84,y,112*clampf(values[i]/(100.0 if i == 0 else 60.0),0,1),5),Color("ce3f2d") if i == 0 else Color("42a6cc"))
		text(str(maxi(0,int(values[i]))),Vector2(203,y-5),Color("e2dccc"),11)
	var phase := fmod(game.time,6.5)
	var opacity := clampf(minf(phase/0.18,(3.1-phase)/0.5),0,1)*(0.84+0.16*sin(game.time*9))
	text(SAYINGS[int(game.time/6.5)%SAYINGS.size()],Vector2(64,69),Color(0.82,0.69,0.44,opacity),11)
	draw_rect(Rect2(816,12,132,88),Color(0.06,0.09,0.12,0.31))
	draw_rect(Rect2(816,12,132,88),Color(0.62,0.55,0.39,0.4),false)
	text("AUSPEX",Vector2(824,17),GOLD,11)
	for obstacle in game.cover:
		if obstacle.hp > 0.0:
			draw_circle(map_point(obstacle.world_pos),1,Color("75705b"))
	for relay in game.relays:
		draw_circle(map_point(relay.world_pos),2,Color("eb9738") if relay.hp > 0.0 else Color("547e6f"))
	for enemy in game.enemies:
		if enemy.hp > 0.0:
			draw_circle(map_point(enemy.world_pos),3 if enemy.kind == "boss" else 2,Color("e54a2f"))
	draw_circle(map_point(game.player.world_pos),3,Color("78e0f9"))
	if game.boss_defeated:
		draw_circle(map_point(game.extraction),3,Color("64e8af"),false)
	panel(Rect2(16,477,928,47))
	var touch: bool = game.touch_controls.enabled and not game.controller_active
	text(("FRAG %02d" if touch else "FRAG %02d  [L2]" if game.controller_active else "FRAG %02d  [SPACE / RMB]") % game.grenades,Vector2(30,490),GOLD,12)
	text("DASH " + ("READY" if game.dash_cd <= 0 else "%.1fs" % game.dash_cd) + ("" if touch else " [L3]" if game.controller_active else " [SHIFT]"),Vector2(245,490),Color("d2ccb5"),12)
	var objective := ("PUMPS %d/3" if game.level == 2 else "RELAYS %d/3") % game.relays_down()
	if game.boss_spawned:
		objective = "REACH EXTRACTION" if game.boss_defeated else "DESTROY THE WALKER"
	text(objective,Vector2(477,490),Color("e69750"),12)
	text("LEFT MOVE / RIGHT AIM + FIRE" if touch else "RS AIM / R2 FIRE / START" if game.controller_active else "WASD MOVE / LMB FIRE / ESC",Vector2(717,491),Color("899095"),11)
	if game.message_timer > 0.0:
		var width := font.get_string_size(game.message,HORIZONTAL_ALIGNMENT_LEFT,-1,12).x
		draw_rect(Rect2(480-width/2-12,133,width+24,28),Color("18191c"))
		text(game.message,Vector2(480-width/2,139),Color("ebc270"),12)
	var target := Vector2.INF
	for relay in game.relays:
		if relay.hp > 0.0 and target == Vector2.INF:
			target = relay.world_pos
	for enemy in game.enemies:
		if enemy.kind == "boss":
			text("ORK WARBOSS" if game.level == 2 else "CATHEDRAL-BREAKER",Vector2(348,24),Color("e1976b"),12)
			draw_rect(Rect2(322,44,322,10),INK)
			draw_rect(Rect2(323,45,320*maxf(0,enemy.hp)/1800,8),Color("b03626"))
			target = enemy.world_pos
	if game.boss_defeated:
		target = game.extraction
	if target != Vector2.INF:
		var p := game.world_to_screen(target)
		if not Rect2(70,160,820,280).has_point(p):
			p = p.clamp(Vector2(65,172),Vector2(895,440))
			draw_circle(p,12,GOLD,false,2)
			text("!",p-Vector2(3,9),GOLD,14)
	if game.combo_timer > 0.0 and game.combo > 1:
		text("%d KILL CHAIN  x%d" % [game.combo,mini(5,game.combo)],Vector2(18,98),Color("f9b850"))
	if game.state == "playing" and not game.paused:
		var p: Vector2 = game.controller_cursor if game.controller_active else game.world_to_screen(game.aim,55)
		draw_circle(p,7,Color("ebcf95"),false)
		for d: Vector2 in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
			draw_line(p+d*8,p+d*12,Color("ebcf95"))
	if game.paused or game.state != "playing":
		draw_rect(Rect2(0,0,960,540),Color(0.03,0.04,0.07,0.80))
		panel(Rect2(240,175,480,185))
		var title := "PAUSED" if game.paused else (("IRON BELLY SECURED" if game.level == 2 else "ASHGATE LIBERATED") if game.state == "won" else "YOU HAVE FALLEN")
		text(title,Vector2(270,207),GOLD,30)
		text("%07d POINTS / %d KILLS / %d SECONDS" % [game.score,game.kills,int(game.time)],Vector2(270,265))
		var prompt := "ESC RESUME / O OPTIONS" if game.paused else "R TO DEPLOY AGAIN / ESC TO QUIT"
		if game.state == "won" and game.level == 1 and not touch:
			prompt = "N FOR IRON BELLY / R TO REPLAY"
		if touch:
			prompt = "TAP HERE TO RESUME" if game.paused else "TAP TO DEPLOY IRON BELLY" if game.state == "won" and game.level == 1 else "TAP HERE TO DEPLOY AGAIN"
		if game.controller_active:
			prompt = "A RESUME / Y OPTIONS / B MENU" if game.paused else "A NEXT MISSION / B MENU" if game.state == "won" and game.level == 1 else "A RETRY / B MENU"
		text(prompt,Vector2(270,310),Color("93a4b0"))
		panel(Rect2(240,373,480,58))
		var audio_text := "AUDIO %s [M]    GUNFIRE %d%% [- / =]" % ["MUTED" if game.muted else "ON",roundi(game.sfx_volume*100)]
		if touch:
			audio_text = "AUDIO %s / TAP TO MUTE OR UNMUTE" % ("MUTED" if game.muted else "ON")
		if game.controller_active:
			audio_text = "AUDIO %s / CHANGE IN TITLE MENU" % ("MUTED" if game.muted else "ON")
		text(audio_text,Vector2(260,389),GOLD,12)
