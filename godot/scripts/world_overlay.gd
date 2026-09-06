extends Node2D
@export var airborne := false
@onready var game: SiegeGame = get_parent().get_parent()

func ring(pos: Vector2, radius: float, color: Color, width: float = 1.0) -> void:
	var points := PackedVector2Array()
	for i in range(41):
		points.append(Iso.project(pos + Vector2.from_angle(i*TAU/40)*radius))
	draw_polyline(points,color,width)

func diamond(pos: Vector2, radius: float, color: Color, width: float = 1.0) -> void:
	var r := radius/sqrt(2.0)
	var points := PackedVector2Array()
	for p: Vector2 in [Vector2(-r,-r),Vector2(r,-r),Vector2(r,r),Vector2(-r,r),Vector2(-r,-r)]:
		points.append(Iso.project(pos+p))
	draw_polyline(points,color,width)

func _draw() -> void:
	if not is_instance_valid(game.player):
		return
	if airborne:
		draw_airborne()
	else:
		draw_ground()

func draw_ground() -> void:
	var stamp := game.poses.texture("res://assets/baked/shadow_mark.png")
	for pos in game.marks:
		draw_texture(stamp,Iso.project(pos)-Vector2(27,8))
	for relay in game.relays:
		if relay.hp > 0.0:
			diamond(relay.world_pos,45,Color("904d2b"))
	for enemy in game.enemies:
		if enemy.kind == "boss" and enemy.phase > 0.0:
			ring(enemy.target,115,Color("ff4121"),3)
			ring(enemy.target,maxf(1,115*(1-enemy.phase/1.25)),Color("ffa43c"),2)
			draw_string(ThemeDB.fallback_font,Iso.project(enemy.target)+Vector2(-34,-12),"INCOMING",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("ff9c50"))
	for pickup in game.pickups:
		var color: Color = {"health":Color("69d169"),"shield":Color("46a8f2"),"frag":Color("e3a744")}[pickup.kind]
		var p := Iso.project(pickup.pos)-Vector2(0,8+sin(game.time*4)*3)
		diamond(pickup.pos,13,color)
		draw_rect(Rect2(p-Vector2(5,8),Vector2(10,12)),color)
		draw_line(p-Vector2(3,2),p+Vector2(3,-2),Color("121419"),2)
		draw_line(p-Vector2(0,5),p+Vector2(0,1),Color("121419"),2)
	if game.boss_defeated:
		diamond(game.extraction,80,Color("5ed6b6"),3)
		draw_string(ThemeDB.fallback_font,Iso.project(game.extraction)+Vector2(-42,-20),"EXTRACTION",HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color("82f0ca"))

func draw_airborne() -> void:
	for casing in game.casings:
		var grounded: bool = casing.height <= 0.0 and casing.vz <= 0.0
		var index := 0 if grounded else int(casing.age*17)%3
		var angle := (int(casing.pos.x+casing.pos.y)%18)*10 if grounded else int(casing.age*72)%36*10
		var texture := game.poses.texture("res://assets/effects/casing_%d.png" % index)
		draw_set_transform(Iso.project(casing.pos)-Vector2(0,casing.height),deg_to_rad(angle))
		draw_texture(texture,-texture.get_size()/2,Color(1,1,1,clampf((8.0-casing.age)/2,0,1)))
	for shot in game.shots:
		var texture := game.poses.texture("res://assets/effects/" + ("enemy_bolt" if shot.enemy else "bolt") + ".png")
		draw_set_transform(Iso.project(shot.pos)-Vector2(0,55),Iso.project(shot.velocity).angle())
		draw_texture(texture,-Vector2(texture.get_width()-1,texture.get_height()/2.0))
	draw_set_transform(Vector2.ZERO)
	for flight in game.grenades_in_flight:
		var p: Vector2 = flight.start.lerp(flight.end,minf(1,flight.age/0.65))
		ring(flight.end,160,Color("9f8d4e"))
		draw_circle(Iso.project(p)-Vector2(0,sin(flight.age/0.65*PI)*100+12),5,Color("85ae48"))
	for particle in game.particles:
		draw_rect(Rect2(Iso.project(particle.pos)-Vector2(0,15+particle.life*22),Vector2.ONE*particle.size),particle.color)
