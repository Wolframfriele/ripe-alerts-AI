import imp
import requests
import ijson
import pandas as pd
import numpy as np
import re
from time import perf_counter
from urllib.request import urlopen
from os.path import exists
from datetime import datetime
from ripe.atlas.sagan import PingResult, TracerouteResult
from adtk.detector import LevelShiftAD
from adtk.data import validate_series
from adtk.visualization import plot
from as_finder import RisASLookUp


class PingImport:
    result_pattern = re.compile("{.*(stored_timestamp).*}")

    def download_dataset(self, measurement_id):
        """creates initial dataset"""
        print(f"collecting initial dataset for measurement: {measurement_id}")
        results_list = []
        yesterday = int(datetime.now().timestamp()) - 24 * 60 * 60
        f = urlopen(
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results?start={yesterday}")
        parser = ijson.items(f, 'item')
        for measurement_data in parser:
            result = self.pre_process(measurement_data)
            results_list.append(result)
        df_ping: pd.DataFrame = pd.DataFrame(results_list)
        return df_ping

    def download_dataset_old(self, measurement_id):
        """creates initial dataset"""
        yesterday = int(datetime.now().timestamp()) - 24 * 60 * 60
        result_string = ""
        results_list = []
        response = requests.get(
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results?start={yesterday}",
            stream=True)
        for i in response.iter_content(decode_unicode=True):
            result_string += i
            result = PingImport.result_pattern.search(result_string)
            if result:
                start, end = result.span()
                ping_result_raw = result_string[start:end]
                result_string = result_string[end:]
                result = self.pre_process(ping_result_raw)
                results_list.append(result)
        df_ping: pd.DataFrame = pd.DataFrame(results_list)
        return df_ping

    def convert_dataset(self, dataset_path, store=False):
        """creates initial dataset from downloaded json file"""
        start = perf_counter()
        results_list = []
        with open(dataset_path) as f:
            parser = ijson.items(f, 'item')
            for measurement_data in parser:
                result = self.pre_process(measurement_data)
                results_list.append(result)
        df_ping: pd.DataFrame = pd.DataFrame(results_list)
        del results_list
        if store:
            store_location = dataset_path[:-4] + 'feather'
            df_ping.reset_index()
            df_ping.to_feather(store_location)

        run_time = round(perf_counter() - start, 4)
        print(f'Convert dataset: {run_time}')
        return df_ping

    def pre_process(self, single_result_raw):
        start = perf_counter()
        measurement_result = PingResult(single_result_raw)
        if measurement_result.packets_received == 0:
            packet_loss = 100
        else:
            packet_loss = round(((measurement_result.packets_sent -
                                measurement_result.packets_received) / measurement_result.packets_sent) * 100, 2)
        clean_result = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'rtt_min': measurement_result.rtt_min,
            'rtt_average': measurement_result.rtt_average,
            'packets_loss': packet_loss
        }
        run_time = round(perf_counter() - start, 4)
        print(f'Pre Process: {run_time}')
        return clean_result

    def read_dataset(self, dataset_path):
        """
        Check if a feather of json data already exist; if it exist import feather, 
        if doesnt exits: Convert json to dataframe and save a feather.
        """
        store_location = dataset_path[:-4] + 'feather'
        if exists(store_location):
            return pd.read_feather(store_location)
        else:
            self.convert_dataset(dataset_path, store=True)
            return pd.read_feather(store_location)
