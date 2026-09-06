class_name PoseLibrary
extends RefCounted
## Reads the original Blender exports, including animated combat and waist sockets.
const MODELS := {"player": "player", "grunt": "grunt", "rifle": "rifle", "runner": "grunt", "brute": "rifle", "boss": "boss"}
const VIEWS := {-90: "player_n", -45: "player_ne", 0: "player", 45: "player_se", 90: "player_s"}
const SIZES := {"player": Vector2(88,100), "grunt": Vector2(82,90), "rifle": Vector2(82,94), "runner": Vector2(70,78), "brute": Vector2(98,112), "boss": Vector2(200,238)}
var models: Dictionary
var registration: Dictionary
var textures: Dictionary = {}

func _init() -> void:
	registration = JSON.parse_string(FileAccess.get_file_as_string("res://assets/data/player_registration.json"))
	models = JSON.parse_string(FileAccess.get_file_as_string("res://assets/rendered/sprites.json"))["models"]
	var upper: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/rendered/upper/sprites.json"))["models"]
	for model: String in models:
		for clip: Dictionary in models[model].clips.values():
			clip["path"] = "res://assets/rendered/" + clip.sheet
	for model: String in upper:
		for clip: Dictionary in upper[model].clips.values():
			clip["path"] = "res://assets/rendered/upper/" + clip.sheet
		models[model].clips.merge(upper[model].clips, true)

func texture(path: String) -> Texture2D:
	if not textures.has(path):
		textures[path] = load(path)
	return textures[path]

static func direction_angle(angle: float, previous: int = 999) -> int:
	if VIEWS.has(previous) and absf(angle - previous) <= 26.5:
		return previous
	var best := 0
	var error := INF
	for view: int in VIEWS:
		if absf(angle - view) < error:
			best = view
			error = absf(angle - view)
	return best

func pose(kind: String, stride: float, moving: bool, angle: float, recoil: float, time: float, windup: float = 0.0, view: int = 999) -> Dictionary:
	var model: String = MODELS[kind]
	if kind == "player":
		model = VIEWS[direction_angle(angle) if view == 999 else view]
	var data: Dictionary = models[model]
	var clip := ""
	var index := 0
	if kind == "boss" and windup > 0.0:
		clip = "attack"
		index = mini(int(data.clips[clip].count) - 1, int((1.0 - windup / 1.25) * data.clips[clip].count))
	else:
		clip = ("walk_fire" if recoil > 0.05 else "walk") if moving else ("fire" if recoil > 0.0 else "idle")
		if kind == "boss" and clip == "fire":
			clip = "idle"
		if kind == "player" and data.get("aim_angles") != null:
			var sample := float(data.aim_angles[0])
			for candidate: float in data.aim_angles:
				if absf(candidate - angle) < absf(sample - angle):
					sample = candidate
			clip += "_aim_" + str(int(sample))
		if kind != "player" and kind != "boss":
			clip += "_up" if angle < -20.0 else ("_down" if angle > 20.0 else "")
		var count := int(data.clips[clip].count)
		if moving:
			index = int(stride * count) % count
		elif recoil > 0.0 and kind != "boss":
			index = clampi(int((1.0 - recoil / 0.105) * count), 0, count - 1)
		else:
			index = int(time * 2.0) % count
	return {"model": model, "clip": clip, "index": maxi(0, index)}

func geometry(kind: String, key: Dictionary, facing: int) -> Dictionary:
	var data: Dictionary = models[key.model]
	var factor := Vector2.ONE if kind == "player" else Vector2(SIZES[kind]) / Vector2(SIZES[MODELS[kind]])
	var cell := Iso.vec(data.cell)
	var size := (cell * factor).round()
	var scale := size / cell
	var flipped: bool = facing < 0 and key.model not in ["player_n", "player_s"]
	var result := {"size": size, "scale": scale, "flip": flipped}
	for socket: String in ["anchor", "muzzle", "barrel", "ejection", "waist"]:
		var values: Array
		if socket == "anchor":
			values = data.anchor
		else:
			var plural := socket + "s"
			if not data.clips[key.clip].has(plural):
				continue
			values = data.clips[key.clip][plural][key.index]
		var point := Iso.vec(values) * scale
		if kind == "player" and socket == "anchor":
			point.y += float(registration.ground_shift[key.model])
		if flipped:
			point.x = size.x - point.x
		result[socket] = point
	return result

static func round_even(value: float) -> int:
	# Preserve Python's nearest-even tie rule, including exact stopping phases.
	var lower := floori(value)
	var fraction := value - lower
	if fraction == 0.5:
		return lower if posmod(lower,2) == 0 else lower + 1
	return lower if fraction < 0.5 else lower + 1

func lower_origin(key: Dictionary, facing: int) -> Vector2:
	var waist: Vector2 = geometry("player",key,facing).waist
	return Vector2(round_even(waist.x)-40,round_even(waist.y)-12-int(registration.belt_overlap[key.model]))

func lower_pose(key: Dictionary, facing: int, stride: float, moving: bool, move_view: int, move_facing: int) -> Vector3i:
	var body_view := int(VIEWS.find_key(key.model))
	if not moving:
		return Vector3i(body_view,facing,posmod(round_even(stride*2.0)*2,4))
	return gait_pose(body_view,facing,move_view,move_facing,float(key.index)/float(models[key.model].clips[key.clip].count))

func best_aim(actor: Node2D, preferred: int, time: float, target: Vector2) -> Vector2:
	var result := _best_view(actor, preferred, time, target)
	if result.x > 3.0:
		for view: int in VIEWS:
			if absi(view - preferred) == 45:
				var candidate := _best_view(actor, view, time, target)
				if candidate.x + 0.25 < result.x:
					result = candidate
	return Vector2(result.y, result.z)

func _best_view(actor: Node2D, view: int, time: float, target: Vector2) -> Vector3:
	var result := Vector3(180.0, view, view)
	for angle: float in models[VIEWS[view]].aim_angles:
		var key := pose("player", actor.stride, actor.moving, angle, actor.recoil, time, 0.0, view)
		var geo := geometry("player", key, actor.facing)
		var delta: Vector2 = target - (geo.muzzle - geo.anchor)
		if delta.length_squared() < 16.0:
			continue
		var axis: Vector2 = Iso.unit(geo.muzzle - geo.barrel)
		var error := absf(rad_to_deg(axis.angle_to(delta)))
		if error < result.x:
			result = Vector3(error, view, angle)
	return result

static func gait_pose(body_view: int, facing: int, move_view: int, move_facing: int, phase: float) -> Vector3i:
	var body := float(body_view) if facing >= 0 else wrapf(180.0 - body_view, -180.0, 180.0)
	var travel := float(move_view) if move_facing >= 0 else wrapf(180.0 - move_view, -180.0, 180.0)
	var delta := wrapf(travel - body, -180.0, 180.0)
	var backward := absf(delta) > 90.0
	if backward:
		delta = fposmod(delta + 360.0, 360.0) - 180.0
	var pelvis := deg_to_rad(body + clampf(delta, -45.0, 45.0))
	var leg_facing := 1 if cos(pelvis) >= -0.000001 else -1
	var leg_view := direction_angle(rad_to_deg(atan2(sin(pelvis), absf(cos(pelvis)))))
	var step := int(phase * 4.0) % 4
	return Vector3i(leg_view, leg_facing, posmod(-step, 4) if backward else step)
