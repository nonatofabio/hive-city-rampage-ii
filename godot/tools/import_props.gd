extends SceneTree
## Pack the generated color-key atlas into transparent runtime sprites.
func _initialize() -> void:
	var source := Image.load_from_file(ProjectSettings.globalize_path("res://../art/props/atlas.png"))
	if source == null:
		push_error("Missing art/props/atlas.png")
		quit(1)
		return
	source.convert(Image.FORMAT_RGBA8)
	for y in source.get_height():
		for x in source.get_width():
			var p := source.get_pixel(x,y)
			if p.r > 0.65 and p.b > 0.65 and p.g < 0.5:
				source.set_pixel(x,y,Color.TRANSPARENT)
	var names := ["crate_wreck","barrel_wreck","relay_wreck","sandbags","barricade","tank_trap"]
	var widths := [140,112,155,116,108,92]
	var edges := [0,550,1000,1536]
	DirAccess.make_dir_recursive_absolute("res://assets/props")
	for i in 6:
		var col := i%3
		var cell := source.get_region(Rect2i(edges[col],(i/3)*512,edges[col+1]-edges[col],512))
		cell = cell.get_region(cell.get_used_rect())
		cell.resize(widths[i],roundi(float(cell.get_height())*widths[i]/cell.get_width()),Image.INTERPOLATE_LANCZOS)
		if cell.save_png("res://assets/props/"+names[i]+".png") != OK:
			quit(1)
			return
	print("PROP IMPORT PASS: six transparent sprites")
	quit()
