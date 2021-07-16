import time

import numpy as np

import common.color as Colors
import common.utility as Utility


class FrameRate:

    def __init__(self):
        self.current_time = 0
        self.previous_time = 0
        self.fps = 0

    def run(self, img):
        self.current_time = time.time()
        self.fps = np.divide(1, (self.current_time - self.previous_time))
        self.previous_time = self.current_time
        Utility.set_text(img, f"FPS: {int(self.fps)}", (610, 40), dim=1.5, color=Colors.RED, thickness=4)
