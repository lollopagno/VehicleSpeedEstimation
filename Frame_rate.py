import time

import numpy as np

import Common.color as Colors
import Common.utility as Utility


class FrameRate:

    def __init__(self, x, y):
        self.current_time = 0
        self.previous_time = 0
        self.fps = 0

        # Coordinate
        self.x = x
        self.y = y

    def run(self, img):
        self.current_time = time.time()
        self.fps = np.divide(1, (self.current_time - self.previous_time))
        self.previous_time = self.current_time
        Utility.set_text(img, f"FPS: {int(self.fps)}", (self.x, self.y), dim=1.5, color=Colors.RED, thickness=2)
