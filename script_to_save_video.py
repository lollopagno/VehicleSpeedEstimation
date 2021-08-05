import cv2 as cv
import pafy

from Common import url as Url

PATH = "video/jackson_hole.avi"

video_pafy = pafy.new(Url.CAMBRIDGE)
play = video_pafy.getbest()
cap = cv.VideoCapture(play.url)

frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

size_frame = (frame_width, frame_height)

video = cv.VideoWriter(PATH, cv.VideoWriter_fourcc(*'MJPG'), 10, size_frame)

while cap.isOpened():
    ret, frame = cap.read()

    if ret:
        video.write(frame)
        cv.imshow("OpenCv", frame)
        cv.waitKey(20)

        if 0xFF == ord('q'):
            break
