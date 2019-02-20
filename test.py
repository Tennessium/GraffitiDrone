import math

from graffiti_drone import path, flight
# from graffiti_drone import path

heart = path.Path()
heart.load_json("json/new1.json")
# heart.plot("test.png")

heart_flight = flight.Flight(wall_yaw=math.pi/2)
heart_flight.draw(heart, y=0.5, delay_ratio=3)
