extends Control
## Native title menu: gameplay remains frozen until deployment.
const DISPLAY_FONT = preload("res://assets/fonts/Cinzel.ttf")
const BODY_FONT = preload("res://assets/fonts/Rajdhani-SemiBold.ttf")
const GOLD := Color("d5b577")
var show_orders := false
@onready var game: SiegeGame = get_parent().get_parent()
var deploy: Button
var audio: Button
var level_button: Button

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	level_button = make_button("MISSION: ASHGATE",Rect2(330,285,300,36),select_level)
	deploy = make_button("DEPLOY TO ASHGATE",Rect2(330,339,300,44),game.start_mission)
	make_button("FIELD ORDERS",Rect2(330,393,145,36),toggle_orders)
	audio = make_button("AUDIO: ON",Rect2(485,393,145,36),toggle_audio)
	if not OS.has_feature("android"):
		make_button("QUIT",Rect2(430,442,100,30),func(): get_tree().quit())
	visibility_changed.connect(func():
		if visible:
			audio.text = "AUDIO: OFF" if game.muted else "AUDIO: ON"
			deploy.grab_focus()
	)

func make_button(caption: String, rect: Rect2, action: Callable) -> Button:
	var button := Button.new()
	button.text = caption
	button.position = rect.position
	button.size = rect.size
	button.add_theme_font_override("font",BODY_FONT)
	button.add_theme_font_size_override("font_size",19)
	button.add_theme_color_override("font_color",GOLD)
	for state in ["normal","hover","pressed","focus"]:
		var style := StyleBoxFlat.new()
		style.bg_color = Color("29271f") if state in ["hover","focus"] else Color("11161a")
		style.border_color = GOLD if state != "normal" else Color("706044")
		style.set_border_width_all(1)
		button.add_theme_stylebox_override(state,style)
	button.pressed.connect(action)
	add_child(button)
	return button

func toggle_audio() -> void:
	game.muted = not game.muted
	audio.text = "AUDIO: OFF" if game.muted else "AUDIO: ON"

func toggle_orders() -> void:
	show_orders = not show_orders
	queue_redraw()

func centered(value: String, y: float, font: Font, size: int, color: Color) -> void:
	var width := font.get_string_size(value,HORIZONTAL_ALIGNMENT_LEFT,-1,size).x
	draw_string(font,Vector2((960-width)/2,y),value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func _draw() -> void:
	draw_rect(Rect2(0,0,960,540),Color(0.025,0.035,0.045,0.85))
	for inset in [18,23]:
		draw_rect(Rect2(inset,inset,960-2*inset,540-2*inset),Color("64553d"),false,1)
	for x in [34,926]:
		for y in [34,506]:
			draw_circle(Vector2(x,y),2,GOLD)
	centered("N O N A T O F A B I O   P R E S E N T S",60,BODY_FONT,14,Color("a5a398"))
	draw_line(Vector2(240,84),Vector2(437,84),GOLD)
	draw_line(Vector2(523,84),Vector2(720,84),GOLD)
	var skull := preload("res://assets/effects/servo_skull.png")
	draw_texture_rect(skull,Rect2(466,65,28,45),false,Color("dbc89d"))
	centered("HIVE CITY",160,DISPLAY_FONT,49,GOLD)
	centered("RAMPAGE",228,DISPLAY_FONT,68,Color("f0dfb7"))
	centered("II",284,DISPLAY_FONT,54,GOLD)
	draw_line(Vector2(310,262),Vector2(434,262),Color("796341"))
	draw_line(Vector2(526,262),Vector2(650,262),Color("796341"))

	centered("SECURE THE PUMPS. BREAK THE WAAAGH." if game.level == 2 else "THREE RELAYS. ONE SIEGE WALKER. NO RETREAT.",495,BODY_FONT,14,Color("a49b86"))
	if show_orders:
		draw_rect(Rect2(170,110,620,215),Color("10161b"))
		draw_rect(Rect2(170,110,620,215),GOLD,false,1)
		centered("FIELD ORDERS",151,DISPLAY_FONT,26,GOLD)
		centered("Hold three pumps for 8 seconds. Defeat the Ork Warboss." if game.level == 2 else "Destroy three signal relays. Eliminate the siege walker.",191,BODY_FONT,20,Color("dfd7c4"))
		centered("Reach extraction. Survive the streets of Ashgate.",216,BODY_FONT,20,Color("dfd7c4"))
		var controls := "WASD  Move     Mouse  Aim     LMB  Fire     ESC  Pause"
		var actions := "SPACE / RMB  Frag     SHIFT  Dash"
		if game.touch_controls.enabled:
			controls = "Left stick  Move     Right stick  Aim + fire"
			actions = "Tap FRAG, DASH or PAUSE for tactical actions"
		centered(controls,264,BODY_FONT,18,GOLD)
		centered(actions,291,BODY_FONT,18,GOLD)

func select_level() -> void:
	game.level = 2 if game.level == 1 else 1
	game.reset()
	sync_level()
	queue_redraw()

func sync_level() -> void:
	level_button.text = "MISSION: IRON BELLY" if game.level == 2 else "MISSION: ASHGATE"
	deploy.text = "DEPLOY TO IRON BELLY" if game.level == 2 else "DEPLOY TO ASHGATE"
	queue_redraw()
