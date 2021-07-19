import numpy as np

import common.color as Color


#####
# 0- Taipei
# 1- Busan
# 2- Jackson Hole
# 3- Derry
# 4- Cambridge
####


class TrackingModule:

    def __init__(self, info_city):
        self.num_city = info_city["Index"]
        self.name_city = info_city["Name"]
        self.lane = info_city["Lane"]

        self.colors_list = [Color.VIOLA, Color.CYAN, Color.YELLOW, Color.GREEN]

    def get_frame_rate_polygon(self):
        r"""
        Get polygon of frame rate.
        """
        if self.num_city == 0:
            return np.array([[590, 18], [590, 50], [725, 50], [725, 18]])
        else:
            return np.array([])

    def get_view_polygon(self):
        r"""
        Get polygon of view of lanes.
        """
        if self.num_city == 0:
            return np.array([[56, 278], [184, 277], [222, 507], [71, 509], [55, 384], [56, 416], [61, 456]])
        else:
            return np.array([])

    def get_rectangle_polygon(self):
        r"""
        Get polygon of view to show location, current hour and current date.
        """
        if self.num_city == 0:
            return np.array([[12, 11], [144, 11], [144, 65], [12, 65]])
        else:
            return np.array([])

    def get_number_lane(self):
        r"""
        Get number of lane of specific city.
        """
        if self.num_city == 0:
            return 2
        else:
            return 0

    def get_color(self, index):
        r"""
        Get specific colors.
        :param index: index of color.
        """
        return self.colors_list[index]

    def get_polygon_lane(self, index):
        r"""
        Get polygon of specific lane.
        :param index: current index.
        """
        if self.num_city == 0:
            if index == 0:
                return np.array([[140, 271], [182, 274], [187, 312], [149, 312]])
            elif index == 1:
                return np.array([[138, 271], [98, 271], [103, 314], [147, 313]])
        else:
            return np.array([])

    def get_motion(self):
        r"""
        Get parameters of motion.
        :return:
        """
        if self.num_city == 4:
            iteration_dilate = 8
            kernel = np.ones((3, 3), np.uint8)
            area = 500
            filter = (5, 5)

            return kernel, filter, area, iteration_dilate

        else:
            return None, None, None, None

    def get_velocity(self, index):
        r"""
        Get area of mask to update velocity.
        :param index: current index.
        """
        if self.num_city == 0:
            if index == 0:
                return tuple((20, 30))
            elif index == 1:
                return tuple((20, 100))
        else:
            return None

    def get_corner(self, index):
        r"""
        Get area of mask to update number of corners.
        :param index: current index.
        """
        if self.num_city == 0:
            if index == 0:
                return tuple((20, 60))
            elif index == 1:
                return tuple((20, 130))
        else:
            return None

    def refresh_mask(self, index, mask):
        r"""
        Refresh mask in specific portion of image.
        :param index: current index.
        :param mask: mask to update.
        """
        if self.num_city == 0:
            if index == 0:
                # Portion image: (y1,y2), (x1,x2)
                mask[13:46, 170:368] = 0
                mask[44:73, 140:192] = 0
                return mask
            elif index == 1:
                mask[84:113, 170:353] = 0
                mask[113:143, 146:210] = 0
                return mask
        else:
            return None

    def draw_numbers(self, index):
        r"""
        Draw number of specific lane.
        :param index: current index
        """
        if self.num_city == 0:
            if index == 0:
                return tuple((145, 257))
            elif index == 1:
                return tuple((100, 257))
        else:
            return None

    def draw_line_between_lane(self, index):
        r"""
        Draw line between lane.
        :param index: current index
        """
        if self.num_city == 0:
            if index == 0:
                return tuple((182, 274)), tuple((217, 508))
            elif index == 1:
                return tuple((140, 271)), tuple((168, 510))
            elif index == 2:
                return tuple((98, 279)), tuple((113, 510))
