from numpy import arange, linspace, sqrt, arcsin, pi, sin, cos, append, array, where
from matplotlib import pyplot as plt
import json

# def load_json(filename):
#     # trying to open a file and load paths
#         try:
#             with open(filename) as f:
#                 path = json.load(f)
#             path = Path(name = path["name"], color = path["color"], last_point = path["last_point"], t = path["coordinates"])
#             return path
#     # exception
#         except Exception:
#             print("error while reading file. check it, please!")

class Path:
    def __init__(self, name = "", color = "black", shift = (1, 1), wall_dimensions = (2, 2)):
        # json
        # self.path = {"name": name, "color": color, "last_point": (0, 0), "coordinates": []}
        self.name = name
        self.color = color
        self.last_point = (0, 0)
        self.coordinates = []
        self.min_wall_size = min(wall_dimensions)
        self.shift_x = shift[0]
        self.shift_y = shift[1]

    def angle_to_radians(self, angle):
        # radians to degrees
        return pi*angle/180

    def convert_angle(self, i, j):
        # calculates x and y coordinates of the point to an angle
        return 180*arcsin(j/sqrt(i**2+j**2))/pi

    def get_angle(self, i, j):
        # converts an angle depending on the quarter of the point
        if j<0 and i<0:
            angle = self.convert_angle(i, -j)
        elif j<0 and i>0:
            angle = 180 - self.convert_angle(i, -j)
        elif j>0 and i>0:
            angle = 180 + self.convert_angle(i, j)
        elif j>0 and i<0:
            angle = 360 - self.convert_angle(i, j)
        elif j==0 and i<0:
            angle = 0
        elif j==0 and i>0:
            angle = 180
        elif j<0 and i==0:
            angle = 90
        elif j>0 and i==0:
            angle = 270
        return angle

    def load_gcode(self, filename, step=3, points_per_meter=20):
        # encodes .gcode file into a path

        spray = False

        x = []
        y = []
        commands = []
        press_values = []

        # lambda for converting GCode string into a command with parameters
        convert_command = lambda a: (a[:1], float(a[1:]))

        # parsing coordinates
        with open(filename, "r") as f:
            for i in f.readlines():
                i = i[:-1]
                command = i.split()
                # G-commands filter
                if len(command) > 2 and command[0][0] == 'G':
                    commands.append(dict(map(convert_command, command)))

        for command in commands:
            # number of a command
            type = command['G']

            # interpolation without spraying
            if type == 0 and 'X' in command.keys() and 'Y' in command.keys():
                x = append(x, array(command['X']))
                y = append(y, array(command['Y']))
                press_values.append(spray)
                last_x, last_y = command['X'], command['Y']

            # spraying state check
            elif (type == 0 or type == 1) and ('Z' in command.keys()):
                z = command['Z']
                if z >= 0:
                    spray = False
                else:
                    spray = True

            # linear interpolation
            elif type == 1 and 'X' in command.keys() and 'Y' in command.keys():
                distance = sqrt((command['X'] - last_x) ** 2 + (command['Y'] - last_y) ** 2)
                # print("distance:", distance)
                # TODO: fix distance calculating
                number_of_points = int(distance * points_per_meter)
                x = append(x, linspace(last_x, command['X'], number_of_points))
                y = append(y, linspace(last_y, command['Y'], number_of_points))
                # print(number_of_points)
                press_values += [spray]*number_of_points
                last_x, last_y = command['X'], command['Y']

            # clockwise interpolation
            elif type == 2:
                angles = []
                ax, ay = last_x, last_y
                bx, by = command['X'], command['Y']
                ai, aj = command['I'], command['J']
                ox, oy = ax + ai, ay + aj
                bi, bj = ox - bx, oy - by
                a_angle = self.get_angle(ai, aj)
                b_angle = self.get_angle(bi, bj)
                if a_angle > b_angle:
                    angles = linspace(a_angle, b_angle, int((a_angle-b_angle)//step))
                elif a_angle < b_angle:
                    angles = linspace(a_angle+360, b_angle, int((a_angle+360-b_angle)//step))
                angles = self.angle_to_radians(angles)
                x = append(x, cos(angles) * sqrt(ai**2+aj**2) + ox)
                y = append(y, sin(angles) * sqrt(ai**2+aj**2) + oy)
                press_values += [spray] * len(angles)
                last_x, last_y = command['X'], command['Y']

            # counterclockwise interpolation
            elif type == 3:
                angles = []
                ax, ay = last_x, last_y
                bx, by = command['X'], command['Y']
                ai, aj = command['I'], command['J']
                ox, oy = ax + ai, ay + aj
                bi, bj = ox - bx, oy - by
                a_angle = self.get_angle(ai, aj)
                b_angle = self.get_angle(bi, bj)
                if a_angle > b_angle:
                    angles = linspace(a_angle, b_angle+360, int((b_angle+360-a_angle)//step))
                elif a_angle < b_angle:
                    angles = linspace(a_angle, b_angle, int((b_angle-a_angle)//step))
                angles = self.angle_to_radians(angles)
                x = append(x, cos(angles) * sqrt(ai**2+aj**2) + ox)
                y = append(y, sin(angles) * sqrt(ai**2+aj**2) + oy)
                press_values += [spray] * len(angles)
                last_x, last_y = command['X'], command['Y']

        # coordinates scaling
        max_image_size = max(max(x) - min(x), max(y) - min(y))
        k = self.min_wall_size / max_image_size
        x *= k
        y *= k

        # coordinates shifting
        x += self.shift_x
        y += self.shift_y

        # setting lowest point first
        x = list(x)
        y = list(y)
        min_index = len(y) - y[::-1].index(min(y)) - 1
        x = x[min_index:] +  x[:min_index]
        y = y[min_index:] +  y[:min_index]

        # rounding to 2 decimal places after point
        round_digits = lambda a: round(a * 10 ** 2)/10 ** 2
        x = list(map(round_digits, x))
        y = list(map(round_digits, y))
        x = array(x)
        y = array(y)

        # merging coordinates into a list of points with press values
        if len(x) == len(y) and len(y) == len(press_values):
            for i in range(len(x)):
                 self.coordinates.append({"id" : i, "x" : x[i], "y" : y[i], "spray" : press_values[i]})

        # setting first point last
        first_point = self.coordinates[0]
        self.last_point = first_point["x"], first_point["y"]

    def plot(self, filename):
        plt.axis('equal')
        for coordinate in self.coordinates:
            plt.plot(coordinate["x"], coordinate["y"], "o")
        plt.savefig(filename)

    def load_json(self, filename):
        # trying to open a file and load path
            try:
                with open(filename) as f:
                    path = json.load(f)
                if len(path) != 0:
                    self.name = path["name"]
                    self.color = path["color"]
                    self.last_point = path["last_point"]
                    self.coordinates = path["coordinates"]
                else:
                    print "file is empty"
        # exception
            except Exception:
                print "error while reading file. check it, please!"

    def write_json(self, filename):
        path = {"name": self.name, "color": self.color, "last_point": self.last_point, "coordinates": self.coordinates}
        with open(filename, "w") as f:
            f.write(json.dumps(path, indent=4))
