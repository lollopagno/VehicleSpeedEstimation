import cv2 as cv
import numpy as np
from colorama import Fore, Style
import time
from ModuleCalibration import ModuleCalibration as MC

NAME_WINDOW = "Calibration"
clicked_image = 0
minimum_image = 30


def callback_mouse(event, x, y, flag, param):
    """ Callback click mouse on the image. """

    global clicked_image, minimum_image, calibration

    if event == cv.EVENT_LBUTTONDOWN:
        frame = calibration.frame
        print(Fore.GREEN + f"Clicked image in position {x, y}")
        print(Style.RESET_ALL)

        success, img = calibration.start(frame)

        if success:
            clicked_image += 1

            cv.putText(img, f"{clicked_image}/{minimum_image}", (530, 460), cv.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            cv.imshow(NAME_WINDOW, img)
            cv.waitKey(1)


def draw_corners_chessboard(frame, criteria, size=(9, 6)):
    """ Draw corners in chess board  """

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    ret, corners = cv.findChessboardCorners(gray, size, None)

    if ret:
        corners_2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        cv.drawChessboardCorners(frame, size, corners_2, ret)


criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((6 * 9, 3), np.float32)
objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

calibration = MC(objp, criteria=criteria)

cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 750)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 512)

cv.namedWindow(NAME_WINDOW)
cv.setMouseCallback(NAME_WINDOW, callback_mouse, calibration)
previous_time = 0

while cap.isOpened():

    ret, frame = cap.read()

    if ret:

        current_time = time.time()
        fps = np.divide(1, (current_time - previous_time))
        previous_time = current_time
        cv.putText(frame, f"FPS: {int(fps)}", (10, 35), cv.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)

        frame_copy = frame.copy()
        calibration.set_frame(frame_copy)
        draw_corners_chessboard(frame, criteria)

        # Iterate through all images
        if clicked_image < minimum_image:

            cv.putText(frame, f"{clicked_image}/{minimum_image}", (530, 460), cv.FONT_HERSHEY_PLAIN, 2,
                       (0, 255, 0), 2)
            cv.imshow(NAME_WINDOW, frame)
            cv.waitKey(1)

        else:
            calibration.calibrate()
            print("Calibration terminated!")
            break
