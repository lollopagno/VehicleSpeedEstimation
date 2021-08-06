import cv2 as cv
import numpy as np

import Common.color as Color
import Common.utility as Utility
import MotionTracking.Motion as motion
from Common.load_video import get_video
from Frame_rate import FrameRate
from MotionTracking.ModuleTracking import TrackingModule

WINDOW_OPTICAL_FLOW = "Optical Flow Sparse"
WINDOW_PARAMETERS = "Parameters"

px2mm = 0.088  # TODO look this!

# Params for Shi-Tomasi corner detection
feature_params = dict(maxCorners=500,
                      qualityLevel=0.3,
                      minDistance=7,
                      blockSize=7)

# Parameters for Lucas-Kanade optical flow
lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03))


def callback_mouse(event, x, y, flag, param):
    r"""
    Image callback after mouse click.
    """
    if event == cv.EVENT_LBUTTONDOWN:
        Utility.log(0, f"Click image in position ({x},{y})")


class OpticalFlowSparse:

    def __init__(self, video_url, height_cam=512, width_cam=750, show_log=True):
        # Camera
        self.height = height_cam
        self.width = width_cam
        self.camera = get_video(video_url["Url"], self.height, self.width)

        # Info MotionTracking
        self.tracking_module = TrackingModule(video_url)

        # Optical flow
        self.corners = []
        self.corners_len = 2
        self.detect_interval = 4
        self.previous_frame = None
        self.id_frame = 0

        self.lane_list = []
        self.velocity_list = []
        self.corner_list = []

        # Frame Rate
        x, y = video_url["Frame rate"]
        self.frame_rate = FrameRate(x=x, y=y)

        self.show_log = show_log

        # Constants
        self.alpha = 0.5  # Used for addWeighted
        self.ms_2_kmh = 3.6  # Used to convert m/s into km/h
        self.minimum_corners = 5  # Minimum corners to update velocity

    def run(self):

        if self.show_log:
            Utility.log(0, "Optical Flow Sparse start!")
            Utility.log(0, f"City: {self.tracking_module.name_city}")

        _, first_frame = self.camera.read()
        first_frame = cv.resize(first_frame, (self.width, self.height))

        cv.namedWindow(WINDOW_OPTICAL_FLOW)
        cv.namedWindow(WINDOW_PARAMETERS)
        cv.setMouseCallback(WINDOW_OPTICAL_FLOW, callback_mouse)
        cv.setMouseCallback(WINDOW_PARAMETERS, callback_mouse)

        # Mask
        view_mask = np.zeros_like(first_frame[:, :, 0])
        parameters_mask = np.zeros((250, 600))

        # Polygons
        view_polygon = self.tracking_module.get_view_polygon()
        frame_rate_polygon = self.tracking_module.get_frame_rate_polygon()
        rectangle_polygon = self.tracking_module.get_rectangle_polygon()

        if len(view_polygon) > 0:
            cv.fillConvexPoly(view_mask, view_polygon, 1)

        if len(frame_rate_polygon) > 0:
            cv.fillConvexPoly(view_mask, frame_rate_polygon, 1)

        if len(rectangle_polygon) > 0:
            cv.fillConvexPoly(view_mask, rectangle_polygon, 1)

        lanes = self.tracking_module.get_number_lane()

        for index in range(0, lanes):
            self.lane_list.append(self.tracking_module.get_polygon_lane(index))
            self.velocity_list.append(0)
            self.corner_list.append(0)

        while self.camera.isOpened():
            ret, frame = self.camera.read()

            if ret:
                # Resize
                frame = cv.resize(frame, (self.width, self.height))
                frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                frame_copy = frame.copy()  # Temporary frame to execute operations

                img = cv.bitwise_and(frame_copy, frame_copy, mask=view_mask)

                # Draw text
                for index in range(0, len(self.lane_list)):
                    self.draw_param_lane(index, parameters_mask)

                    # Draw numbers
                    Utility.set_text(img, str(index + 1), self.tracking_module.draw_numbers(index),
                                     color=self.tracking_module.get_color(index), dim=3, thickness=3)

                # Draw lines
                if len(self.lane_list) != 0:
                    for index in range(0, len(self.lane_list) + 1):
                        (x1, y1), (x2, y2) = self.tracking_module.draw_line_between_lane(index)
                        cv.line(img, (x1, y1), (x2, y2), Color.RED, 3)

                # Frame rate
                self.frame_rate.run(img)

                # Draw polygons
                img_poly_lane = frame_copy.copy()

                for index, lane in enumerate(self.lane_list):
                    cv.fillPoly(img_poly_lane, [lane], self.tracking_module.get_color(index), cv.LINE_AA)

                img = cv.addWeighted(img_poly_lane, self.alpha, img, 1 - self.alpha, 0)

                if len(self.corners) > 0:
                    prev_img, current_img = self.previous_frame, frame_gray

                    # Detect motion
                    motion.detect_motion_sparse(img=frame, frame_1=prev_img, frame_2=current_img, VALUE_AREA=600)

                    prev_corners = np.float32([corner[-1] for corner in self.corners]).reshape(-1, 1, 2)

                    # Optical flow scattered
                    corners_1, st_1, err_1 = cv.calcOpticalFlowPyrLK(prev_img, current_img, prev_corners, None,
                                                                     **lk_params)
                    corners_2, st_2, err_2 = cv.calcOpticalFlowPyrLK(current_img, prev_img, corners_1, None,
                                                                     **lk_params)

                    # Difference between corners
                    difference = abs(prev_corners - corners_2).reshape(-1, 2).max(-1)
                    good = difference < 1
                    new_corners = []

                    for corner, (x, y), good_features in zip(self.corners, corners_1.reshape(-1, 2), good):

                        if not good_features:
                            continue

                        corner.append((round(x, 1), round(y, 1)))
                        if len(corner) > self.corners_len:
                            del corner[0]

                        new_corners.append(corner)
                        # cv.circle(frame, (int(x), int(y)), 3, Color.YELLOW, -1)

                    # Update corners
                    self.corners = new_corners

                    # Reset counter polygons
                    corner_local_list = []
                    distance_local_list = []

                    for _ in range(0, len(self.lane_list)):
                        corner_local_list.append(0)
                        distance_local_list.append(0)

                    for corner in self.corners:

                        # Determine which polygon the corner belongs to
                        for index, lane in enumerate(self.lane_list):
                            is_inside = cv.pointPolygonTest(lane, corner[0], True)

                            if is_inside > 0:
                                current_corner = corner_local_list[index]
                                current_distance = distance_local_list[index]

                                current_corner += 1
                                current_distance += Utility.calc_distance(corner[0], corner[1])
                                mmm_1 = current_distance / current_corner
                                current_velocity = self.get_velocity(mmm_1)

                                # Update values list
                                corner_local_list[index] = current_corner
                                self.velocity_list[index] = current_velocity
                                distance_local_list[index] = current_distance

                    self.corner_list = corner_local_list

                if self.id_frame % self.detect_interval == 0:
                    f"""Update values each n-interval ({self.detect_interval}) frames"""

                    for index, corners in enumerate(self.corner_list):
                        if corners > self.minimum_corners:
                            # Update velocity, corners
                            Utility.log(0,
                                        f"UPDATE VELOCITY\n1) V: {self.velocity_list[index]}, C: {self.corner_list[index]}")

                            self.draw_param_lane(index, parameters_mask)

                    mask = np.zeros_like(frame_gray)
                    mask[:] = 255
                    for x, y in [np.int32(track[-1]) for track in self.corners]:
                        # Draw circles (corners), if they exist
                        cv.circle(mask, (x, y), 3, Color.GREEN, -1)

                    # cv.imshow("Mask points", mask)

                    # Calculation corners
                    corners = cv.goodFeaturesToTrack(frame_gray, mask=mask, **feature_params)
                    if corners is not None:
                        for x, y in corners.reshape(-1, 2):
                            self.corners.append([(x, y)])

                # Update id and current frame
                self.id_frame += 1
                self.previous_frame = frame_gray

                # Show views
                cv.imshow("Original", frame)
                cv.imshow(WINDOW_OPTICAL_FLOW, img)
                cv.imshow(WINDOW_PARAMETERS, parameters_mask)
                cv.waitKey(10)

    def get_velocity(self, distance):
        r"""
        Calculate velocity.
        :param distance: distance between two points.
        """
        return round(distance * px2mm * self.frame_rate.fps * self.ms_2_kmh, 2)

    def draw_param_lane(self, index, mask):
        r"""
        Update the parameters for specific lane.
        :param index: current index of lane.
        :param mask: mask to update the parameters.
        """
        # Portion image: (y1,y2), (x1,x2)
        mask = self.tracking_module.refresh_mask(index, mask)

        Utility.set_text(mask, f"{index + 1}-Lane speed: {self.velocity_list[index]} km/h,  ",
                         self.tracking_module.get_velocity(index), color=Color.WHITE, dim=1.2, thickness=1)
        Utility.set_text(mask, f" {index + 1}-Corners : {self.corner_list[index]}",
                         self.tracking_module.get_corner(index), color=Color.WHITE, dim=1.2, thickness=1)
