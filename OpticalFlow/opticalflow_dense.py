import sys

import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication

from Common.load_video import get_video
from Common.table import Table
from Common.utility import log
from Frame_rate import FrameRate
from MotionTracking.Motion import detect_vehicle

WINDOW_OPTICAL_FLOW = "Optical Flow Dense"


def callback_mouse(event, x, y, flag, param):
    r"""
    Image callback after mouse click.
    """

    if event == cv.EVENT_LBUTTONDOWN:
        print(f"Click image in position ({x},{y})")


class OpticalFlowDense:

    def __init__(self, video_url, height_cam=512, width_cam=750, show_log=True):
        # Camera
        self.height = height_cam
        self.width = width_cam
        self.camera = get_video(video_url["Url"], self.height, self.width)

        # Table
        self.app_qt = QApplication(sys.argv)
        self.table = Table()

        self.vehicle_list = []
        self.counter_vehicle = 0

        # Frame Rate
        x, y = video_url["Frame rate"]
        self.frame_rate = FrameRate(x=x, y=y)

        self.show_log = show_log
        self.iterations = 0
        self.city = video_url["Name"]

    def run(self):

        cv.namedWindow(WINDOW_OPTICAL_FLOW)
        cv.setMouseCallback(WINDOW_OPTICAL_FLOW, callback_mouse)

        if self.show_log:
            log(0, "Optical Flow Dense start!")
            log(0, f"City: {self.city}")

        self.table.show()

        _, first_frame = self.camera.read()
        first_frame = cv.resize(first_frame, (self.width, self.height))
        prev_gray = cv.cvtColor(first_frame, cv.COLOR_BGR2GRAY)

        # Mask: [HSV Model] hue (direction of car), value (velocity), saturation (unused)
        mask_hsv = np.zeros_like(first_frame)  # Each row of mask: (hue  [ANGLE], saturation, value [VELOCITY])
        mask_hsv[..., 1] = 255

        while self.camera.isOpened():

            ret, frame = self.camera.read()

            if ret:

                frame = cv.bilateralFilter(frame, 9, 75, 75)
                frame = cv.resize(frame, (self.width, self.height))
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

                self.frame_rate.run(frame)

                # Optical Flow Dense
                flow = cv.calcOpticalFlowFarneback(prev_gray, gray, None, pyr_scale=0.5, levels=5, winsize=11,
                                                   iterations=5,
                                                   poly_n=5, poly_sigma=1.1, flags=0)

                # Magnitude and angle
                magnitude, angle = cv.cartToPolar(flow[..., 0], flow[..., 1])

                # Set image hue according to the optical flow direction
                mask_hsv[..., 0] = angle * 180 / np.pi / 2

                # Set image value according to the optical flow magnitude (normalized)
                mask_hsv[..., 2] = cv.normalize(magnitude, None, 0, 255, cv.NORM_MINMAX)

                mask_rgb = cv.cvtColor(mask_hsv, cv.COLOR_HSV2BGR)
                mask = np.zeros_like(frame)
                mask = cv.addWeighted(mask, 1, mask_rgb, 2, 0)

                self.vehicle_list, self.counter_vehicle = detect_vehicle(img=frame, mask=mask,
                                                                         vehicles=self.vehicle_list,
                                                                         counter_vehicle=self.counter_vehicle,
                                                                         table=self.table)

                log(0, f"Iteration: {self.iterations}")
                self.iterations += 1
                dense_flow = cv.addWeighted(frame, 1, mask_rgb, 2, 0)

                # cv.imshow("Dense Optical Flow", dense_flow)
                cv.imshow("Mask", cv.resize(mask, (400, 400)))
                cv.imshow(WINDOW_OPTICAL_FLOW, frame)

                # Update frame
                prev_gray = gray

                if cv.waitKey(1) & 0xFF == ord('q'):
                    break

        cv.destroyAllWindows()
        sys.exit(self.app_qt.exec_())
