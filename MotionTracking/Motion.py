import cv2 as cv

import Common.color as Color
import Common.utility as Utility
from Common.utility import log
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


def morphological_operations(mask):
    r"""
    Performs morphological operations on the mask.

    :param mask: mask of img.
    :return contours: contours detect by mask.
    """

    mask_gray = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)
    _, mask_bin = cv.threshold(mask_gray, 20, 255, cv.THRESH_BINARY)

    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
    mask_erode = cv.erode(mask_bin, kernel, iterations=15)
    mask_dilate = cv.dilate(mask_erode, kernel, iterations=4)

    contours, _ = cv.findContours(mask_dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    mask_binary = cv.resize(mask_dilate, (400, 400))
    mask_binary = cv.cvtColor(mask_binary, cv.COLOR_GRAY2RGB)
    Utility.set_text(mask_binary, str(len(contours)), (320, 380), color=Color.RED, thickness=3)
    cv.imshow("Binary mask", mask_binary)
    cv.waitKey(1)

    return contours


def get_distance(new_coordinates, list, max_distance, default_distance=20):
    r"""
    Calculates the distance among all vehicles detected.

    :param new_coordinates: coordinates of the next bounding box (vehicle)
    :param list: list of vehicles to loop.
    :param max_distance: maximum allowable distance in the search for the vehicle.
    :param default_distance: default value minimum distance.

    :return min_distance: smaller distance located relative to new_coordinates.
    :return current_item: information of the vehicle extracted on the basis of new_coordinates.
    """

    start, end = new_coordinates
    new_barycenter = Utility.get_barycenter(end)

    min_distance = default_distance
    result = None

    for box in list:

        _start, _end = box.coordinates
        _barycenter = Utility.get_barycenter(_end)

        distance = Utility.get_length(new_barycenter, _barycenter)

        if max_distance > distance >= 0:

            if min_distance == default_distance or distance <= min_distance:
                # Update variables
                min_distance = distance
                result = box
                log(0, f"Update bounding box for {box.name}, [Distance]: {min_distance}")

    return min_distance, result


class Motion:
    r"""
    Class to detect moving vehicles.
    """

    def __init__(self, table):
        r"""
        Costructor of class Motion.
        :param table object table.
        """
        self.counter_vehicle = 0
        self.iteration = 0
        self.fps = 0
        self.table = table

        # Vehicle list
        self.prev_vehicles = []
        self.current_vehicles = []
        self.deleted_vehicles = []
        self.vehicles_stationary = {}

        # Maximum num frame before deleting the vehicle history
        self.num_frame_to_remove_vehicle_history = 10

    def detect_vehicle(self, img, mask, iter, fps):
        r"""
        Detect vehicle into img.
        :param img: img.
        :param mask: mask of img.
        :param iter: current iteration.
        :param fps: current frame per second.
        """

        self.iteration = iter
        self.fps = fps

        rows_to_add_to_table = []

        contours = morphological_operations(mask)

        if len(self.prev_vehicles) == 0:
            log(0, "NO vehicles (if)")
            r"""
            Added new vehicles only to the first iteration or 
            when the scene is devoid of vehicles.
            """

            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)

                if Utility.get_area(cnt):
                    # log(0, f"Counter deleted [{area}]! (if motion)")
                    continue

                ret, v = self.check_repaint_vehicles(((x, y), (x + w, y + h)), "Repaint wihout vehicles")

                if not ret:
                    name = f"Vehicle {self.counter_vehicle + 1}"
                    coordinates = ((x, y), (x + w, y + h))

                    v = Vehicle(name, coordinates)
                    log(0, f"Added the new {v.name}")

                    self.current_vehicles.append(v)
                    self.counter_vehicle += 1

                Utility.draw_vehicles([v], img)
                rows_to_add_to_table.append(v)

        else:
            log(0, "YES vehicles (else)")
            r"""
            Added new vehicles when present at the previous frame.
            """

            vehicles_to_draw = []

            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)

                if Utility.get_area(cnt):
                    # log(0, f"Counter deleted! [{area}] (else motion)")
                    continue

                # Added new vehicles.
                rows_to_add_to_table, draw = self.add_new_vehicles(new_coordinates=((x, y), (x + w, y + h)),
                                                                   img=img)

                if draw is not None:
                    vehicles_to_draw = Utility.check_vehicle_in_list(vehicles_to_draw, draw.name)
                    vehicles_to_draw.append(draw)

            Utility.draw_vehicles(vehicles_to_draw, img)

            for vehicle in self.prev_vehicles:
                self.table.delete_row(vehicle.name)

                vehicle.set_iteration(self.iteration)
                self.deleted_vehicles.append(vehicle)

                try:
                    del self.vehicles_stationary[vehicle.name]
                except KeyError:
                    pass

        self.prev_vehicles = self.current_vehicles.copy()
        self.current_vehicles.clear()
        self.table.add_rows(rows_to_add_to_table)

        # Delete vehicles in list after 3 iterations
        tmp_list = []
        for del_vehicle in self.deleted_vehicles:
            iter = del_vehicle.iteration

            if not iter == self.iteration - self.num_frame_to_remove_vehicle_history:
                tmp_list.append(del_vehicle)

        self.deleted_vehicles = tmp_list.copy()

    def add_new_vehicles(self, new_coordinates, img, max_distance=15):
        r"""
        Added new vehicles based on the minimum distance between all bounding boxes.

        :param new_coordinates: coordinates of the next bounding box (vehicle).
        :param img: img to draw in.
        :param max_distance: maximum distance in pixel allowed.
        """

        rows_to_add = []
        min_distance, vehicle = get_distance(new_coordinates,
                                             self.prev_vehicles,
                                             max_distance=max_distance)

        if vehicle is not None:

            if Utility.check_exit_to_the_scene(img, vehicle.coordinates):
                r"""
                Check if the vehicles no longer present (out of the scene).
                """
                log(0, f"Remove {vehicle.name} (not displayed)")

            elif min_distance == 0:
                r"""
                Detects if there are stationary vehicles.
                """

                # Temporary list to modify it a run time.
                tmp_vehicles_stationary = self.vehicles_stationary

                for index, stat_vehicle in enumerate(self.vehicles_stationary.items()):

                    if stat_vehicle.name == vehicle.name:
                        # Found vehicle on vehicles_stationary list.
                        num_stat = stat_vehicle.num_frame_to_remove_vehicle - 1

                        if num_stat != 0:
                            # The vehicle is still shown
                            stat_vehicle.decrease_frame_stationary()

                            self.current_vehicles.append(stat_vehicle)
                            self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                        elif num_stat == 0:
                            # Delete vehicle in stationary list. No tracking.
                            stat_vehicle.unmarked_as_stationary()
                            del tmp_vehicles_stationary[stat_vehicle.name]
                        break

                    if index + 1 == len(tmp_vehicles_stationary):
                        # Vehicle wasn't on vehicles_stationary list.
                        stat_vehicle.marked_as_stationary()

                        self.current_vehicles.append(stat_vehicle)
                        self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                if len(self.vehicles_stationary) == 0:
                    log(0, f"Added new {vehicle.name} as stationary vehicle.")
                    vehicle.marked_as_stationary()

                    self.current_vehicles.append(vehicle)
                    self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                self.vehicles_stationary = tmp_vehicles_stationary

            elif min_distance < max_distance:
                r"""
                Added new vehicles when present at the previous frame.
                """

                # Update list vehicles with the next bounding box (vehicle) specification.
                for index, box in enumerate(self.prev_vehicles):

                    if vehicle.name == box.name:
                        # Update vehicle to the scene
                        log(0, f"Update {box.name} with min_distance {min_distance}")

                        box.set_coordinates(new_coordinates)
                        velocity = (Utility.get_velocity(distance=min_distance,
                                                         fps=self.fps))

                        self.table.update_velocity(box.name, velocity)
                        box.set_velocity(velocity)

                        self.current_vehicles.append(box)
                        self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, box.name)
                        rows_to_add.append(box)

                        # Remove the vehicle if it was previously stationary
                        try:
                            del self.vehicles_stationary[box.name]
                        except KeyError:
                            pass
                        break
        else:
            r"""
            Added new vehicles when not present at the previous frame.
            """
            ret, result = self.check_repaint_vehicles(new_coordinates, "Repaint in add_vehicles ")

            if not ret:
                # New vehicle added to the scene
                name = f"Vehicle {self.counter_vehicle + 1}"
                log(0, f"Added the new {name}")

                # Update vehicles list
                v = Vehicle(name, new_coordinates)
                self.current_vehicles.append(v)

                rows_to_add.append(v)
                self.counter_vehicle += 1

            else:
                result.set_iteration(self.prev_vehicles)
                self.deleted_vehicles.append(result)

            vehicle = result

        return rows_to_add, vehicle

    def check_repaint_vehicles(self, coordinates, _log):
        r""""
        Check if there are vehicles to be redesigned.

        :param coordinates: coordinates of the last position of the vehicle.

        :return True if the vehicle need to be redesigned, false otherwise.
        """
        max_distance = 100
        min_distance, result = get_distance(coordinates, self.deleted_vehicles, max_distance=max_distance)

        if min_distance < max_distance and result is not None:
            log(3, f"{_log} {result.name}")
            self.current_vehicles.append(result)
            return True, result

        return False, None
