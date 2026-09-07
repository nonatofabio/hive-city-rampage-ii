extends Control
## Native title menu: gameplay remains frozen until deployment.
const DISPLAY_FONT = preload("res://assets/fonts/Cinzel.ttf")
const BODY_FONT = preload("res://assets/fonts/Rajdhani-SemiBold.ttf")
const GOLD := Color("d5b577")
var show_orders := false
var show_options := false
var options_from_game := false
var options_button: Button
var speed_button: Button
var view_button: Button
var volume_button: Button
@onready var game: SiegeGame = get_parent().get_parent()
var deploy: Button
var audio: Button
var level_button: Button
var orders_button: Button
var quit_button: Button
var close_button: Button

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	level_button = make_button("MISSION: ASHGATE",Rect2(550,120,340,44),select_level)
	deploy = make_button("DEPLOY TO ASHGATE",Rect2(550,178,340,48),game.start_mission)
	orders_button = make_button("FIELD ORDERS",Rect2(550,240,340,44),toggle_orders)
	audio = make_button("AUDIO: ON",Rect2(550,298,340,44),toggle_audio)
	options_button = make_button("OPTIONS",Rect2(550,356,340,44),open_options)
	quit_button = make_button("QUIT",Rect2(550,414,340,44),quit_game)
	speed_button = make_button("",Rect2(260,160,440,48),cycle_speed)
	view_button = make_button("",Rect2(260,230,440,48),cycle_view)
	volume_button = make_button("",Rect2(260,300,440,48),cycle_volume)
	for button: Button in [speed_button,view_button,volume_button]:
		button.hide()
	close_button = make_button("BACK TO MENU",Rect2(330,405,300,44),close_panel)
	close_button.hide()
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

func close_panel() -> void:
	if show_options:
		close_options()
	else:
		close_orders()

func open_options() -> void:
	options_from_game = not game.at_title
	if options_from_game:
		game.paused = true
		game.controller_fire_pressed = false
		game.hud.hide()
		game.touch_controls.hide()
		show()
	set_orders(true)
	show_orders = false
	show_options = true
	close_button.text = "BACK TO PAUSE" if options_from_game else "BACK TO MENU"
	for button: Button in [speed_button,view_button,volume_button]:
		button.show()
	sync_options()
	speed_button.grab_focus()
	queue_redraw()

func close_options() -> void:
	show_options = false
	for button: Button in [speed_button,view_button,volume_button]:
		button.hide()
	set_orders(false)
	if options_from_game:
		hide()
		game.hud.show()
		game.touch_controls.visible = game.touch_controls.enabled
	else:
		options_button.grab_focus()
	options_from_game = false

func sync_options() -> void:
	speed_button.text = "CURSOR SPEED: %.1fx" % game.CURSOR_SPEEDS[game.cursor_speed_index]
	view_button.text = "VIEW: " + game.view_mode
	volume_button.text = "SOUND: %d%%" % roundi(game.sfx_volume*100)

func cycle_speed() -> void:
	game.cursor_speed_index = (game.cursor_speed_index+1)%game.CURSOR_SPEEDS.size()
	sync_options()
	game.save_settings()

func cycle_view() -> void:
	var names := ["WIDE","NORMAL","CLOSE"]
	game.set_view(names[(names.find(game.view_mode)+1)%names.size()])
	sync_options()
	game.save_settings()

func cycle_volume() -> void:
	game.sfx_volume = 0.0 if game.sfx_volume>0.99 else minf(1.0,game.sfx_volume+0.2)
	sync_options()
	game.save_settings()

func toggle_orders() -> void:
	set_orders(not show_orders)

func close_orders() -> void:
	set_orders(false)

func set_orders(open: bool) -> void:
	show_orders = open
	close_button.text = "BACK TO MENU"
	for button: Button in [level_button,deploy,orders_button,audio,options_button,quit_button]:
		button.visible = not open
	close_button.visible = open
	if is_visible_in_tree():
		(close_button if open else orders_button).grab_focus()
	queue_redraw()

func quit_game() -> void:
	get_tree().quit()

func centered(value: String, y: float, font: Font, size: int, color: Color, center_x: float = 480.0) -> void:
	var width := font.get_string_size(value,HORIZONTAL_ALIGNMENT_LEFT,-1,size).x
	draw_string(font,Vector2(center_x-width/2,y),value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func _draw() -> void:
	draw_rect(Rect2(0,0,960,540),Color(0.025,0.035,0.045,0.85))
	for inset in [18,23]:
		draw_rect(Rect2(inset,inset,960-2*inset,540-2*inset),Color("64553d"),false,1)
	for x in [34,926]:
		for y in [34,506]:
			draw_circle(Vector2(x,y),2,GOLD)
	if show_options:
		draw_rect(Rect2(80,75,800,400),Color("10161b"))
		draw_rect(Rect2(80,75,800,400),GOLD,false,1)
		centered("OPTIONS",123,DISPLAY_FONT,26,GOLD)
		return
	if show_orders:
		draw_orders()
		return
	centered("N O N A T O F A B I O   P R E S E N T S",60,BODY_FONT,14,Color("a5a398"))
	# Keep font sizes independent of the world view and rendering resolution.
	draw_line(Vector2(88,122),Vector2(225,122),GOLD)
	draw_line(Vector2(285,122),Vector2(422,122),GOLD)
	var skull := preload("res://assets/effects/servo_skull.png")
	draw_texture_rect(skull,Rect2(241,103,28,45),false,Color("dbc89d"))
	centered("HIVE CITY",218,DISPLAY_FONT,49,GOLD,255)
	centered("RAMPAGE",286,DISPLAY_FONT,68,Color("f0dfb7"),255)
	centered("II",355,DISPLAY_FONT,54,GOLD,255)
	centered("SECURE THE PUMPS.",412,BODY_FONT,18,Color("a49b86"),255) if game.level==2 else centered("THREE RELAYS. ONE SIEGE WALKER.",412,BODY_FONT,16,Color("a49b86"),255)
	centered("BREAK THE WAAAGH." if game.level==2 else "NO RETREAT.",437,BODY_FONT,16,Color("a49b86"),255)
	draw_line(Vector2(497,115),Vector2(497,456),Color("64553d"))
	centered("DEPLOYMENT",96,BODY_FONT,18,GOLD,720)

func select_level() -> void:
	game.level = 2 if game.level == 1 else 1
	game.reset()
	sync_level()
	queue_redraw()

func sync_level() -> void:
	level_button.text = "MISSION: IRON BELLY" if game.level == 2 else "MISSION: ASHGATE"
	deploy.text = "DEPLOY TO IRON BELLY" if game.level == 2 else "DEPLOY TO ASHGATE"
	queue_redraw()

func draw_orders() -> void:
	draw_rect(Rect2(80,75,800,400),Color("10161b"))
	draw_rect(Rect2(80,75,800,400),GOLD,false,1)
	centered("FIELD ORDERS",123,DISPLAY_FONT,26,GOLD)
	centered("Hold three pumps for 8 seconds. Defeat the Ork Warboss." if game.level == 2 else "Destroy three signal relays. Eliminate the siege walker.",191,BODY_FONT,20,Color("dfd7c4"))
	centered("Reach extraction. Survive the streets of Ashgate.",216,BODY_FONT,20,Color("dfd7c4"))
	var controls := "WASD  Move     Mouse  Aim     LMB  Fire     ESC  Pause"
	var actions := "SPACE / RMB  Frag     SHIFT  Dash"
	if game.touch_controls.enabled:
		controls = "Left stick  Move     Right stick  Aim + fire"
		actions = "Tap FRAG, DASH or PAUSE for tactical actions"
	if game.controller_active:
		controls = "Left stick / D-pad  Move     Right stick  Cursor"
		actions = "L2  Frag     L3  Dash     R2  Fire     START  Pause"
	centered(controls,264,BODY_FONT,18,GOLD)
	centered(actions,291,BODY_FONT,18,GOLD)
	centered("Hold fire near an enemy to use the chainsword.",324,BODY_FONT,17,GOLD)
