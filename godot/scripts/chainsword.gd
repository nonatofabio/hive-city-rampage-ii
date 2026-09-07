extends Node2D
## Small vector weapon rendered at the game's pixel scale, attached to the off hand.
func _draw() -> void:
	var actor: SiegeActor = get_parent()
	if actor.melee_time <= 0.0:
		return
	var progress := 1.0-actor.melee_time/0.42
	var angle := actor.melee_direction.angle()+lerpf(-1.1,0.9,progress)
	draw_set_transform(Vector2(0,-48),angle)
	# Swept edge, powered teeth, steel blade, gold guard and dark grip.
	draw_arc(Vector2.ZERO,57,-0.5,0.15,14,Color(0.8,0.86,0.93,(1-progress)*0.65),3)
	draw_rect(Rect2(7,-3,14,6),Color("252a31"))
	draw_rect(Rect2(18,-10,5,20),Color("c29a40"))
	draw_colored_polygon(PackedVector2Array([Vector2(23,-6),Vector2(58,-6),Vector2(65,0),Vector2(58,6),Vector2(23,6)]),Color("14191e"))
	draw_rect(Rect2(25,-3,32,6),Color("8c9da8"))
	for x in range(25,59,5):
		for side in [-1,1]:
			draw_colored_polygon(PackedVector2Array([Vector2(x,side*5),Vector2(x+2,side*9),Vector2(x+4,side*5)]),Color("d3d6c9"))
	draw_line(Vector2(27,0),Vector2(55,0),Color("373e45"),2)
	draw_set_transform(Vector2.ZERO)
