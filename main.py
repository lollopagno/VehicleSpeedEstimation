import common.url as Url
from opticalflow_sparse import OpticalFlowSparse

DENSE = "Dense"
SPARSE = "Sparse"


class App:

    def __init__(self, video_url, type_op=DENSE, height_cam=512, width_cam=750):
        self.type_op = type_op
        self.op_sparse = OpticalFlowSparse(video_url=video_url,
                                           height_cam=height_cam,
                                           width_cam=width_cam)

        self.op_dense = None

    def run(self):
        if self.type_op == SPARSE:
            self.op_sparse.run()


if __name__ == "__main__":
    r"""
    Main
    """

    app = App(video_url=Url.TAIPEI,
              type_op=SPARSE)
    app.run()
