extends Node2D
## Single cutting edge, armored spine and a motor housing near the grip.
## Reference notes: art/chainsword/README.md. Geometry is drawn for this game.
func _draw() -> void:
	var actor: SiegeActor = get_parent()
	if actor.melee_time <= 0.0:
		return
	var progress := 1.0-actor.melee_time/0.42
	var angle := actor.melee_direction.angle()+lerpf(-1.1,0.9,progress)
	draw_set_transform(Vector2(0,-48),angle)
	draw_arc(Vector2.ZERO,59,-0.35,0.08,12,Color(0.76,0.81,0.84,(1-progress)*0.4),2)
	# Wrapped grip and a guard; a solid, blunt-backed chain casing.
	draw_rect(Rect2(6,-3,14,6),Color("20252b"))
	for x in range(8,19,3):
		draw_line(Vector2(x,-3),Vector2(x,3),Color("53565a"),1)
	draw_rect(Rect2(18,-8,4,17),Color("a88b45"))
	draw_colored_polygon(PackedVector2Array([Vector2(22,-6),Vector2(62,-6),Vector2(67,-2),Vector2(63,5),Vector2(22,5)]),Color("272f35"))
	draw_colored_polygon(PackedVector2Array([Vector2(27,-4),Vector2(61,-4),Vector2(64,-1),Vector2(60,2),Vector2(27,2)]),Color("687984"))
	# Smooth spine: no teeth on the back edge.
	draw_line(Vector2(27,-5),Vector2(61,-5),Color("aeb8b9"),1)
	draw_line(Vector2(28,4),Vector2(62,4),Color("10151a"),2)
	var travel := int(progress*24)%3
	for x in range(29,61,4):
		var tooth_x := x+travel
		draw_colored_polygon(PackedVector2Array([Vector2(tooth_x,4),Vector2(tooth_x+1,8),Vector2(tooth_x+4,4)]),Color("bbc1b8"))
	# Motor casing covers the chain return; vents and pins read at sprite scale.
	draw_rect(Rect2(21,-8,9,15),Color("39454d"))
	for y in [-5,-2,1]:
		draw_line(Vector2(22,y),Vector2(26,y),Color("151b20"),1)
	draw_circle(Vector2(28,4),1.5,Color("a88b45"))
	draw_circle(Vector2(61,-1),1.5,Color("a5afb0"))
	draw_set_transform(Vector2.ZERO)
