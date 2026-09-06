class_name Iso
extends RefCounted
## Combat stays in flat world coordinates. Only the presentation is projected.

static func project(p: Vector2) -> Vector2:
	return Vector2(p.x - p.y, (p.x + p.y) * 0.5)

static func unproject(p: Vector2) -> Vector2:
	return Vector2(p.x * 0.5 + p.y, p.y - p.x * 0.5)

static func vec(a: Array) -> Vector2:
	return Vector2(a[0], a[1])

static func unit(p: Vector2) -> Vector2:
	return p.normalized() if p.length_squared() > 0.001 else Vector2.RIGHT

static func segment_entry(a: Vector2, b: Vector2, center: Vector2, radius: float) -> float:
	var delta := b - a
	var offset := a - center
	var c := offset.length_squared() - radius * radius
	if c <= 0.0:
		return 0.0
	var length2 := delta.length_squared()
	if length2 == 0.0:
		return -1.0
	var dot := offset.dot(delta)
	var discriminant := dot * dot - length2 * c
	if discriminant < 0.0:
		return -1.0
	var t := (-dot - sqrt(discriminant)) / length2
	return t if t >= 0.0 and t <= 1.0 else -1.0
