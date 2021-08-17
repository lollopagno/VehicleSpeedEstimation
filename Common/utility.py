import math

import cv2 as cv
import numpy as np
from colorama import Style, Fore
from Common.url import CITIES

import Common.color as Color


def log(info, msg):
    r"""
    Print message based on info.

    :param info: type of message.
    :param msg: msg to show.

    Info:
    - 0: information.
    - 1: Errors.
    - 2: Actions table.
    - 3: Drawing.
    """
    if info == 0:
        print(Fore.YELLOW + f"[INFO] {msg}")
    elif info == 1:
        print(Fore.RED + f"[ERROR] {msg}")
    elif info == 2:
        print(Fore.BLUE + f"[TABLE] {msg}")
    elif info == 3:
        print(Fore.GREEN + f"[DRAWING] {msg}")

    print(Style.RESET_ALL)


def set_text(img, text, pos, font=cv.FONT_HERSHEY_PLAIN, dim: float = 2, color=Color.MAGENTA, thickness=2):
    r"""
    Draw text into image.

    :param img: image.
    :param text: text to draw.
    :param pos: position into image.
    :param font: text font.
    :param dim: text dimension.
    :param color: text color.
    :param thickness: text thickness.
    """
    cv.putText(img, text, pos, font, dim, color, thickness)


def get_length(point_1, point_2):
    r"""
    Calculate the length between two points.

    :param point_1: point 1.
    :param point_2: point 2.
    """
    return math.sqrt(math.pow(point_2[0] - point_1[0], 2) + math.pow((point_2[1] - point_1[1]), 2))


def get_random_color():
    r"""
    Create a random color rgb.
    """
    color = tuple(np.random.choice(range(256), size=3))
    return tuple((int(color[0]), int(color[1]), int(color[2])))


def get_area(contour, min_area=70):
    r"""
    Get the area of a specific contour.

    :param contour: contour.
    :param min_area: minimum area value.

    :return: True if the contour is to be discarded, false otherwise.
    """

    area = cv.contourArea(contour)
    peri = cv.arcLength(contour, True)
    approx = cv.approxPolyDP(contour, 0.04 * peri, True)
    return min_area >= area or len(approx) < 4


def get_polygon(city):
    """
    Get polygon based on specific city.

    :param city: city object.
    """

    polygon = []

    for _city in CITIES:
        if city["Name"] == _city:

            for _polygon in city["Polygon"]:
                polygon.append(_polygon)

    return polygon


def check_polygon(img, polygons, coordinates):
    """
    Check if the coordinates are inside the polygon.

    :param polygons: polygons of the city.
    :param coordinates: coordinates to check.

    return: bool, True if the coordinates are out the polygon, false otherwise.
    """
    is_out = True

    if len(polygons) > 0:
        centroid = get_centroid(coordinates)
        point = (int(centroid[0]), int(centroid[1]))

    for polygon in polygons:
        is_inside = cv.pointPolygonTest(polygon, point, False)

        if is_inside >= 0:
            is_out = False
            break

    if is_out:
        # Todo: delete in the future
        try:
            cv.circle(img, point, 35, (0, 0, 255), thickness=10)
        except:
            pass

    return is_out


def draw_vehicles(vehicles, img):
    r"""
    Draw the bounding box of a vehicle.

    :param img: img to draw in.
    :param vehicles: vehicles to draw.
    """

    height, width, _ = img.shape

    for vehicle in vehicles:
        log(3, vehicle.name)

        thick = int((height + width) // 900)

        start, end = vehicle.coordinates[0], vehicle.coordinates[3]
        name = vehicle.name
        color = vehicle.color

        cv.rectangle(img, start, end, color, thick + 3)
        cv.circle(img, vehicle.centroid, 2, Color.RED, thick + 3)

        x, y = start

        # Split text and number
        num = [str(i) for i in name.split() if i.isdigit()]
        name = name.replace(num[0], "")
        set_text(img, name, (x, y - 12), color=color, thickness=thick, dim=1.5)
        set_text(img, num[0], (x + 90, y - 12), color=color, thickness=thick + 1, dim=1.5)


def get_coordinates_bb(points):
    """
    Get all cordinates of the bouding box.

    :param points: start point and end point of the bouding box.

    point_1: (x_start, y_start)
    point_2: (x_end, y_start)
    point_3: (x_start, y_end)
    point_4: (x_end, y_end)

    :return: array with four coordinates of the bouding box.
    """

    (x_start, y_start), (x_end, y_end) = points

    point_2 = (x_end, y_start)
    point_3 = (x_start, y_end)

    return [(x_start, y_start), point_2, point_3, (x_end, y_end)]


def get_centroid(coordinates):
    r"""
    Get centroid of the bounding box.

    :param coordinates: coordinates of the bounding box.
    :return: coordinates of the centroid.
    """
    return np.mean(coordinates, axis=0, dtype=np.int)


def get_velocity(distance, fps):
    r"""
    ....
    """
    # Conversion factors
    ms2kmh = 3.6
    px2m = 0.075

    return distance * ms2kmh * fps * px2m


def check_exit_to_the_scene(img, coordinates, max_value=10):
    r"""
    The functions checks if the vehicle leave to the scene.

    :param img: shape of image.
    :param coordinates: coordinates of the vehicle.
    :param max_value: maximum value to consider a vehicle out of the scene.

    :return: True if the vehicle is out of the scene, otherwise False.
    """

    (x_start, y_start), (x_end, y_end) = coordinates[0], coordinates[3]
    height, width, _ = img.shape

    if (x_start <= max_value and x_end <= max_value) or (x_start >= width - max_value and x_end >= width - max_value):
        # Check x-coordinate
        return True
    elif (y_start <= max_value and y_end <= max_value) or (
            y_start >= height - max_value and y_end >= height - max_value):
        # Check y-coordinate
        return True
    else:
        return False


def delete_item_in_list(list, name):
    r"""
    Delete vehicle by name in list.

    :param list: list of vehicles.
    :param name: name of vehicle to be deleted.

    :return: list updated.
    """

    for index, vehicle in enumerate(list):
        if vehicle.name == name:
            del list[index]
            break

    return list


def check_vehicle_in_list(list, vehicle_to_search):
    r"""
    Check if name is present in list. If present, deletes this name in the list and reinsertes it.

    :param list: list to search name.
    :param vehicle_to_search: vehicle to search.
    """

    for index, vehicle in enumerate(list):
        if vehicle.name == vehicle_to_search.name:
            del list[index]
            break

    list.append(vehicle_to_search)
    return list


def stack_images(scale, imgArray):
    r"""
    Stack the images based on the number of them by rows and columns.
    Resize the images.
    :param scale: scale factor
    :param imgArray: array of images
    :return: array of images to show
    """

    rows = len(imgArray)
    cols = len(imgArray[0])

    rowsAvailable = isinstance(imgArray[0], list)

    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]

    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):

                if imgArray[x][y].shape[:2] == imgArray[0][0].shape[:2]:
                    imgArray[x][y] = cv.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]),
                                               None, scale, scale)

                if len(imgArray[x][y].shape) == 2:
                    imgArray[x][y] = cv.cvtColor(imgArray[x][y], cv.COLOR_GRAY2BGR)

        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank] * rows

        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)

    else:
        for x in range(0, rows):

            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None, scale, scale)

            if len(imgArray[x].shape) == 2:
                imgArray[x] = cv.cvtColor(imgArray[x], cv.COLOR_GRAY2BGR)

        hor = np.hstack(imgArray)
        ver = hor

    return ver
