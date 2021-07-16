import numpy as np

import common.color as Color


#####
# 0- Taipei
# 1- Busan
# 2- Jackson Hole
# 3- Derry
# 4- Cambridge
####


class Tracking:

    def __init__(self, info_city):
        self.num_city = info_city["Index"]
        self.name_city = info_city["Name"]
        self.lane = info_city["Lane"]

        self.colors_list = [Color.VIOLA, Color.CYAN, Color.YELLOW, Color.GREEN]

    def get_frame_rate_polygon(self):
        if self.num_city == 0:
            return np.array([[590, 18], [590, 50], [725, 50], [725, 18]])
        else:
            return np.array([])

    def get_view_polygon(self):
        if self.num_city == 0:
            return np.array([[56, 278], [184, 277], [222, 507], [71, 509], [55, 384], [56, 416], [61, 456]])
        else:
            return np.array([])

    def get_rectangle_polygon(self):
        if self.num_city == 0:
            return np.array([[12, 11], [144, 11], [144, 65], [12, 65]])
        else:
            return np.array([])

    def get_number_lane(self):
        if self.num_city == 0:
            return 2
        else:
            return 0

    def get_color(self, index):
        return self.colors_list[index]

    def get_lane(self, index):
        if self.num_city == 0:
            if index == 0:
                return np.array([[140, 271], [182, 274], [187, 312], [149, 312]])
            elif index == 1:
                return np.array([[138, 271], [98, 271], [103, 314], [147, 313]])
        else:
            return np.array([])

    def get_motion(self):
        if self.num_city == 4:
            iteration_dilate = 8
            kernel = np.ones((3, 3), np.uint8)
            area = 500
            filter = (5, 5)

            return kernel, filter, area, iteration_dilate

        else:
            return None, None, None, None
