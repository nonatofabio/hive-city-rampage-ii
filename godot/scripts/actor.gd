class_name SiegeActor
extends Node2D
## Reusable actor scene. World-space simulation and projected visuals are separate.
@export_enum("player", "grunt", "rifle", "runner", "brute", "boss", "crate", "barrel", "relay") var kind := "grunt"
@export var hp := 45.0
@export var radius := 18.0
var world_pos := Vector2.ZERO
var max_hp := 45.0
var cooldown := 0.0
var flash := 0.0
var recoil := 0.0
var stride := 0.0
var moving := false
var facing := 1
var aim_angle := 0.0
var aim_view := 0
var move_angle := 0
var move_facing := 1
var phase := 0.0
var target := Vector2.ZERO
var muzzle := Vector2.ZERO
var ejection := Vector2.ZERO
@onready var shadow: Sprite2D = $Shadow
@onready var lower: Sprite2D = $Lower
@onready var body: Sprite2D = $Body
@onready var muzzle_flash: Sprite2D = $Muzzle

func configure(data: Dictionary) -> void:
	kind = data.kind
	world_pos = Iso.vec(data.position)
	hp = float(data.hp)
	max_hp = hp
	radius = float(data.radius)
	position = Iso.project(world_pos)

func pose_key(library: PoseLibrary, time: float) -> Dictionary:
	return library.pose(kind, stride, moving, aim_angle, recoil, time, phase, aim_view if kind == "player" else 999)

func socket(library: PoseLibrary, time: float, socket_name: String) -> Vector2:
	var geo := library.geometry(kind, pose_key(library, time), facing)
	return geo[socket_name] - geo.anchor

func refresh(library: PoseLibrary, time: float, aim: Vector2, illumination: float = 0.0) -> void:
	position = Iso.project(world_pos)
	visible = hp > 0.0
	if not visible:
		return
	var prop := kind in ["crate", "barrel", "relay"]
	var shadow_kind := "prop" if prop else ("boss" if kind == "boss" else "actor")
	shadow.texture = library.texture("res://assets/baked/shadow_" + shadow_kind + ".png")
	shadow.position = Vector2(0, 6 if prop else 2)
	lower.visible = false
	muzzle_flash.visible = false
	if prop:
		body.texture = library.texture("res://assets/baked/" + kind + ".png")
		body.position = Vector2(-58, -body.texture.get_height() + 16)
	else:
		var key := pose_key(library, time)
		var data: Dictionary = library.models[key.model]
		var clip: Dictionary = data.clips[key.clip]
		var geo := library.geometry(kind, key, facing)
		var cell := Iso.vec(data.cell)
		body.texture = library.texture(clip.path)
		body.region_enabled = true
		body.region_rect = Rect2(Vector2(key.index * cell.x, 0), cell)
		body.scale = geo.scale
		body.flip_h = geo.flip
		body.position = -Vector2(geo.anchor)
		muzzle = geo.muzzle - geo.anchor
		ejection = geo.ejection - geo.anchor
		if kind == "player":
			var gait := library.lower_pose(key,facing,stride,moving,move_angle,move_facing)
			var vertical := absi(gait.x) == 90
			lower.visible = true
			lower.texture = library.texture("res://assets/rendered/walk/%d.png" % gait.x)
			lower.region_rect = Rect2((gait.z % 2 if vertical else gait.z) * 80, 0, 80, 64)
			lower.flip_h = gait.z >= 2 if vertical else gait.y < 0
			lower.position = library.lower_origin(key,facing) - Vector2(geo.anchor)
		if recoil > 0.065 and kind in ["player", "rifle"]:
			muzzle_flash.visible = true
			muzzle_flash.texture = library.texture("res://assets/effects/muzzle_%d.png" % (int(time * 24) % 2))
			muzzle_flash.position = muzzle
			muzzle_flash.offset = Vector2(0, -muzzle_flash.texture.get_height() * 0.477)
			muzzle_flash.rotation = (Iso.project(aim - world_pos) - Vector2(0, 55) - muzzle).angle()
	var glow := illumination * 0.25 + (0.35 if flash > 0.0 else 0.0)
	body.self_modulate = Color(1.0 + glow, 1.0 + glow * 0.7, 1.0 + glow * 0.35)
	lower.self_modulate = body.self_modulate
	queue_redraw()

func _draw() -> void:
	if kind == "player":
		var points := PackedVector2Array([Vector2(-31,0), Vector2(0,-15.5), Vector2(31,0), Vector2(0,15.5), Vector2(-31,0)])
		draw_polyline(points, Color("55a5cd"), 1.0)
	elif hp < max_hp and hp > 0.0 and PoseLibrary.SIZES.has(kind):
		var y: float = -PoseLibrary.SIZES[kind].y
		draw_rect(Rect2(-19, y, 38, 4), Color("121419"))
		draw_rect(Rect2(-19, y, 38 * hp / max_hp, 3), Color("ae3b28"))
	elif kind == "relay" and hp > 0.0 and body.texture != null:
		draw_string(ThemeDB.fallback_font,Vector2(-39,-body.texture.get_height()+14),"SIGNAL RELAY",HORIZONTAL_ALIGNMENT_LEFT,-1,11,Color("f68e46"))
