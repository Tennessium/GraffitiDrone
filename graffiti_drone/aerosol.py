import serial, rospy

class Aerosol(object):
    def __init__(self, color, up_value=800, down_value=500):
        self.color = color
        self.up_value = up_value
        self.down_value = down_value
        self.value = False

        self.ser = serial.Serial(port='/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0', baudrate=9600)
        self.ser.write(str(up_value))

    def spray(self, value):
        self.value = value
    	if value:
    	    self.ser.write(str(self.down_value))
    	else:
    	    self.ser.write(str(self.up_value))
    	rospy.sleep(6)
