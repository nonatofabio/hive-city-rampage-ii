extends SceneTree
func _initialize() -> void:
	var source := Image.load_from_file(ProjectSettings.globalize_path("res://../art/orks/atlas.png"))
	var names := ["boy","shoota","warboss"]
	var rows := [0,304,600,1024]
	var cols := [0,408,782,1170,1536]
	for row in 3:
		var frames: Array[Image]=[]
		var biggest := Vector2i.ZERO
		for col in 4:
			var part := source.get_region(Rect2i(cols[col],rows[row],cols[col+1]-cols[col],rows[row+1]-rows[row]))
			part=part.get_region(part.get_used_rect()); frames.append(part)
			biggest.x=maxi(biggest.x,part.get_width()); biggest.y=maxi(biggest.y,part.get_height())
		var factor := minf(120.0/biggest.x,138.0/biggest.y)
		var sheet := Image.create(512,144,false,Image.FORMAT_RGBA8)
		for col in 4:
			var part:=frames[col]
			part.resize(roundi(part.get_width()*factor),roundi(part.get_height()*factor),Image.INTERPOLATE_LANCZOS)
			sheet.blit_rect(part,Rect2i(Vector2i.ZERO,part.get_size()),Vector2i(col*128+(128-part.get_width())/2,140-part.get_height()))
		sheet.save_png("res://assets/orks/"+names[row]+".png")
	quit()
