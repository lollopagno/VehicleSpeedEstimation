import math

import cv2 as cv

import common.color as Color


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
