import cv2 as cv
import pafy

from Common.utility import log


def get_video(url, height, width):
    r"""
    Parse url video. Setting video capture.

    :param url: url-video.
    :param height: height of camera video.
    :param width: width of camera video.
    """
    flag = False  # Fix unknown exception of pafy

    while not flag:
        try:
            #video_pafy = pafy.new(url)
            #play = video_pafy.getbest()
            #cap = cv.VideoCapture(play.url)

            cap = cv.VideoCapture("video/cambridge.avi")
            cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
            flag = True
        except Exception as e:
            log(1, f"Error load video: {e}")

    return cap
