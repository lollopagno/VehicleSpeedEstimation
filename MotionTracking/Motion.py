import cv2 as cv

import Common.color as Color
import Common.utility as Utility
from Common.table import COLUMN_VELOCITY
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
    """
    Performs morphological operations on the mask.

    :param mask: mask of img.

    :return contours: contours detect by mask.
    """

    mask_gray = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)
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

    mask = cv.resize(mask, (400, 400))
    stack = Utility.stack_images(1, ([mask_binary, mask]))
    cv.imshow("Masks", stack)
    cv.waitKey(1)

    return contours


def get_distance(new_coordinates, list, max_distance, _log, default_distance=150):
    """
    Calculates the distance among all vehicles detected.

    :param new_coordinates: coordinates of the next bounding box (vehicle)
    :param list: list of vehicles to loop.
    :param max_distance: maximum allowable distance in the search for the vehicle.
    :param default_distance: default value minimum distance.

    :return min_distance: smaller distance located relative to new_coordinates.
    :return result: information of the vehicle extracted on the basis of new_coordinates.
    """

    new_centroid = Utility.get_centroid(new_coordinates)
    dist_already_calculated = []

    min_distance = default_distance
    result = None

    print(f"Search to find minimum distance {_log}")
    for box in list:

        if not box.name in dist_already_calculated:
            print(f"{box.name}:  {box.coordinates}, new_coordinates: {new_coordinates}")
            dist_already_calculated.append(box.name)
            _centroid = box.centroid
            distance = Utility.get_length(new_centroid, _centroid)

            print(f"Min distance [{min_distance}], distance: [{distance}]\n")
            if max_distance > distance >= 0:

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


class Motion:
    """
    Class to detect moving vehicles.
    """

    def __init__(self, table):
        """
        Constructor of class Motion.

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

        self.vehicles_to_draw = []

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

        contours = morphological_operations(mask)

        if len(self.prev_vehicles) == 0:
            log(0, "NO vehicles (if)")
            """
            Adds new vehicles only to the first iteration or 
            when the scene is devoid of vehicles.
            """

            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)

                if Utility.get_area(cnt):
                    continue

                # Checks if the vehicle was already tracked
                ret, v = self.check_repaint_vehicles(((x, y), (x + w, y + h)), "Repaint without vehicles")

                if not ret:
                    # New vehicle added
                    name = f"Vehicle {self.counter_vehicle + 1}"
                    coordinates = Utility.get_coordinates_bb(points=((x, y), (x + w, y + h)))

                    v = Vehicle(name, coordinates)
                    log(0, f"Added the new {v.name} with {(x, y), (x + w, y + h)}")
                    self.current_vehicles.append(v)

                    self.counter_vehicle += 1

                # Updates list to draw vehicles and update table
                Utility.draw_vehicles([v], img)
                self.table.add_rows([v])

        else:
            log(0, "YES vehicles (else)")
            """
            Adds new vehicles previous frame.
            """

            self.vehicles_to_draw.clear()
            rows_to_add_to_table = []
            tmp_new_coordinates = []

            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)

                if Utility.get_area(cnt):
                    continue

                vehicle = self.tracking(new_coordinates=((x, y), (x + w, y + h)), img=img)

                if vehicle is None:
                    tmp_new_coordinates.append([(x, y), (x + w, y + h)])
                else:
                    # Checks if the vehicle was already tracked to update the new coordinates
                    self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)

            for coordinates in tmp_new_coordinates:
                vehicle = self.add_new_vehicles(coordinates)
                rows_to_add_to_table.append(vehicle)

                # Checks if the vehicle was already tracked to update the new coordinates
                self.vehicles_to_draw = Utility.check_vehicle_in_list(self.vehicles_to_draw, vehicle)

            Utility.draw_vehicles(self.vehicles_to_draw, img)
            self.table.add_rows(rows_to_add_to_table)

            for vehicle in self.prev_vehicles:
                # Deletes vehicles to no longer track
                self.table.delete_row(vehicle.name)

                # Add vehicles to history list
                vehicle.set_iteration(self.iteration)
                self.deleted_vehicles.append(vehicle)

                try:
                    # Remove the vehicle if it was previously stationary
                    del self.vehicles_stationary[vehicle.name]
                except KeyError:
                    pass

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

    def tracking(self, new_coordinates, img, max_distance=30):
        """
        Tracking vehicles based on the minimum distance between all bounding boxes.

        :param new_coordinates: coordinates of the next bounding box (vehicle).
        :param img: img to draw in.
        :param max_distance: maximum distance in pixel allowed.

        :return vehicle: if different from None, return vehicle object
        """

        min_distance, vehicle = get_distance(new_coordinates,
                                             self.prev_vehicles,
                                             max_distance=max_distance,
                                             _log="add new_vehicles")

        if vehicle is not None:

            if Utility.check_exit_to_the_scene(img, vehicle.coordinates):
                """
                Checks if the vehicles no longer present (out of the scene).
                """
                log(0, f"Remove {vehicle.name} (not displayed)")

            elif min_distance == 0:
                """
                Detects if there are stationary vehicles.
                """

                # Temporary list to modify it a run time.
                tmp_vehicles_stationary = self.vehicles_stationary

                for index, stat_vehicle in enumerate(self.vehicles_stationary.items()):

                    if stat_vehicle.name == vehicle.name:
                        # Search for vehicles in the list of stationary vehicles.
                        num_stat = stat_vehicle.num_frame_to_remove_vehicle - 1

                        if num_stat != 0:
                            # The vehicle is still shown
                            stat_vehicle.decrease_frame_stationary()

                            self.current_vehicles.append(stat_vehicle)
                            self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                        elif num_stat == 0:
                            # Deletes vehicle in the list of stationary vehicles. No tracking.
                            stat_vehicle.unmarked_as_stationary()
                            del tmp_vehicles_stationary[stat_vehicle.name]
                        break

                    if index + 1 == len(tmp_vehicles_stationary):
                        # Vehicle wasn't on vehicles_stationary list.
                        stat_vehicle.marked_as_stationary()

                        self.current_vehicles.append(stat_vehicle)
                        self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                if len(self.vehicles_stationary) == 0:
                    # The list of the stationary vehicles is empty.
                    log(0, f"Added new {vehicle.name} as stationary vehicle.")
                    vehicle.marked_as_stationary()

                    self.current_vehicles.append(vehicle)
                    self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                # Updates stationary list.
                self.vehicles_stationary = tmp_vehicles_stationary

            elif min_distance < max_distance:
                """
                Adds new vehicles present to the previous frame.
                """

                # Updates the coordinates of the vehicle to the scene
                log(0, f"Update {vehicle.name} with min_distance {min_distance} with {new_coordinates}")

                vehicle.set_coordinates(Utility.get_coordinates_bb(points=new_coordinates))
                velocity = (Utility.get_velocity(distance=min_distance, fps=self.fps))

                vehicle.set_velocity(velocity)
                self.table.update_table(vehicle.name, COLUMN_VELOCITY, f"{vehicle.velocity} km/h")

                self.current_vehicles.append(vehicle)
                self.prev_vehicles = Utility.delete_item_in_list(self.prev_vehicles, vehicle.name)

                try:
                    # Remove the vehicle if it was previously stationary
                    del self.vehicles_stationary[vehicle.name]
                except KeyError:
                    pass

        return vehicle

    def add_new_vehicles(self, new_coordinates):
        """
        Adds new vehicles when not present at the previous frame.

        :param new_coordinates:  coordinates of the next bounding box (vehicle).

        :return vehicle: vehicle to be drawn.
        """
        ret, vehicle = self.check_repaint_vehicles(new_coordinates, "Repaint in add_vehicles ")

        if not ret:
            # New vehicle added to the scene
            name = f"Vehicle {self.counter_vehicle + 1}"
            log(0, f"Added the new {name} with coordinates {new_coordinates}")

            # Update vehicles list
            new_coordinates = Utility.get_coordinates_bb(points=new_coordinates)
            vehicle = Vehicle(name, new_coordinates)

            self.current_vehicles.append(vehicle)
            self.counter_vehicle += 1

        else:
            vehicle.set_iteration(self.prev_vehicles)
            self.deleted_vehicles.append(vehicle)

        return vehicle

    def check_repaint_vehicles(self, coordinates, _log):
        """
        Check if there are vehicles to be redesigned.

        :param coordinates: coordinates of the last position of the vehicle.

        :return True if the vehicle need to be redesigned, false otherwise.
        """
        max_distance = 100
        min_distance, result = get_distance(coordinates, self.deleted_vehicles, max_distance=max_distance,
                                            _log="Repaint")

        if min_distance < max_distance and result is not None:

            # Check if the vehicle is already to be drawn
            flag = False
            for vehicle_to_draw in self.vehicles_to_draw:
                if result.name == vehicle_to_draw.name:
                    flag = True
                    break

            if not flag:
                log(3, f"{_log} {result.name}")

                # Update coordinates
                coordinates = Utility.get_coordinates_bb(points=coordinates)
                result.set_coordinates(coordinates)

                # Update lists
                self.current_vehicles.append(result)
                Utility.delete_item_in_list(self.prev_vehicles, result.name)

                return True, result

        return False, None
