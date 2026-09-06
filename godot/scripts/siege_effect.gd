class_name SiegeEffect
extends Node2D
var custom_sheet := ""
var effect_kind := "fire"
var actor_kind := "grunt"
var age := 0.0
var variant := 0
var facing := 1
var radius := 160.0
var world_pos := Vector2.ZERO
@onready var sprite: Sprite2D = $Sprite
@onready var light: Sprite2D = $Light

func refresh(library: PoseLibrary, dt: float) -> void:
	age += dt
	position = Iso.project(world_pos)
	light.visible = effect_kind == "explosion" and age < 0.35
	if light.visible:
		light.texture = library.texture("res://assets/baked/blast_light.png")
		light.scale = Vector2.ONE * radius / 160.0
		light.self_modulate = Color(1,1,1,maxf(0,1-age/0.35))
	if effect_kind == "death" and not custom_sheet.is_empty():
		if age>=20:
			queue_free()
			return
		sprite.texture = library.texture(custom_sheet)
		var cell := Vector2(sprite.texture.get_width()/4,sprite.texture.get_height())
		sprite.region_rect = Rect2(Vector2.ZERO,cell)
		sprite.scale = Vector2(100.0/cell.y,100.0/cell.y*lerpf(1.0,0.45,clampf(age/0.5,0,1)))
		sprite.position = -cell*Vector2(0.5,0.85)*sprite.scale
		sprite.rotation = lerpf(0.0,0.45,clampf(age/0.5,0,1))
		sprite.modulate = Color(0.5,0.5,0.5,clampf((20-age)/2,0,1))
		z_index = -1
		return
	var name_key := effect_kind
	var count := 8
	var index := 0
	var factor := 1.0
	var anchor_ratio := 0.94
	if effect_kind == "death":
		if age >= 20.0:
			queue_free()
			return
		name_key = "death_" + str(PoseLibrary.MODELS.get(actor_kind, actor_kind))
		count = 4
		index = 0 if age < 0.10 else (1 if age < 0.28 else (2 if age < 0.52 else 3))
		factor = 0.86 if actor_kind == "runner" else (1.18 if actor_kind == "brute" else 1.0)
		anchor_ratio = 0.88
		sprite.flip_h = facing < 0
		modulate.a = clampf((20.0 - age) / 2.0, 0.0, 1.0)
		z_index = -1 if age >= 0.85 else 0
	elif effect_kind == "explosion":
		if age >= 1.05:
			queue_free()
			return
		index = mini(7, int(age / 1.05 * 8))
		factor = clampf(radius / 160.0, 0.7, 1.5)
		modulate.a = clampf((1.05 - age) / 0.27, 0.0, 1.0)
	else:
		index = int(age * 10.0 + variant * 3) % 8
	sprite.texture = library.texture("res://assets/effects/" + name_key + ".png")
	var size := Vector2(sprite.texture.get_width() / count, sprite.texture.get_height())
	sprite.region_rect = Rect2(Vector2(index * size.x, 0), size)
	sprite.scale = Vector2.ONE * factor
	sprite.position = -size * Vector2(0.5, anchor_ratio) * factor
