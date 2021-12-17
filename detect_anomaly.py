import numpy as np
import pandas as pd

class SimpleDetector(object):
    def __init__(self) -> None:

        super().__init__()

    def fit(self, data):
        np_data = data.to_numpy()
        median = np_data.median()
        maximum = np_data.max()
        