extends SceneTree
## Audit imported alpha using the exact registration helpers used by Sprite2D.
var poses: PoseLibrary
var sheets: Dictionary = {}
var belts: Dictionary = {}

func _initialize() -> void:
	run.call_deferred()

func belt_points(gait: Vector3i) -> Array[Vector2i]:
	if belts.has(gait):
		return belts[gait]
	var vertical := absi(gait.x)==90
	var step := gait.z%2 if vertical else gait.z
	var flip := gait.z>=2 if vertical else gait.y<0
	var source: Image = poses.texture("res://assets/rendered/walk/%d.png" % gait.x).get_image()
	var points: Array[Vector2i] = []
	for y in range(12,24):
		for x in range(80):
			if roundi(source.get_pixel(step*80+(79-x if flip else x),y).a*255.0)>64:
				points.append(Vector2i(x,y))
	belts[gait]=points
	return points

func run() -> void:
	poses=PoseLibrary.new()
	var total:=0
	var failures:=0
	var report: Dictionary={}
	for view: int in PoseLibrary.VIEWS:
		var model: String=PoseLibrary.VIEWS[view]
		var data: Dictionary=poses.models[model]
		var minimum:=100000
		var worst: Array=[]
		for clip_name: String in data.clips:
			var clip: Dictionary=data.clips[clip_name]
			if not str(clip.path).contains("/upper/"):
				continue
			var sheet: Image=poses.texture(clip.path).get_image()
			for index in range(int(clip.count)):
				for facing in [1,-1]:
					var upper:=sheet.get_region(Rect2i(index*int(data.cell[0]),0,int(data.cell[0]),int(data.cell[1])))
					if facing<0 and absi(view)!=90:
						upper.flip_x()
					var mask:=BitMap.new()
					mask.create_from_image_alpha(upper,64.0/255.0)
					var key: Dictionary={"model":model,"clip":clip_name,"index":index}
					var origin:=Vector2i(poses.lower_origin(key,facing))
					var gaits: Dictionary={}
					if clip_name.begins_with("walk"):
						for travel: int in PoseLibrary.VIEWS:
							for side in [1,-1]:
								gaits[PoseLibrary.gait_pose(view,facing,travel,side,float(index)/float(clip.count))]=true
					else:
						gaits[Vector3i(view,facing,0)]=true
						gaits[Vector3i(view,facing,2)]=true
					for gait: Vector3i in gaits:
						var overlap:=0
						for pixel: Vector2i in belt_points(gait):
							var point:=pixel+origin
							if Rect2i(Vector2i.ZERO,mask.get_size()).has_point(point) and mask.get_bitv(point):
								overlap+=1
						if overlap<minimum:
							minimum=overlap
							worst=[clip_name,index,facing,gait.x,gait.y,gait.z]
						if overlap<32:
							failures+=1
						total+=1
		report[model]={"minimum_belt_overlap_pixels":minimum,"worst_case":worst}
		print("SEAM %s minimum=%d" % [model,minimum])
	report["checked_combinations"]=total
	DirAccess.make_dir_recursive_absolute("res://artifacts")
	var file:=FileAccess.open("res://artifacts/seams-godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t")+"\n")
	file.close()
	if failures>0 or total!=17112:
		push_error("SEAM FAIL: %d inadequate overlaps, %d combinations" % [failures,total])
		quit(1)
	else:
		print("SEAM PASS: %d combinations; all overlaps >=32 pixels at alpha >64" % total)
		quit(0)
