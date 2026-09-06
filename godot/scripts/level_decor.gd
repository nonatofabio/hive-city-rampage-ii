extends Node2D
@onready var game: SiegeGame = get_parent().get_parent()
func _process(_dt: float) -> void:
	queue_redraw()
func block(p: Vector2, w: float, d: float, h: float, color: Color) -> void:
	var a := Iso.project(p)
	var b := Iso.project(p+Vector2(w,0))
	var c := Iso.project(p+Vector2(w,d))
	var e := Iso.project(p+Vector2(0,d))
	var z := Vector2(0,-h)
	draw_colored_polygon(PackedVector2Array([a,b,b+z,a+z]),color.darkened(0.4))
	draw_colored_polygon(PackedVector2Array([b,c,c+z,b+z]),color.darkened(0.2))
	draw_colored_polygon(PackedVector2Array([a+z,b+z,c+z,e+z]),color)
func _draw() -> void:
	if game.level != 2:
		return
	for x in range(30,2350,220):
		var wall := game.poses.texture("res://assets/industry/wall.png")
		draw_texture(wall,Iso.project(Vector2(x,35))-Vector2(0,wall.get_height()-80))
	for x in [520,1160,1800]:
		var furnace := game.poses.texture("res://assets/industry/furnace.png")
		draw_texture(furnace,Iso.project(Vector2(x,650))-Vector2(85,furnace.get_height()-15))
	for i in game.relays.size():
		var p := Iso.project(game.relays[i].world_pos)
		var done: bool = game.relays[i].hp<=0
		draw_arc(p,74,0,TAU,48,Color("54dbb1") if done else Color("dda445"),2)
		draw_arc(p,69,-PI/2,-PI/2+TAU*minf(1,game.capture_progress[i]/8),48,Color("54dbb1"),5)
	for hazard in game.hazards:
		var p := Iso.project(Iso.vec(hazard))
		var active := fmod(game.time,5)<2
		var vent := game.poses.texture("res://assets/industry/vent.png")
		draw_texture(vent,p-Vector2(80,vent.get_height()/2),Color.WHITE if active else Color(0.35,0.4,0.45))
