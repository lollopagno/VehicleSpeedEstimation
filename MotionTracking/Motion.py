import cv2 as cv
import numpy as np

import Common.color as Color
import Common.utility as Utility
from Common.table import COLUMN_VELOCITY, COLUMN_DIRECTION, COLUMN_STATIONARY
from Common.utility import log
from MotionTracking.Vehicle import UNKNOWN
from MotionTracking.Vehicle import Vehicle


def detect_motion_sparse(img, frame_1, frame_2, kernel=None, filter_blur=(5, 5), iter_dilate=4, VALUE_AREA=150):
    r"""

    """
    frame_1 = cv.cvtColor(frame_1, cv.COLOR_GRAY2BGR)
    frame_2 = cv.cvtColor(frame_2, cv.COLOR_GRAY2BGR)

    diff = cv.absdiff(frame_1, frame_2)
    diff_gray = cv.cvtColor(diff, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(diff_gray, filter_blur, 0)
    _, thresh = cv.threshold(blur, 20, 255, cv.THRESH_BINARY)

    dilate = cv.dilate(thresh, kernel, iterations=iter_dilate)

    cv.imshow("Dilate", dilate)
    cv.waitKey(1)

    contours, _ = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        (x, y, w, h) = cv.boundingRect(cnt)
        area = cv.contourArea(cnt)

        if area <= VALUE_AREA:
            continue

        cv.rectangle(img, (x, y), (x + w, y + h), Color.RED, 2)


def discard_area(cnt, polygons, img, excluded_area):
    (x, y, w, h) = cv.boundingRect(cnt)
    coordinates = ((x, y), (x + w, y + h))

    if Utility.get_area(cnt):
        # Discard small areas
        return True, []

    if not excluded_area:
        if Utility.check_polygon(img, polygons, coordinates=coordinates):
            # Check if the point is inside the polygon
            return True, []

    return False, coordinates


class Motion:
    """
    Class to detect moving vehicles.
    """

    def __init__(self, table):
        """
        Constructor of class Motion.

        :param table object table.
        """
        # Number of the vehicles
        self.counter_vehicle = 0

        # Iteration number
        self.iteration = 0

        # Frame Rate
        self.fps = 0

        # Mask: [HSV Model] hue (direction of car), value (velocity), saturation (unused)
        # Each row of mask: (hue  [ANGLE], saturation, value [VELOCITY])
        self.mask_hsv = None
        self.angle = None
        self.magnitude = None

        # Table
        self.table = table

        # Vehicle list
        self.prev_vehicles = []
        self.current_vehicles = []
        self.deleted_vehicles = []
        self.vehicles_stationary = []

        self.color_list = []

        self.vehicles_to_draw = []

        # Maximum num frame before deleting the vehicle history
        self.num_frame_to_remove_vehicle_history = 10

    def detect_vehicle(self, img, flow, iter, fps, polygons, excluded_area):
        r"""
        Detect vehicle into img.
        :param img: img.
        :param flow: optical flow.
        :param iter: current iteration.
        :param fps: current frame per second.
        :param polygons: polygons of the city.
        :param excluded_area: bool, if true it doesn't consider the polygon.
        """

        self.iteration = iter
        self.fps = fps

        if self.mask_hsv is None:
            self.mask_hsv = np.zeros_like(img)
            self.mask_hsv[..., 1] = 255

        self.magnitude, self.angle = cv.cartToPolar(flow[:, :, 0], flow[:, :, 1])
        self.mask_hsv[..., 0] = self.angle * 180 / np.pi / 2
        self.mask_hsv[..., 2] = cv.normalize(self.magnitude, None, 0, 255, cv.NORM_MINMAX)

        mask_rgb = cv.cvtColor(self.mask_hsv, cv.COLOR_HSV2BGR)
        mask = np.zeros_like(img)
        self.mask_hsv = cv.addWeighted(mask, 1, mask_rgb, 2, 0)

        contours = self.morphological_operations()
        self.vehicles_to_draw.clear()

        if len(self.prev_vehicles) == 0:
            log(0, "NO vehicles (if)")
            """
            Adds new vehicles only to the first iteration or 
            when the scene is devoid of vehicles.
            """

            num_cnt = len(contours)
            for num, cnt in enumerate(contours):
                ret, coordinates = discard_area(cnt, polygons, img, excluded_area)

                if ret:
                    continue

                vehicle = self.check_vehicle_by_colors(coordinates)
                if vehicle is None:
                    # Checks if the vehicle was already tracked
                    ret = self.check_repaint_vehicles(coordinates, "Repaint without vehicles")

                    if not ret:
                        # New vehicle added
                        self.create_new_vehicle(coordinates)

            # Updates list to draw vehicles and update table
            Utility.draw_vehicles(self.vehicles_to_draw, img)
            self.table.add_rows(self.vehicles_to_draw)

        else:
            log(0, "YES vehicles (else)")
            """
            Adds new vehicles previous frame.
            """
            tmp_new_coordinates = []

            num_cnt = len(contours)
            for num, cnt in enumerate(contours):
                ret, coordinates = discard_area(cnt, polygons, img, excluded_area)

                if ret:
                    continue

                vehicle = self.check_vehicle_by_colors(coordinates)
                if vehicle is None:
                    vehicle = self.tracking(coordinates=coordinates, img=img)

                    if vehicle is None:
                        tmp_new_coordinates.append(coordinates)

            for coordinates in tmp_new_coordinates:
                self.add_new_vehicles(coordinates)

            Utility.draw_vehicles(self.vehicles_to_draw, img)
            self.table.add_rows(self.vehicles_to_draw)

            for vehicle in self.prev_vehicles:
                # Deletes vehicles to no longer track

                for index, color in enumerate(self.color_list):
                    if color == vehicle.color:
                        del self.color_list[index]
                        break

                self.table.delete_row(vehicle.name)

                # Add vehicles to history list
                vehicle.set_iteration(self.iteration)
                self.deleted_vehicles.append(vehicle)

                # Remove the vehicle if it was previously stationary
                self.vehicles_stationary, ret = Utility.delete_item_in_list(self.vehicles_stationary, vehicle.name)
                if ret:
                    vehicle.unmarked_as_stationary()
                    self.table.update_table(vehicle.name, COLUMN_STATIONARY, vehicle.is_stationary)

        # Updates lists
        print(f"iter {self.iteration}")
        print("prev_vehicles")
        for i in self.prev_vehicles:
            print(i.to_string() + "\n")

        print("current vehicles")
        for i in self.current_vehicles:
            print(i.to_string() + "\n")

        self.prev_vehicles = self.current_vehicles.copy()
        self.current_vehicles.clear()

        # Deletes vehicles history after N iterations
        tmp_list = []
        for del_vehicle in self.deleted_vehicles:
            iter = del_vehicle.iteration

            if not iter == self.iteration - self.num_frame_to_remove_vehicle_history:
                tmp_list.append(del_vehicle)

        # Updates vehicles history list
        self.deleted_vehicles = tmp_list.copy()

    def get_distance(self, coordinates, list, max_distance, _log, default_distance=150):
        """
        Calculates the distance among all vehicles detected.

        :param coordinates: coordinates of the next bounding box (vehicle)
        :param list: list of vehicles to loop.
        :param max_distance: maximum allowable distance in the search for the vehicle.
        :param default_distance: default value minimum distance.

        :return min_distance: smaller distance located relative to new_coordinates.
        :return result: information of the vehicle extracted on the basis of new_coordinates.
        """

        new_centroid = Utility.get_centroid(coordinates)
        dist_already_calculated = []

        min_distance = default_distance
        result = None

        print(f"Search to find minimum distance {_log} with {coordinates}")
        for box in list:

            if not box.name in dist_already_calculated:
                # Check if the vehicle has been already controlled.
                dist_already_calculated.append(box.name)

                _centroid = box.centroid
                distance = Utility.get_length(new_centroid, _centroid)

                if max_distance > distance >= 0:
                    # Check if the vehicle has a distance between the values.

                    direction = Utility.get_direction(f"Vehicle [{box.name}] to find", coordinates, self.angle,
                                                      self.magnitude)

                    if (box.get_direction() == UNKNOWN or direction == box.get_direction()) \
                            or distance <= 50:  # TODO check this distance
                        # Check if the vehicle has the same direction

                        if min_distance == default_distance or distance < min_distance:
                            # Updates variables
                            min_distance = distance  # Minimum distance between vehicles
                            result = box  # Vehicle to be returned

                            log(0, f"Update bounding box for {box.name}, [Distance]: {min_distance} with {_log}")

                            if min_distance == 0:
                                break

        name = None
        if result is not None:
            name = result.name
        print(f"Returned value with {min_distance} of {name}")
        return min_distance, result

    def morphological_operations(self):
        """
        Performs morphological operations on the mask.

        :return contours: contours detect by mask.
        """

        mask_gray = cv.cvtColor(self.mask_hsv, cv.COLOR_BGR2GRAY)
        _, mask_bin = cv.threshold(mask_gray, 20, 255, cv.THRESH_BINARY)

        # Morphological operations
        kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        mask_erode = cv.erode(mask_bin, kernel, iterations=12)
        mask_dilate = cv.dilate(mask_erode, kernel, iterations=1)

        # Find contours
        contours, _ = cv.findContours(mask_dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

        # Mask binary
        mask_binary = cv.resize(mask_dilate, (400, 400))
        mask_binary = cv.cvtColor(mask_binary, cv.COLOR_GRAY2RGB)

        Utility.set_text(mask_binary, str(len(contours)), (320, 380), color=Color.RED, thickness=3)

        mask = cv.resize(self.mask_hsv, (400, 400))
        stack = Utility.stack_images(1, ([mask_binary, mask]))
        cv.imshow("Masks", stack)
        cv.waitKey(1)

        return contours

    def create_new_vehicle(self, coordinates):
        name = f"Vehicle {self.counter_vehicle + 1}"
        log(0, f"Added the new {name} with coordinates {coordinates}")

        # Update vehicles list
        direction = Utility.get_direction(name, coordinates, self.angle, self.magnitude)
        coordinates = Utility.get_coordinates_bb(points=coordinates)
        intensity = Utility.get_intensity(self.mask_hsv, coordinates)

        color, self.color_list = Utility.get_random_color(self.color_list)
        vehicle = Vehicle(name, coordinates, intensity, color, direction)

        self.current_vehicles.append(vehicle)
        self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)
        self.counter_vehicle += 1

    def tracking(self, coordinates, img, max_distance=30):
        """
        Tracking vehicles based on the minimum distance between all bounding boxes.

        :param coordinates: coordinates of the next bounding box (vehicle).
        :param img: img to draw in.
        :param max_distance: maximum distance in pixel allowed.

        :return vehicle: if different from None, return vehicle object
        """

        min_distance, vehicle = self.get_distance(coordinates,
                                                  self.prev_vehicles,
                                                  max_distance=max_distance,
                                                  _log="add new_vehicles")

        if vehicle is not None:

            if Utility.check_exit_to_the_scene(img, vehicle.coordinates):
                """
                Checks if the vehicles no longer present (out of the scene).
                """
                log(0, f"Remove {vehicle.name} (not displayed)")
                self.vehicles_stationary, ret = Utility.delete_item_in_list(self.vehicles_stationary, vehicle.name)
                if ret:
                    vehicle.unmarked_as_stationary()
                    self.table.update_table(vehicle.name, COLUMN_STATIONARY, vehicle.is_stationary)

            elif min_distance == 0:
                """
                Detects if there are stationary vehicles.
                """

                # Temporary list to modify it a run time.
                tmp_vehicles_stationary = self.vehicles_stationary.copy()

                for index, stat_vehicle in enumerate(self.vehicles_stationary):

                    if stat_vehicle.name == vehicle.name:
                        # Search for vehicles in the list of stationary vehicles.
                        num_stat = stat_vehicle.num_frame_to_remove_vehicle - 1

                        if num_stat != 0:
                            # The vehicle is still shown
                            stat_vehicle.decrease_frame_stationary()

                            self.current_vehicles.append(stat_vehicle)
                            self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, stat_vehicle.name)
                            self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, stat_vehicle)

                        elif num_stat == 0:
                            # Deletes vehicle in the list of stationary vehicles. No tracking.
                            stat_vehicle.unmarked_as_stationary()
                            self.table.update_table(stat_vehicle.name, COLUMN_STATIONARY, stat_vehicle.is_stationary)
                            del tmp_vehicles_stationary[index]
                        break

                    if index + 1 == len(self.vehicles_stationary):
                        # Vehicle wasn't on vehicles_stationary list.
                        vehicle.marked_as_stationary()
                        self.table.update_table(vehicle.name, COLUMN_STATIONARY, vehicle.is_stationary)

                        direction = Utility.get_direction(vehicle.name, coordinates, self.angle, self.magnitude)
                        vehicle.set_direction(direction)
                        self.table.update_table(vehicle.name, COLUMN_DIRECTION, vehicle.get_direction())

                        tmp_vehicles_stationary.append(vehicle)
                        self.current_vehicles.append(vehicle)
                        self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)
                        self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)

                # Updates stationary list.
                self.vehicles_stationary = tmp_vehicles_stationary.copy()

                if len(self.vehicles_stationary) == 0:
                    # The list of the stationary vehicles is empty.
                    log(0, f"Added new {vehicle.name} as stationary vehicle.")
                    vehicle.marked_as_stationary()
                    self.table.update_table(vehicle.name, COLUMN_STATIONARY, vehicle.is_stationary)

                    # Update direction
                    direction = Utility.get_direction(vehicle.name, coordinates, self.angle, self.magnitude)
                    vehicle.set_direction(direction)
                    self.table.update_table(vehicle.name, COLUMN_DIRECTION, vehicle.get_direction())

                    # Update intensity
                    intensity = Utility.get_intensity(self.mask_hsv, coordinates)
                    vehicle.set_intensity(intensity)

                    self.vehicles_stationary.append(vehicle)
                    self.current_vehicles.append(vehicle)
                    self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)
                    self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

            elif min_distance < max_distance:
                """
                Adds new vehicles present to the previous frame.
                """

                log(0, f"Update {vehicle.name} with min_distance {min_distance} with {coordinates}")

                # Update coordinates
                vehicle.set_coordinates(Utility.get_coordinates_bb(points=coordinates))

                # Update velocity
                velocity = Utility.get_velocity(distance=min_distance, fps=self.fps)
                vehicle.set_velocity(velocity)

                # Update direction
                direction = Utility.get_direction(vehicle.name, coordinates, self.angle, self.magnitude)
                vehicle.set_direction(direction)

                # Update intensity
                intensity = Utility.get_intensity(self.mask_hsv, coordinates)
                vehicle.set_intensity(intensity)

                self.table.update_table(vehicle.name, COLUMN_DIRECTION, vehicle.get_direction())
                self.table.update_table(vehicle.name, COLUMN_VELOCITY, f"{vehicle.velocity} km/h")

                self.current_vehicles.append(vehicle)
                self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)
                self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)

                # Remove the vehicle if it was previously stationary
                self.vehicles_stationary, ret = Utility.delete_item_in_list(self.vehicles_stationary, vehicle.name)
                if ret:
                    vehicle.unmarked_as_stationary()
                    self.table.update_table(vehicle.name, COLUMN_STATIONARY, vehicle.is_stationary)

        return vehicle

    def add_new_vehicles(self, coordinates):
        """
        Adds new vehicles when not present at the previous frame.

        :param coordinates:  coordinates of the next bounding box (vehicle).

        :return vehicle: vehicle to be drawn.
        """
        ret = self.check_repaint_vehicles(coordinates, "Repaint in add_vehicles ")

        if not ret:
            # New vehicle added to the scene
            self.create_new_vehicle(coordinates)

    def check_repaint_vehicles(self, coordinates, _log):
        """
        Check if there are vehicles to be redesigned.

        :param coordinates: coordinates of the last position of the vehicle.

        :return True if the vehicle need to be redesigned, false otherwise.
        """
        max_distance = 70
        min_distance, result = self.get_distance(coordinates, self.deleted_vehicles, max_distance=max_distance,
                                                 _log="Repaint")

        if min_distance < max_distance and result is not None:

            # Check if the vehicle is already to be drawn
            # TODO check this!
            flag = False
            for vehicle_to_draw in self.vehicles_to_draw:
                if result.name == vehicle_to_draw.name:
                    flag = True
                    break

            if not flag:
                log(3, f"{_log} {result.name}")

                # Update direction
                direction = Utility.get_direction(result.name, coordinates, self.angle, self.magnitude)
                result.set_direction(direction)
                self.table.update_table(result.name, COLUMN_DIRECTION, result.get_direction())

                # Update coordinates
                coordinates = Utility.get_coordinates_bb(points=coordinates)
                result.set_coordinates(coordinates)

                # Update intensity
                intensity = Utility.get_intensity(self.mask_hsv, coordinates)
                result.set_intensity(intensity)

                # Update lists
                self.current_vehicles.append(result)
                self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, result.name)
                self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, result)

                return True

        return False

    def check_vehicle_by_colors(self, coordinates):
        """
        ....
        """
        intensity_to_compare = Utility.get_intensity(self.mask_hsv, coordinates)
        h, s, v = intensity_to_compare

        result = None
        values_range = 15

        for vehicle in self.current_vehicles:

            intensity = vehicle.average_intensity

            print(f"Intensity Vehicle: {vehicle.name}, {vehicle.average_intensity} of coordinates "
                  f"{vehicle.coordinates} compare to {intensity_to_compare} of coordinates {coordinates}")

            if not h - values_range <= intensity[0] <= h + values_range:
                print("Exclude for h")
                continue

            if not s - values_range <= intensity[1] <= s + values_range:
                print("Exclude for s")
                continue

            if not v - values_range <= intensity[2] <= v + values_range:
                print("Exclude for v")
                continue

            (x_start_1, y_start_1), _, _, (x_end_1, y_end_1) = vehicle.coordinates
            (x_start_2, y_start_2), (x_end_2, y_end_2) = coordinates

            if x_start_1 < x_start_2:
                print(f"1-BB fusion: {(x_start_1, y_start_1), (x_end_2, y_end_2)}")
                vehicle.set_coordinates(Utility.get_coordinates_bb(points=((x_start_1, y_start_1), (x_end_2, y_end_2))))
            else:
                print(f"2-BB fusion: {(x_start_2, y_start_2), (x_end_1, y_end_1)}")
                vehicle.set_coordinates(Utility.get_coordinates_bb(points=((x_start_2, y_start_2), (x_end_1, y_end_1))))

            self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)
            result = vehicle
            break

        return result
