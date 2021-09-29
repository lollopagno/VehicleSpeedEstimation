import cv2 as cv
import pafy

from Common import url as Url

PATH = "video/test_video"

video_pafy = pafy.new(Url.CAMBRIDGE['Path'])
play = video_pafy.getbest()
cap = cv.VideoCapture(play.url)

frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

size_frame = (frame_width, frame_height)

video = cv.VideoWriter(PATH, cv.VideoWriter_fourcc(*'MJPG'), 10, size_frame)

window_name = "Save video in progres..."
cv.namedWindow(window_name)

while cap.isOpened():
    ret, frame = cap.read()

    if ret:
        video.write(frame)
        frame = cv.resize(frame, (650, 650))
        cv.imshow(window_name, frame)
        cv.waitKey(1)

        if 0xFF == ord('q'):
            break
