import cv2 as cv
import numpy as np

import Common.color as Color
from MotionTracking.Table import COLUMN_VELOCITY, COLUMN_DIRECTION, COLUMN_STATIONARY
from MotionTracking.Utility import log
from MotionTracking.Vehicle import UNKNOWN
from MotionTracking.Vehicle import Vehicle
from MotionTracking import Utility as Utility


class Motion:
    """
    Class to detect moving vehicles.
    """

    def __init__(self, table, excluded_area, show_log, iterations_history=25, iterations_stationary=25):
        """
        Constructor of class Motion.

        :param table object table.
        :param excluded_area: bool, if true it does consider the polygon.
        :param show_log: bool, if true the logs are showed.
        :param iterations_history: maximum number frame before deleting the vehicle history.
        :param iterations_stationary: maximum number frame before deleting the stationary vehicle.
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
        self.num_iterations_to_remove_vehicle_history = iterations_history

        # Maximum num frame before deleting the stationary vehicle
        self.num_iterations_stationary = iterations_stationary

        # Minimum distance to mark a vehicle as stationary.
        self.dist_for_stationary = 1.5

        self.show_log = show_log
        self.excluded_area = excluded_area

    def detect_vehicle(self, img, img_to_draw, flow, iter, fps, polygons):
        r"""
        Detect vehicle into img

        :param img: img.
        :param img_to_draw: img in which to draw vehicles.
        :param flow: optical flow.
        :param iter: current iteration.
        :param fps: current frame per second.
        :param polygons: polygons of the city.
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
            """
            Adds new vehicles only to the first iteration or 
            when the scene is devoid of vehicles.
            """

            for num, cnt in enumerate(contours):
                ret, coordinates = Utility.discard_area(cnt, polygons, self.excluded_area)

                if ret:
                    continue

                vehicle = self.check_vehicle_by_colors(coordinates)
                if vehicle is None:
                    # Checks if the vehicle was already tracked
                    ret = self.check_repaint_vehicles(coordinates)

                    if not ret:
                        # New vehicle added
                        self.create_new_vehicle(coordinates)

            # Updates list to draw vehicles and update table
            Utility.draw_vehicles(self.vehicles_to_draw + self.vehicles_stationary, self.iteration, img_to_draw,
                                  self.show_log)
            self.table.add_rows(self.vehicles_to_draw + self.vehicles_stationary)

        else:
            """
            Adds new vehicles based on previous frame.
            """
            tmp_new_coordinates = []

            for num, cnt in enumerate(contours):
                ret, coordinates = Utility.discard_area(cnt, polygons, self.excluded_area)

                if ret:
                    continue

                vehicle = self.check_vehicle_by_colors(coordinates)
                if vehicle is None:
                    vehicle = self.tracking(coordinates=coordinates, img=img)

                    if vehicle is None:
                        tmp_new_coordinates.append(coordinates)

            for coordinates in tmp_new_coordinates:
                self.add_new_vehicles(coordinates)

            Utility.draw_vehicles(self.vehicles_to_draw + self.vehicles_stationary, self.iteration, img_to_draw,
                                  self.show_log)
            self.table.add_rows(self.vehicles_to_draw + self.vehicles_stationary)

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

        tmp_list = []
        count_deleted = 0

        for index, stat_vehicle in enumerate(self.vehicles_stationary):
            # Remove the vehicle if has been tracked for more than N iteration.

            if stat_vehicle.iteration == self.iteration - self.num_iterations_stationary:
                del tmp_list[index - count_deleted]
                count_deleted += 1

        # Updates vehicles history list
        self.vehicles_stationary = tmp_list.copy()

        # Updates lists
        self.prev_vehicles = self.current_vehicles.copy()
        self.current_vehicles.clear()

        # Deletes vehicles history after N iterations
        tmp_list = self.deleted_vehicles.copy()
        count_deleted = 0
        for index, del_vehicle in enumerate(self.deleted_vehicles):

            if del_vehicle.iteration == self.iteration - self.num_iterations_to_remove_vehicle_history:
                del tmp_list[index - count_deleted]
                count_deleted += 1

        # Updates vehicles history list
        self.deleted_vehicles = tmp_list.copy()

    def get_distance(self, coordinates, list, max_distance, default_distance=150):
        """
        Calculates the distance among all vehicles detected.

        :param coordinates: coordinates of the next bounding box (vehicle).
        :param list: list of vehicles to loop.
        :param max_distance: maximum allowable distance in the search for the vehicle.
        :param default_distance: default value minimum distance.

        :return min_distance: smaller distance located relative to the coordinates.
        :return result: information of the vehicle extracted on the basis of the coordinates.
        """

        new_centroid = Utility.get_centroid(coordinates)
        dist_already_calculated = []

        min_distance = default_distance
        result = None

        for box in list:

            if not box.name in dist_already_calculated:
                # Check if the vehicle has been already controlled.
                dist_already_calculated.append(box.name)

                _centroid = box.centroid
                distance = Utility.get_length(new_centroid, _centroid)

                if max_distance > distance >= 0:
                    # Check if the vehicle has a distance between the values.

                    direction = Utility.get_direction(coordinates, self.angle, self.magnitude)

                    if (box.get_direction() == UNKNOWN or direction == box.get_direction()) or distance <= 50:
                        # Check if the vehicle has the same direction

                        if min_distance == default_distance or distance < min_distance:
                            # Updates variables
                            min_distance = distance  # Minimum distance between vehicles
                            result = box  # Vehicle to be returned

                            if self.show_log:
                                log(0, f"Update bounding box for {box.name}, [Distance]: {min_distance}")

                            if min_distance == 0:
                                break

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
        """
        Create a new vehicles.

        :param coordinates: coordinates of the vehicle.
        """

        name = f"Vehicle {self.counter_vehicle + 1}"
        if self.show_log:
            log(0, f"Added the new {name} with coordinates {coordinates}")

        # Update vehicles list
        direction = Utility.get_direction(coordinates, self.angle, self.magnitude)
        coordinates = Utility.get_coordinates_bb(points=coordinates)
        intensity = Utility.get_intensity(self.mask_hsv, coordinates)

        color, self.color_list = Utility.get_random_color(self.color_list)
        vehicle = Vehicle(name, coordinates, intensity, color, self.num_iterations_stationary, direction)

        self.current_vehicles.append(vehicle)
        self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)
        self.counter_vehicle += 1

    def tracking(self, coordinates, img, max_distance=30):
        """
        Tracking vehicles based on the minimum distance between all bounding boxes.

        :param coordinates: coordinates of the next bounding box (vehicle).
        :param img: img to draw in.
        :param max_distance: maximum distance in pixel allowed.

        :return vehicle: if different from None, return vehicle object.
        """

        min_distance, vehicle = self.get_distance(coordinates,
                                                  self.prev_vehicles + self.vehicles_stationary,
                                                  max_distance=max_distance)

        if vehicle is not None:

            if Utility.check_exit_to_the_scene(img, vehicle.coordinates):
                """
                Checks if the vehicles no longer present (out of the scene).
                """
                if self.show_log:
                    log(0, f"Remove {vehicle.name} (not displayed)")

                self.deleted_vehicles, _ = Utility.delete_all_items_in_list(self.deleted_vehicles, vehicle.name)
                self.prev_vehicles, _ = Utility.delete_all_items_in_list(self.prev_vehicles, vehicle.name)
                self.vehicles_stationary, ret = Utility.delete_item_in_list(self.vehicles_stationary, vehicle.name)
                self.table.delete_row(vehicle.name)

            elif min_distance < self.dist_for_stationary:
                """
                Detects if there are stationary vehicles.
                """

                self.add_vehicles_stationary(vehicle, min_distance, coordinates)

            elif min_distance < max_distance:
                """
                Adds new vehicles present based on the previous frame.
                """

                if self.show_log:
                    log(0, f"Update {vehicle.name} with min_distance {min_distance} with {coordinates}")

                vehicle = self.update_parameters_vehicle(vehicle, coordinates, min_distance)

                self.current_vehicles.append(vehicle)
                self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)
                self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)

        return vehicle

    def add_new_vehicles(self, coordinates):
        """
        Adds new vehicles when not present at the previous frame.

        :param coordinates:  coordinates of the next bounding box (vehicle).

        :return vehicle: vehicle to be drawn.
        """
        ret = self.check_repaint_vehicles(coordinates)

        if not ret:
            # New vehicle added to the scene
            self.create_new_vehicle(coordinates)

    def add_vehicles_stationary(self, vehicle, min_distance, coordinates):
        """
        Added a stationary vehicle in list.

        :param vehicle: vehicle to add.
        :param min_distance: minimum distance.
        :param coordinates: coordinates of the vehicle.
        """

        # Temporary list to modify it a run time.
        tmp_vehicles_stationary = self.vehicles_stationary.copy()

        for index, stat_vehicle in enumerate(self.vehicles_stationary):

            if stat_vehicle.name == vehicle.name:
                # Search for vehicles in the list of stationary vehicles.
                num_stat = stat_vehicle.num_frame_to_remove_vehicle - 1

                if num_stat != 0:
                    # The vehicle is still shown
                    stat_vehicle.decrease_iterations_stationary()

                    stat_vehicle = self.update_parameters_vehicle(stat_vehicle, coordinates, min_distance)

                    self.current_vehicles.append(stat_vehicle)
                    self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, stat_vehicle.name)

                elif num_stat == 0:
                    # Deletes vehicle in the list of stationary vehicles. No tracking.
                    stat_vehicle.unmarked_as_stationary(self.num_iterations_stationary)
                    self.table.delete_row(stat_vehicle.name)

                    self.deleted_vehicles, _ = Utility.delete_all_items_in_list(self.deleted_vehicles,
                                                                                stat_vehicle.name)
                    self.prev_vehicles, _ = Utility.delete_all_items_in_list(self.prev_vehicles, stat_vehicle.name)

                    del tmp_vehicles_stationary[index]
                break

            if index + 1 == len(self.vehicles_stationary):
                # Vehicle wasn't on vehicles_stationary list.
                vehicle = self.update_parameters_vehicle(vehicle, coordinates, min_distance)

                tmp_vehicles_stationary.append(vehicle)
                self.current_vehicles.append(vehicle)
                self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

        # Updates stationary list.
        self.vehicles_stationary = tmp_vehicles_stationary.copy()

        if len(self.vehicles_stationary) == 0:
            # The list of the stationary vehicles is empty.

            vehicle = self.update_parameters_vehicle(vehicle, coordinates, min_distance)

            self.vehicles_stationary.append(vehicle)
            self.current_vehicles.append(vehicle)
            self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

    def update_parameters_vehicle(self, vehicle, coordinates, min_distance):
        """
        Update parameter of the vehicle.

        :param vehicle: vehicle.
        :param coordinates: new coordinates of the vehicle.
        :param min_distance: minimum distance of the vehicle.

        :return: vehicle object with the informations updated.
        """

        # Update coordinates
        vehicle.set_coordinates(Utility.get_coordinates_bb(points=coordinates))

        # Update direction
        direction = Utility.get_direction(coordinates, self.angle, self.magnitude)
        vehicle.set_direction(direction)
        self.table.update_table(vehicle.name, COLUMN_DIRECTION, vehicle.get_direction())

        # Update intensity
        intensity = Utility.get_intensity(self.mask_hsv, coordinates)
        vehicle.set_intensity(intensity)

        # Update velocity
        velocity = Utility.get_velocity(distance=min_distance, fps=self.fps)
        vehicle.set_velocity(velocity)
        self.table.update_table(vehicle.name, COLUMN_VELOCITY, f"{vehicle.velocity} km/h")

        if min_distance < self.dist_for_stationary:
            vehicle.marked_as_stationary()
        else:
            vehicle.unmarked_as_stationary(self.num_iterations_stationary)

            # Remove the vehicle if it was previously stationary
            self.vehicles_stationary, _ = Utility.delete_item_in_list(self.vehicles_stationary, vehicle.name)

        self.table.update_table(vehicle.name, COLUMN_STATIONARY, vehicle.is_stationary)

        return vehicle

    def check_repaint_vehicles(self, coordinates):
        """
        Check if there are vehicles to be redesigned.

        :param coordinates: coordinates of the last position of the vehicle.

        :return bool, true if the vehicle need to be redesigned, false otherwise.
        """
        repaint_vehicle = False
        max_distance = 50
        min_distance, result = self.get_distance(coordinates, self.deleted_vehicles, max_distance=max_distance)

        if min_distance < max_distance and result is not None:

            # Check if the vehicle is already to be drawn
            for vehicle_to_draw in self.vehicles_to_draw:
                if result.name == vehicle_to_draw.name:
                    repaint_vehicle = True
                    break

            if not repaint_vehicle:
                repaint_vehicle = True

                if min_distance < self.dist_for_stationary:
                    # Stationary vehicle
                    self.add_vehicles_stationary(result, min_distance, coordinates)

                else:
                    # Vehicle in motion
                    result = self.update_parameters_vehicle(result, coordinates, min_distance)

                    # Update lists
                    self.current_vehicles.append(result)
                    self.prev_vehicles, _ = Utility.delete_item_in_list(self.prev_vehicles, result.name)
                    self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, result)
            else:
                repaint_vehicle = False

        return repaint_vehicle

    def check_vehicle_by_colors(self, coordinates):
        """
        Check if two vehicles is the same vehicle by colors intensity.

        :param coordinates: coordinates of one of the two vehicles.

        :return vehicle object with coordinates updated.
        """
        centroid = Utility.get_centroid(coordinates)
        intensity_to_compare = Utility.get_intensity(self.mask_hsv, coordinates)

        result = None
        intensity_range = 150

        for vehicle in self.current_vehicles:

            distance = Utility.get_length(vehicle.centroid, centroid)
            if distance <= 30:

                intensity = vehicle.average_intensity

                if not intensity_to_compare - intensity_range <= intensity <= intensity_to_compare + intensity_range:
                    continue

                (x_start_1, y_start_1), _, _, (x_end_1, y_end_1) = vehicle.coordinates
                (x_start_2, y_start_2), (x_end_2, y_end_2) = coordinates

                if x_start_1 < x_start_2:
                    vehicle.set_coordinates(
                        Utility.get_coordinates_bb(points=((x_start_1, y_start_1), (x_end_2, y_end_2))))
                else:
                    vehicle.set_coordinates(
                        Utility.get_coordinates_bb(points=((x_start_2, y_start_2), (x_end_1, y_end_1))))

                self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)
                result = vehicle
                break

        return result
