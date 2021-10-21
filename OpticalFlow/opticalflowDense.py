import sys
import time

import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication

from Calibration.ModuleCalibration import load_coefficients
from Common import color as Color
from Common.loadVideo import get_video
from MotionTracking import Utility as Utility
from MotionTracking.Motion import Motion
from MotionTracking.Table import Table
from MotionTracking.Utility import log

WINDOW_OPTICAL_FLOW = "Optical Flow Dense"


def callback_mouse(event, x, y, flag, param):
    r"""
    Image callback after mouse click.
    """

    if event == cv.EVENT_LBUTTONDOWN:
        print(f"Click image in position ({x},{y})")


def filtering(frame):
    r"""
    Filtering image.
    """
    return cv.GaussianBlur(frame, ksize=(9, 9), sigmaX=cv.BORDER_DEFAULT)


class OpticalFlowDense:
    r"""
    Class to detect moving vehicles by implementation of optical flow dense.
    """

    def __init__(self, video_url, height_cam=512, width_cam=750, excluded_area=True, show_log=True):
        """"
        Constructor of class.

        :param video_url: url to get video.
        :param height_cam: height of camera.
        :param width_cam: width of camera.
        :param excluded_area: bool, if true it does consider the polygon.
        :param show_log: bool, of true show the log.
        """

        # Camera
        self.height = height_cam
        self.width = width_cam
        self.camera = get_video(video_url["Path"], self.height, self.width)

        # Table
        self.app_qt = QApplication(sys.argv)
        self.table = Table(show_log)

        # Object Motion
        self.motion = Motion(self.table, excluded_area, show_log)

        # Frame Rate
        self.frame_rate_x, self.frame_rate_y = video_url["Frame rate"]
        self.previous_time = 0
        self.current_time = 0
        self.fps = 0

        self.alpha = 0.5

        # Flag
        self.excluded_area = excluded_area
        self.show_log = show_log
        self.iterations = 0

        # City
        self.obj_city = video_url
        self.polygons = None

        self.start_video = False

    def frame_rate(self, frame):
        """
        Calculates the frame rate.

        :param frame: img to put text.
        """

        self.current_time = time.time()
        self.fps = np.divide(1, (self.current_time - self.previous_time))
        self.previous_time = self.current_time
        Utility.set_text(frame, f"FPS: {int(self.fps)}", (self.frame_rate_x, self.frame_rate_y), dim=1.5,
                         color=Color.RED, thickness=2)

    def run(self):
        """
        Trackin vehicles by optical flow.
        """

        cv.namedWindow(WINDOW_OPTICAL_FLOW)
        cv.setMouseCallback(WINDOW_OPTICAL_FLOW, callback_mouse)

        data = load_coefficients("Calibration/data")
        camera_matrix, dist_matrix, rvecs, tvecs = data
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(camera_matrix, dist_matrix, (self.width, self.height), 0,
                                                         (self.width, self.height))

        if self.show_log:
            log(0, "Optical Flow Dense start!")
            log(0, f"City: {self.obj_city['Name']}")

        self.table.show()

        _, first_frame = self.camera.read()

        first_frame_copy = cv.resize(first_frame.copy(), (self.width, self.height))
        first_frame_copy = cv.undistort(first_frame_copy, camera_matrix, dist_matrix, None, newcameramtx)

        first_frame = filtering(first_frame)
        first_frame = cv.resize(first_frame, (self.width, self.height))
        first_frame = cv.undistort(first_frame, camera_matrix, dist_matrix, None, newcameramtx)

        prev_gray = cv.cvtColor(first_frame, cv.COLOR_BGR2GRAY)

        stack = Utility.stack_images(1, ([first_frame_copy, first_frame_copy]))
        cv.imshow(WINDOW_OPTICAL_FLOW, stack)

        mask = cv.resize(np.zeros_like(first_frame), (400, 400))
        stack_mask = Utility.stack_images(1, ([mask, mask]))
        cv.imshow("Masks", stack_mask)
        key = cv.waitKey(0)

        if self.excluded_area:
            self.polygons = Utility.get_polygon(self.obj_city)
            mask_poly = np.zeros_like(first_frame[:, :, 0])

            for polygon in self.polygons:
                cv.fillConvexPoly(mask_poly, polygon, 1)

        if key % 256 == 32:
            self.start_video = True

        if self.start_video:

            while self.camera.isOpened():

                ret, frame = self.camera.read()

                if ret:
                    if self.show_log:
                        log(0, f"Iteration: {self.iterations}")

                    frame_copy = cv.resize(frame.copy(), (self.width, self.height))
                    frame_copy = cv.undistort(frame_copy, camera_matrix, dist_matrix, None, newcameramtx)
                    img_to_draw = frame_copy.copy()

                    frame = filtering(frame)
                    frame = cv.resize(frame, (self.width, self.height))
                    frame = cv.undistort(frame, camera_matrix, dist_matrix, None, newcameramtx)

                    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

                    if self.excluded_area:
                        frame = cv.bitwise_and(frame, frame, mask=mask_poly)
                        # for polygon in self.polygons:
                        #    cv.polylines(frame, [polygon], True, (255, 0, 255), 8)

                    if self.excluded_area:
                        img_to_draw = cv.addWeighted(img_to_draw, self.alpha, frame, 1 - self.alpha, 0)

                    self.frame_rate(img_to_draw)

                    # Optical Flow Dense
                    flow = cv.calcOpticalFlowFarneback(prev_gray, gray, None, pyr_scale=0.5, levels=5, winsize=11,
                                                       iterations=5, poly_n=5, poly_sigma=1.1, flags=0)

                    # flow = cv.calcOpticalFlowFarneback(prev_gray, gray, None, pyr_scale=0.5, levels=5, winsize=15,
                    #                                    iterations=2, poly_n=5, poly_sigma=1.1, flags=0)

                    if self.show_log:
                        Utility.set_text(frame, f"Iter: {self.iterations}", (40, 45), dim=1.5, color=Color.RED)

                    self.motion.detect_vehicle(img=frame, img_to_draw=img_to_draw, flow=flow, iter=self.iterations,
                                               fps=self.fps,
                                               polygons=self.polygons)

                    stack = Utility.stack_images(1, ([img_to_draw, frame_copy]))
                    cv.imshow(WINDOW_OPTICAL_FLOW, stack)

                    key = cv.waitKey(1)
                    if key & 0xFF == ord('q'):
                        # Exit to the program
                        self.table.close()
                        cv.destroyAllWindows()
                        sys.exit()

                    # Update frame
                    prev_gray = gray
                    self.iterations += 1
