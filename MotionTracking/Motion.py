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


def detect_car(img, mask, vehicles, counter_vehicle, table):
    r"""

    """
    img_gray = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)
    _, thresh = cv.threshold(img_gray, 20, 255, cv.THRESH_BINARY)

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    opening = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel, iterations=4)
    erode = cv.erode(opening, kernel, iterations=4)

    contours, _ = cv.findContours(erode, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    new_list_vehicles = []

    if len(vehicles) == 0:
        for num, cnt in enumerate(contours):
            (x, y, w, h) = cv.boundingRect(cnt)
            area = cv.contourArea(cnt)

            if area <= 500:
                print("Counter deleted! (if motion)")
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

            if area <= 500:
                print("Counter deleted! (else motion)")
                continue

            new_coordinates = ((x, y), (x + w, y + h))
            vehicles, new_list_vehicles, counter_vehicle = Utility.get_distance_bouding_box(
                new_coordinates=new_coordinates,
                boxes=vehicles,
                new_list=new_list_vehicles,
                counter=counter_vehicle,
                table=table,
                img = img)

        if len(vehicles) > 0:
            # Remove vehicles no longer present
            for vehicle in vehicles:
                name, _, _, _ = vehicle
                table.delete_row(name)

    cv.imshow("Binary mask", cv.resize(opening, (400, 400)))
    cv.waitKey(1)

    return new_list_vehicles, counter_vehicle
