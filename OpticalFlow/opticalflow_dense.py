import sys

import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication

from Common import color as Color
from Common import utility as Utility
from Common.load_video import get_video
from Common.table import Table
from Common.utility import log
from Frame_rate import FrameRate
from MotionTracking.Motion import Motion

WINDOW_OPTICAL_FLOW = "Optical Flow Dense"


def callback_mouse(event, x, y, flag, param):
    r"""
    Image callback after mouse click.
    """

    if event == cv.EVENT_LBUTTONDOWN:
        print(f"Click image in position ({x},{y})")


class OpticalFlowDense:
    r"""
    Class to detect moving vehicles by implementation of optical flow dense.
    """

    def __init__(self, video_url, height_cam=512, width_cam=750, exclude_area=True, show_log=True):
        """"
        Constructor of class.

        :param video_url: url to get video.
        :param height_cam: height of camera.
        :param width_cam: width of camera.
        :param exclude_area: bool, if true it doesn't consider the polygon.
        :param show_log: bool, of true show the log.
        """

        # Camera
        self.height = height_cam
        self.width = width_cam
        self.camera = get_video(video_url["Url"], self.height, self.width)

        # Table
        self.app_qt = QApplication(sys.argv)
        self.table = Table()

        # Object Motion
        self.motion = Motion(self.table)

        # Frame Rate
        x, y = video_url["Frame rate"]
        self.frame_rate = FrameRate(x=x, y=y)

        self.alpha = 0.5

        # Flag
        self.excluded_area = exclude_area
        self.show_log = show_log  # TODO insert this in code!
        self.iterations = 0

        # City
        self.obj_city = video_url
        self.polygons = None

    def run(self):

        cv.namedWindow(WINDOW_OPTICAL_FLOW)
        cv.setMouseCallback(WINDOW_OPTICAL_FLOW, callback_mouse)

        if self.show_log:
            log(0, "Optical Flow Dense start!")
            log(0, f"City: {self.obj_city['Name']}")

        self.table.show()

        _, first_frame = self.camera.read()
        first_frame = cv.resize(first_frame, (self.width, self.height))
        prev_gray = cv.cvtColor(first_frame, cv.COLOR_BGR2GRAY)

        # Mask: [HSV Model] hue (direction of car), value (velocity), saturation (unused)
        mask_hsv = np.zeros_like(first_frame)  # Each row of mask: (hue  [ANGLE], saturation, value [VELOCITY])
        mask_hsv[..., 1] = 255

        if not self.excluded_area:
            self.polygons = Utility.get_polygon(self.obj_city)
            mask_poly = np.zeros_like(first_frame[:, :, 0])

            for polygon in self.polygons:
                cv.fillConvexPoly(mask_poly, polygon, 1)

        while self.camera.isOpened():

            ret, frame = self.camera.read()

            if ret:
                if self.show_log:
                    log(0, f"Iteration: {self.iterations}")

                frame = cv.medianBlur(frame, ksize=5)
                frame = cv.resize(frame, (self.width, self.height))
                frame_copy = frame.copy()
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

                if not self.excluded_area:
                    frame = cv.bitwise_and(frame, frame, mask=mask_poly)

                self.frame_rate.run(frame)

                # Optical Flow Dense
                flow = cv.calcOpticalFlowFarneback(prev_gray, gray, None, pyr_scale=0.5, levels=5, winsize=11,
                                                   iterations=5, poly_n=5, poly_sigma=1.1, flags=0)

                # Magnitude and angle
                magnitude, angle = cv.cartToPolar(flow[..., 0], flow[..., 1])

                # Set image hue according to the optical flow direction
                mask_hsv[..., 0] = angle * 180 / np.pi / 2

                # Set image value according to the optical flow magnitude (normalized)
                mask_hsv[..., 2] = cv.normalize(magnitude, None, 0, 255, cv.NORM_MINMAX)

                mask_rgb = cv.cvtColor(mask_hsv, cv.COLOR_HSV2BGR)
                mask = np.zeros_like(frame)
                mask = cv.addWeighted(mask, 1, mask_rgb, 2, 0)

                Utility.set_text(frame, str(self.iterations), (33, 26), color=Color.RED)
                self.motion.detect_vehicle(img=frame, mask=mask, iter=self.iterations, fps=self.frame_rate.fps,
                                           polygons=self.polygons)

                if not self.excluded_area:
                    frame = cv.addWeighted(frame_copy, self.alpha, frame, 1 - self.alpha, 0)

                cv.imshow(WINDOW_OPTICAL_FLOW, frame)

                # Update frame
                prev_gray = gray
                self.iterations += 1

                if cv.waitKey(1) & 0xFF == ord('q'):
                    break

        cv.destroyAllWindows()
        sys.exit(self.app_qt.exec_())
