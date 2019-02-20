from graffiti_drone import path

heart = path.Path(shift=(0,0.9), wall_dimensions=(1.5,1.5))
heart.load_gcode("gcode/heart.nc")
heart.write_json("json/new.json")
heart.plot("images/new.png")
