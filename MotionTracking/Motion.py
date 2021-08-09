import cv2 as cv

import Common.color as Color
import Common.utility as Utility


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


class Motion:
    r"""
    Class to detect moving vehicles.
    """

    def __init__(self, table):
        r"""
        Costructor of class Motion.
        :param table object table.
        """
        self.counter = 0
        self.table = table
        self.prev_vehicles = []
        self.current_vehicles = []
        self.vehicles_stationary = {}

        # Constant
        self.max_area = 900
        self.num_frame_to_remove_vehicle = 3

    def detect_vehicle(self, img, mask):
        r"""
        Detect vehicle into img.
        :param img: img.
        :param mask: mask of img.
        """

        img_gray = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)
        _, img_bin = cv.threshold(img_gray, 20, 255, cv.THRESH_BINARY)

        kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        img_erode = cv.erode(img_bin, kernel, iterations=8)
        img_dilate = cv.dilate(img_erode, kernel, iterations=12)

        contours, _ = cv.findContours(img_dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

        mask_binary = cv.resize(img_dilate, (400, 400))
        mask_binary = cv.cvtColor(mask_binary, cv.COLOR_GRAY2RGB)
        Utility.set_text(mask_binary, str(len(contours)), (320, 380), color=Color.RED, thickness=3)
        cv.imshow("Binary mask", mask_binary)
        cv.waitKey(1)

        if len(self.prev_vehicles) == 0:
            r"""
            Added new vehicles only to the first iteration or 
            when the scene is devoid of vehicles.
            """

            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)
                area = cv.contourArea(cnt)

                if area <= self.max_area:
                    # Utility.log(0, f"Counter deleted [{area}]! (if motion)")
                    continue

                color = Utility.get_random_color()

                name = f"Vehicle {self.counter + 1}"
                coordinates = ((x, y), (x + w, y + h))
                velocity = 0

                item = [name, coordinates, color, velocity]
                Utility.log(0, f"Added the new vehicle: {name}")

                self.current_vehicles.append(item)
                self.table.add_row(item)
                Utility.draw_vehicle([item], img)

                self.counter += 1
        else:
            r"""
            Added new vehicles when present at the previous frame.
            """

            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)
                area = cv.contourArea(cnt)

                if area <= self.max_area:
                    # Utility.log(0, f"Counter deleted! [{area}] (else motion)")
                    continue

                new_coordinates = ((x, y), (x + w, y + h))

                # Added new vehicles.
                self.add_new_vehicles(new_coordinates=new_coordinates, img=img)

        self.prev_vehicles = self.current_vehicles.copy()
        self.current_vehicles = []

    def add_new_vehicles(self, new_coordinates, img, max_distance=15):
        r"""
        Added new vehicles based on the minimum distance between all bounding boxes.

        :param new_coordinates: coordinates of the next bounding box (vehicle).
        :param img: img to draw in.
        :param max_distance: maximum distance in pixel allowed.
        """

        vehicles_to_draw = []
        min_distance, current_item = self.get_distance(new_coordinates,
                                                       max_distance=max_distance)

        # Vehicle information
        name, coordinates, color, velocity = current_item

        if Utility.check_exit_to_the_scene(img, coordinates):
            r"""
            Check if the vehicles no longer present (out of the scene).
            """

            Utility.log(0, f"Remove vehicle: {name} (not displayed)")
            # self.table.delete_row(name)

        elif min_distance == 0:
            r"""
            Detects if there are stationary vehicles.
            """

            # Temporary dict to modify it a run time.
            tmp_vehicles_stationary = self.vehicles_stationary

            for index, vehicle in enumerate(self.vehicles_stationary.items()):
                name_stat = vehicle[0]

                if name_stat == name:
                    # Found vehicle on vehicles_stationary list.
                    num_stat = vehicle[1] - 1

                    if num_stat != 0:
                        # The vehicle is still shown
                        tmp_vehicles_stationary[name_stat] = num_stat
                        vehicles_to_draw.append(current_item)
                        self.current_vehicles.append(current_item)

                    elif num_stat == 0:
                        # Delete vehicle in stationary list. No tracking.
                        del tmp_vehicles_stationary[name_stat]
                        break

                if index + 1 == len(tmp_vehicles_stationary):
                    # Vehicle wasn't on vehicles_stationary list.
                    tmp_vehicles_stationary[name_stat] = self.num_frame_to_remove_vehicle
                    vehicles_to_draw.append(current_item)
                    self.current_vehicles.append(current_item)

            if len(self.vehicles_stationary) == 0:
                tmp_vehicles_stationary[name] = self.num_frame_to_remove_vehicle
                vehicles_to_draw.append(current_item)
                self.current_vehicles.append(current_item)

            self.vehicles_stationary = tmp_vehicles_stationary

        elif min_distance < max_distance:  # TODO prima la condizione era min_distance != 0 (per ripristino versione)
            r"""
            Added new vehicles when present at the previous frame.
            """

            # Update list vehicles with the next bounding box (vehicle) specification.
            for index, box in enumerate(self.prev_vehicles):

                if name in box:
                    # Update vehicle to the scene
                    Utility.log(0, f"Update vehicle: {name} with min_distance {min_distance}")
                    new_item = [name, new_coordinates, color, velocity]
                    self.current_vehicles.append(new_item)
                    vehicles_to_draw.append(current_item)

                    # Remove old item vehicle into list
                    del self.prev_vehicles[index]

                    # Remove the vehicle if it was previously stationary
                    for vehicle in self.vehicles_stationary.items():
                        name_stat = vehicle[0]

                        if name_stat == name:
                            del self.vehicles_stationary[name_stat]
                            break

                    break
        else:
            r"""
            Added new vehicles when not present at the previous frame.
            """

            # New vehicle added to the scene
            name = f"Vehicle {self.counter + 1}"
            Utility.log(0, f"Added the new vehicle: {name}")
            velocity = 0
            color = Utility.get_random_color()

            # Update vehicles list
            item = [name, new_coordinates, color, velocity]
            self.current_vehicles.append(item)
            vehicles_to_draw.append(current_item)

            # Update table
            self.table.add_row(item)

            self.counter += 1

        Utility.draw_vehicle(vehicles_to_draw, img)

    def get_distance(self, new_coordinates, max_distance, default_distance=20):
        r"""
        Calculates the distance among all vehicles detected.

        :param new_coordinates: coordinates of the next bounding box (vehicle)
        :param max_distance: maximum allowable distance in the search for the vehicle.
        :param default_distance: default value minimum distance.

        :return min_distance: smaller distance located relative to new_coordinates.
        :return current_item: information of the vehicle extracted on the basis of new_coordinates.
        """

        start, end = new_coordinates
        new_barycenter = Utility.get_barycenter(end)

        min_distance = default_distance
        current_item = []

        for box in self.prev_vehicles:
            name, coordinates, color, velocity = box

            _start, _end = coordinates
            _barycenter = Utility.get_barycenter(_end)

            distance = Utility.get_length(new_barycenter, _barycenter)

            if max_distance > distance >= 0:  # TODO prima la condizione era MAX_DISTANCE > distance > 0 (per ripristino versione)

                if min_distance == default_distance or distance <= min_distance:  # TODO prima la condizione era min_distance == 0 or distance < min_distance (per ripristino versione)
                    min_distance = distance
                    current_item = [name, coordinates, color, velocity]
                    Utility.log(0, f"Update bb for vehicle {name}")

            else:
                Utility.log(0,
                            f"No match [Distance] : {distance}, between cordinates [{_barycenter}] and [{new_barycenter}]")

        return min_distance, current_item
