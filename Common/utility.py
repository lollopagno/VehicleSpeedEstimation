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

    print(Style.RESET_ALL)


def set_text(img, text, pos, font=cv.FONT_HERSHEY_PLAIN, dim=2, color=Color.MAGENTA, thickness=2):
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


def calc_distance(point_1, point_2):
    r"""
    Calculate the distance between two points.

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


def draw_vehicle(img, coordinates, name, color):
    r"""
    Draw the bounding box of a vehicle.
    :param img: img to draw in
    :param coordinates: of the bounding box.
    :param name: name vehicle.
    :param color: color bounding box.
    """
    height, width, _ = img.shape
    thick = int((height + width) // 900)

    start, end = coordinates
    cv.rectangle(img, start, end, color, thick + 3)

    x, y = start
    set_text(img, name, (x, y - 12), color=color, thickness=thick, dim=1.5)


def get_barycenter(point):
    r"""
    Get barycenter of the bounding box.
    :param point: end point (x_max, y_max) of the bounding box.
    :return: coordinates of the barycenter.
    """
    return tuple(map(lambda point: round(point / 2), point))


def get_distance_bounding_box(boxes, new_coordinates, new_list, counter, table, img):
    r"""
    Get the minimum distance between all bounding boxes
    :param boxes: list of the bounding boxes.
    :param new_coordinates: coordinates of the next bounding box.
    :param new_list: list that contains the vehicles to the next frame.
    :param counter: number of total vehicles.
    :param table: object to update the table.
    :param img: img to draw in.
    """

    MAX_DISTANCE = 15  # Distance in pixel

    start, end = new_coordinates
    new_barycenter = get_barycenter(end)

    min_distance = 0
    current_item = []

    for box in boxes:
        _name, _coordinates, _color, _velocity = box

        _start, _end = _coordinates
        _barycenter = get_barycenter(_end)

        distance = calc_distance(new_barycenter, _barycenter)

        if MAX_DISTANCE > distance > 0:
            if min_distance == 0 or distance < min_distance:
                min_distance = distance
                current_item = [_name, _coordinates, _color, _velocity]

    if min_distance != 0:
        # Update list vehicles with the next bounding box specification
        for index, box in enumerate(boxes):
            current_name, _, _, _ = current_item

            if current_name in box:
                # Update vehicle to the scene
                _name, _coordinates, _color, _velocity = current_item
                log(0, f"Update vehicle: {_name}")
                new_item = [_name, new_coordinates, _color, _velocity]
                new_list.append(new_item)
                draw_vehicle(img, new_coordinates, _name, _color)

                # Remove old item vehicle into list
                log(0, f"Remove vehicle in list: {_name}")
                del boxes[index]
                break
    else:
        # New vehicle added to the scene
        name = f"Vehicle {counter}"
        log(0, f"Added the new vehicle: {name}")
        velocity = 0
        color = get_random_color()

        # Update vehicles list
        item = [name, new_coordinates, color, velocity]
        new_list.append(item)
        draw_vehicle(img, new_coordinates, name, color)

        # Update table
        table.add_row(item)

        counter += 1

    return boxes, new_list, counter
