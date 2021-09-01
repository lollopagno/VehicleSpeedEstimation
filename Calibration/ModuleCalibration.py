import cv2 as cv
import os
import numpy as np


class ModuleCalibration:
    r"""
    Class Module Calibration.
    """

    def __init__(self, obj_p, criteria, size_chessboard=(9, 6)):

        self.frame = []

        self.criteria = criteria
        self.size = size_chessboard

        # Arrays to store object points and image points from all the images.
        self.obj_points = []  # 3d point in real world space. (punti oggetto)
        self.img_points = []  # 2d points in image plane.     (punti immagine)

        self.obj_p = obj_p

        try:
            self.path = "data"
            os.mkdir(self.path)
        except Exception:
            pass

    def start(self, frame):
        """ Get intrinsic matrix and distortion coefficient. """
        frame_with_chessboard = frame.copy()
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, self.size, None)
        # cv.findCirclesGrid() # per scacchiera con cerchi

        # If found, add object points, image points (after refining them)
        if ret:
            self.obj_points.append(self.obj_p)
            corners_2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)

            self.img_points.append(corners_2)

        return ret, frame_with_chessboard

    def set_frame(self, frame):
        """ Set new frame. """
        self.frame = frame

    def calibrate(self):
        """ Calibration camera. """
        gray = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
        ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(self.obj_points, self.img_points, gray.shape[::-1], None,
                                                          None)
        np.savez(self.path + "/data_calibration.npz", mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)


def load_coefficients(path):
    """ Loads camera matrix and distortion coefficients. """

    with np.load(path + "/data_calibration.npz") as File:
        camera_matrix, dist_matrix, rvecs, tvecs = File['mtx'], File['dist'], File['rvecs'], File['tvecs']

    return [camera_matrix, dist_matrix, rvecs, tvecs]
