extends SceneTree
func _initialize() -> void:
	var source:=Image.load_from_file(ProjectSettings.globalize_path("res://../art/industry/atlas.png"))
	var names:=["pump","wall","furnace","vent","banner","pump_secured"]
	var boxes:=[Rect2i(0,0,535,540),Rect2i(535,0,510,555),Rect2i(1050,0,486,540),Rect2i(0,555,530,469),Rect2i(535,515,495,509),Rect2i(1030,540,506,484)]
	var widths:=[130,250,170,160,85,130]
	for i in 6:
		var part:=source.get_region(boxes[i]); part.convert(Image.FORMAT_RGBA8)
		for y in part.get_height():
			for x in part.get_width():
				var p:=part.get_pixel(x,y)
				if p.a<0.05 or (i==1 and y>355+x*0.45) or (i==4 and y+515<355+x*0.45): part.set_pixel(x,y,Color.TRANSPARENT)
		part=part.get_region(part.get_used_rect())
		part.resize(widths[i],roundi(float(part.get_height())*widths[i]/part.get_width()),Image.INTERPOLATE_LANCZOS)
		part.save_png("res://assets/industry/"+names[i]+".png")
	quit()
