import math

import cv2 as cv
import numpy as np
from colorama import Style, Fore

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
    """
    if info == 0:
        print(Fore.YELLOW + f"[INFO] {msg}")
    elif info == 1:
        print(Fore.RED + f"[ERROR] {msg}")
    elif info == 2:
        print(Fore.BLUE + f"[TABLE] {msg}")
    elif info == 3:
        print(Fore.GREEN + f"[PAINTING] {msg}")

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


def get_area(contour, min_area=50):
    r"""
    Get the area of a specific contour.

    :param contour: contour.
    :param min_area: minimum area value.

    :return: True if the contour is to be discarded, false otherwise.
    """

    area = cv.contourArea(contour)
    peri = cv.arcLength(contour, True)
    approx = cv.approxPolyDP(contour, 0.04 * peri, True)

    return area <= min_area or len(approx) < 4


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

        start, end = vehicle.coordinates
        name = vehicle.name
        color = vehicle.color

        cv.rectangle(img, start, end, color, thick + 3)

        x, y = start

        # Split text and number
        num = [str(i) for i in name.split() if i.isdigit()]
        name = name.replace(num[0], "")
        set_text(img, name, (x, y - 12), color=color, thickness=thick, dim=1.5)
        set_text(img, num[0], (x + 90, y - 12), color=color, thickness=thick + 1, dim=1.5)


def get_barycenter(point):
    r"""
    Get barycenter of the bounding box.

    :param point: end point (x_max, y_max) of the bounding box.
    :return: coordinates of the barycenter.
    """
    return tuple(map(lambda point: round(point / 2), point))


def check_exit_to_the_scene(img, coordinates, max_value=10):
    r"""
    The functions checks if the vehicle leave to the scene.

    :param img: shape of image.
    :param coordinates: coordinates of the vehicle.
    :param max_value: maximum value to consider a vehicle out of the scene.

    :return: True if the vehicle is out of the scene, otherwise False.
    """

    (x_start, y_start), (x_end, y_end) = coordinates
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
    length = len(list)

    for index, vehicle in enumerate(list):
        if vehicle.name == name:
            del list[index]
            break

    if length == len(list):
        raise Exception("No items has been deleted")

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
