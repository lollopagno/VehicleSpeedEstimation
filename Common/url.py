import numpy as np

CITIES = ["TAIPEI", "BUSAN", "JACKSON HOLE", "DERRY", "CAMBRIDGE"]

# Polygons cities
polygons_taipei = []
polygons_busan = []
polygons_jackson_hole = []
polygons_derry = []
polygons_cambridge = [np.array([[330, 338], [469, 341], [353, 236], [298, 199], [290, 216], [299, 244]]),  # Top Polygon
                      np.array([[1, 374], [86, 364], [202, 343], [329, 329], [362, 412], [297, 410], [221, 418],
                                [142, 440], [111, 466], [118, 496], [1, 495]]),  # Left Polygon
                      np.array([[453, 511], [668, 509], [515, 377], [370, 395]]),  # Bottom Polygon
                      np.array([[365, 413], [393, 423], [513, 376], [467, 335], [329, 337], [335, 350],
                                [329, 351], [322, 356]]),  # Centered polygon
                      np.array([[474, 371], [510, 361], [521, 359], [563, 352], [560, 322], [457, 320]])
                      # Right Polygon
                      ]

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
