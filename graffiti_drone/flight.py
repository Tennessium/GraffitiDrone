#!/usr/bin/python
# importing
import math, rospy
from tqdm import tqdm
from clever import srv
from aerosol import Aerosol
# from neopixel import *
from std_srvs.srv import Trigger
from mavros_msgs.srv import SetMode
from mavros_msgs.srv import CommandBool

class Flight:
    def __init__(self, wall_yaw=0):
        # proxy init
	self.set_attitude = rospy.ServiceProxy('set_attitude', srv.SetAttitude)
        self.navigate = rospy.ServiceProxy('/navigate', srv.Navigate)
        self.set_mode = rospy.ServiceProxy('/mavros/set_mode', SetMode)
        self.arming = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
        self.get_telemetry = rospy.ServiceProxy('/get_telemetry', srv.GetTelemetry)
        self.set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
        self.set_rates = rospy.ServiceProxy('/set_rates', srv.SetRates)
        self.frame_id = 'aruco_map'
        self.wall_yaw = wall_yaw
        # z speed check
        if abs(self.get_telemetry("aruco_map").vz) > 1:
            print "show aruco's and run the script again"
            exit()
        print "init done"

    def take_off(self):
        print "take off begin"
        zp = 1
        self.navigate(z=zp, speed=1, frame_id='fcu_horiz', auto_arm=True)
        self.sleep(1.2)

    def get_distance(self, x1, y1, z1, x2, y2, z2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

    def get_to(self, xp, yp, zp, sp=0.3, yaw=0, yaw_rate=0, auto_arm=False, tol=0.15, freq=10):
        print "navigate to:", xp, yp, zp
        print self.navigate(frame_id='aruco_map', x=xp, y=yp, z=zp, speed=sp, yaw=yaw, yaw_rate=yaw_rate, update_frame=True)
        print "waiting for right tolerance"
        while True:
            telem = self.get_telemetry(frame_id='aruco_map')
            distance = self.get_distance(xp, yp, zp, telem.x, telem.y, telem.z)
            print distance
            if distance < tol:
                print("I am at x :" + str(xp) + "  y :" + str(yp) + "  z :" + str(zp))
                break
            self.sleep(1/freq, show=False)

    def set_to(self, x, y, z, distance, delay_ratio, yaw=0):
        print self.navigate(x=x, y=y, z=z, frame_id='aruco_map', yaw=1.57, speed=9999)
        self.sleep(distance * delay_ratio, show=False)

    def draw(self, path, y=0, delay_ratio = 2.2):
        # paint can init
        can = Aerosol(path.color)
        print "starting drawing " + path.name + " path"
        a = raw_input("mount " + path.color + " color can and press enter")
        # coordinates check
        coordinates = path.coordinates
        if len(coordinates) == 0:
            print "error: there is no coordinates in your path"
            return
        # take off
        self.take_off()
        # navigate to the first point of path (adding shifts)
        first_point = coordinates[0]
        self.get_to(first_point["x"], y, first_point["y"], yaw=self.wall_yaw)
        # drawing the path
        print "now i'm really drawing " + path.name + " path"

	#print self.set_attitude(yaw=1.57)
        # trying to draw a path
        # try:
        for i in tqdm(range(1, len(coordinates))):
            spray = coordinates[i]["spray"]
            if can.value != spray:
                can.spray(spray)
            self.set_to(coordinates[i]["x"], y, coordinates[i]["y"],
                        self.get_distance(coordinates[i]["x"], y, coordinates[i]["y"], coordinates[i-1]["x"], y, coordinates[i-1]["y"]),
                        delay_ratio, yaw=self.wall_yaw)
	can.spray(False)
        # save last point if flight is interrupted


        # landing
        self.land()

    def sleep(self, time, show=True):
        if show:
            print "sleeping for:", time
        rospy.sleep(time)

    def land(self):
        print "Landing..."
        self.set_mode(base_mode=0, custom_mode='AUTO.LAND')
