import numpy as np

CITIES = ["TAIPEI", "BUSAN", "JACKSON HOLE", "DERRY", "CAMBRIDGE"]

# Polygons cities
polygons_taipei = []
polygons_busan = []
polygons_jackson_hole = []
polygons_derry = []
polygons_cambridge = [np.array([[1, 397], [86, 386], [198, 369], [320, 356], [362, 412], [297, 410], [221, 418],
                                [142, 440], [111, 466], [118, 496], [1, 495]]),
                      np.array([[453, 511], [668, 509], [515, 377], [390, 423]]),
                      np.array([[365, 413], [393, 423], [513, 376], [467, 335], [329, 337], [335, 350],
                                [329, 351], [322, 356]]),
                      np.array([[467, 335], [353, 236], [298, 242], [330, 337], [291, 218], [292, 200],
                                [304, 199], [352, 237]]),
                      np.array([[506, 368], [510, 361], [521, 359], [563, 352], [535, 323], [501, 330], [478, 336],
                                [465, 333]])]

# Urls videos
TAIPEI = {"Index": 0, "Name": "TAIPEI", "Lane": 2, "Url": "https://youtu.be/XV1q_2Cl6mI",
          "Frame rate": (635, 40), "Polygon": polygons_taipei}  # Taiwan

BUSAN = {"Index": 1, "Name": "BUSAN", "Lane": 0, "Url": "https://youtu.be/pUcWdJoAuyw",
         "Frame rate": (0, 0), "Polygon": polygons_busan}  # South Korea

JACKSON_HOLE = {"Index": 2, "Name": "JACKSON HOLE", "Lane": 0, "Url": "https://youtu.be/1EiC9bvVGnk",
                "Frame rate": (0, 0), "Polygon": polygons_jackson_hole}  # USA

DERRY = {"Index": 3, "Name": "DERRY", "Lane": 0, "Url": "https://youtu.be/3g_xTJWPJ74", "Frame rate": (0, 0),
         "Polygon": polygons_derry}  # USA

CAMBRIDGE = {"Index": 4, "Name": "CAMBRIDGE", "Lane": 0, "Url": "https://youtu.be/f1DyY6a44yA",
             "Frame rate": (635, 40), "Polygon": polygons_cambridge}  # USA
