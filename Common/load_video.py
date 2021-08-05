import pafy
import cv2 as cv


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
            video_pafy = pafy.new(url)
            play = video_pafy.getbest()

            cap = cv.VideoCapture(play.url)
            cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
            flag = True
        except:
            pass

    return cap
