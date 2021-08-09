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
        self.vehicles = []
        self.new_list_vehicles = []

        self.max_area = 900

    def detect_vehicle(self, img, mask):
        r"""
        Detect vehicle into img.
        :param img: img.
        :param mask: mask.
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

        if len(self.vehicles) == 0:
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
                self.new_list_vehicles.append(item)
                self.table.add_row(item)

                Utility.draw_vehicle(img, ((x, y), (x + w, y + h)), name, color)
                self.counter += 1
        else:
            for num, cnt in enumerate(contours):
                (x, y, w, h) = cv.boundingRect(cnt)
                area = cv.contourArea(cnt)

                if area <= self.max_area:
                    # Utility.log(0, f"Counter deleted! [{area}] (else motion)")
                    continue

                new_coordinates = ((x, y), (x + w, y + h))
                self.get_distance_bounding_box(new_coordinates=new_coordinates, img=img)

            if len(self.vehicles) > 0:
                # Vehicles for which no match was found with previous frames

                for vehicle in self.vehicles:
                    name, coordinates, color, velocity = vehicle

                    if Utility.check_exit_to_the_scene(img_gray, coordinates):
                        # Remove vehicles no longer present if they leave the scene
                        Utility.log(0, f"Remove vehicle: {name} (not displayed)")
                        self.table.delete_row(name)

                    else:
                        # Stationary vehicle
                        Utility.log(0, f"Vehicle {name} is stationary!, {coordinates}")
                        Utility.draw_vehicle(img, coordinates, name, color)

                        item = [name, coordinates, color, velocity]
                        self.new_list_vehicles.append(item)

        self.vehicles = self.new_list_vehicles.copy()
        self.new_list_vehicles =  []

    def get_distance_bounding_box(self, new_coordinates, img):
        r"""
        Get the minimum distance between all bounding boxes.

        :param new_coordinates: coordinates of the next bounding box.
        :param img: img to draw in.
        """

        MAX_DISTANCE = 15  # Distance in pixel
        _DEFAULT = 20  # Default value minimum distance

        start, end = new_coordinates
        new_barycenter = Utility.get_barycenter(end)

        min_distance = _DEFAULT
        current_item = []

        for box in self.vehicles:
            _name, _coordinates, _color, _velocity = box

            _start, _end = _coordinates
            _barycenter = Utility.get_barycenter(_end)

            distance = Utility.calc_distance(new_barycenter, _barycenter)

            if MAX_DISTANCE > distance >= 0:  # TODO prima la condizione era MAX_DISTANCE > distance > 0 (per ripristino versione)

                if min_distance == _DEFAULT or distance <= min_distance:  # TODO prima la condizione era min_distance == 0 or distance < min_distance (per ripristino versione)
                    min_distance = distance
                    current_item = [_name, _coordinates, _color, _velocity]
                    Utility.log(0, f"Update bb for vehicle {_name}")

            else:
                Utility.log(0,
                            f"No match [Distance] : {distance}, between cordinates [{_barycenter}] and [{new_barycenter}]")

        if min_distance < MAX_DISTANCE:  # TODO prima la condizione era min_distance != 0 (per ripristino versione)

            # Update list vehicles with the next bounding box specification
            for index, box in enumerate(self.vehicles):
                current_name, _, _, _ = current_item

                if current_name in box:
                    # Update vehicle to the scene
                    _name, _coordinates, _color, _velocity = current_item
                    Utility.log(0, f"Update vehicle: {_name} with min_distance {min_distance}")
                    new_item = [_name, new_coordinates, _color, _velocity]
                    self.new_list_vehicles.append(new_item)
                    Utility.draw_vehicle(img, new_coordinates, _name, _color)

                    # Remove old item vehicle into list
                    del self.vehicles[index]
                    break
        else:
            # New vehicle added to the scene
            name = f"Vehicle {self.counter + 1}"
            Utility.log(0, f"Added the new vehicle: {name}")
            velocity = 0
            color = Utility.get_random_color()

            # Update vehicles list
            item = [name, new_coordinates, color, velocity]
            self.new_list_vehicles.append(item)
            Utility.draw_vehicle(img, new_coordinates, name, color)

            # Update table
            self.table.add_row(item)

            self.counter += 1
