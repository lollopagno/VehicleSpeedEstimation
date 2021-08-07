import cv2 as cv

import Common.color as Color
import Common.utility as Utility

VALUE_AREA = 400


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


def detect_vehicle(img, mask, vehicles, counter_vehicle, table):
    r"""
    Detect vehicle into img.
    :param img: img .
    :param mask: mask.
    :param vehicles: list of vehicles.
    :param counter_vehicle: number of vehicles.
    :param table object table.
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

    new_list_vehicles = []

    if len(vehicles) == 0:
        for num, cnt in enumerate(contours):
            (x, y, w, h) = cv.boundingRect(cnt)
            area = cv.contourArea(cnt)

            if area <= VALUE_AREA:
                Utility.log(0, f"Counter deleted [{area}]! (if motion)")
                continue

            color = Utility.get_random_color()

            name = f"Vehicle {counter_vehicle + 1}"
            coordinates = ((x, y), (x + w, y + h))
            velocity = 0

            item = [name, coordinates, color, velocity]
            new_list_vehicles.append(item)
            table.add_row(item)

            Utility.draw_vehicle(img, ((x, y), (x + w, y + h)), name, color)
            counter_vehicle += 1
    else:
        for num, cnt in enumerate(contours):
            (x, y, w, h) = cv.boundingRect(cnt)
            area = cv.contourArea(cnt)

            if area <= VALUE_AREA:
                Utility.log(0, f"Counter deleted! [{area}] (else motion)")
                continue

            new_coordinates = ((x, y), (x + w, y + h))
            vehicles, new_list_vehicles, counter_vehicle = Utility.get_distance_bounding_box(
                new_coordinates=new_coordinates,
                boxes=vehicles,
                new_list=new_list_vehicles,
                counter=counter_vehicle,
                table=table,
                img=img)

        if len(vehicles) > 0:

            for vehicle in vehicles:
                name, coordinates, color, _ = vehicle

                if Utility.check_exit_to_the_scene(img_gray, coordinates):
                    # Remove vehicles no longer present if they leave the scene
                    Utility.log(0, f"Remove vehicle: {name} (not displayed)")
                    table.delete_row(name)
                else:
                    # Stationary vehicle
                    Utility.draw_vehicle(img, coordinates, name, color)

    return new_list_vehicles, counter_vehicle
