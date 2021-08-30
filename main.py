import Common.url as Url
from OpticalFlow.opticalflow_dense import OpticalFlowDense

DENSE = "Dense"


class App:

    def __init__(self, video_url, type_op=DENSE, height_cam=512, width_cam=750):
        self.type_op = type_op

        self.op_dense = OpticalFlowDense(video_url=video_url,
                                         height_cam=height_cam,
                                         width_cam=width_cam,
                                         exclude_area=False,
                                         show_log=True)

    def run(self):
        self.op_dense.run()


if __name__ == "__main__":
    r"""
    Main
    """
    app = App(video_url=Url.CAMBRIDGE,
              type_op=DENSE)

    app.run()
