from os.path import exists
import datetime
import requests
import ijson
import pandas as pd
import numpy as np
from ripe.atlas.sagan import PingResult, TracerouteResult

class PingImport(object):
    def download_dataset(self, measurement_id):
        """creates initial dataset"""
        print(f"collecting initial dataset for measurement: {measurement_id}")
        results_list = []
        yesterday = int(datetime.now().timestamp()) - 24 * 60 * 60
        response = requests.get(
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results?start={yesterday}",
            stream=True)
        parser = ijson.items(response, 'item')
        for measurement_data in parser:
            result = self.pre_process(measurement_data)
            results_list.append(result)
        df_ping: pd.DataFrame = pd.DataFrame(results_list)
        return df_ping

    def convert_dataset(self, dataset_path, store=False):
        """creates initial dataset from downloaded json file"""
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
        return df_ping

    def pre_process(self, single_result_raw):
        measurement_result = PingResult(single_result_raw)
        if measurement_result.packets_received == 0:
            packet_loss = 100
        else:
            packet_loss = round(((measurement_result.packets_sent - measurement_result.packets_received) / measurement_result.packets_sent) * 100, 2)
        clean_result = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'rtt_min': measurement_result.rtt_min,
            'rtt_average': measurement_result.rtt_average,
            'packets_loss': packet_loss
        }
        return clean_result

    def read_dataset(self, dataset_path):
        """
        Check if a feather of json data already exist; if it exist import feather, if doesnt exits: Convert json to dataframe and save a feather.
        """
        store_location = dataset_path[:-4] + 'feather'
        if exists(store_location):
            return pd.read_feather(store_location)
        else:
            self.convert_dataset(dataset_path, store=True)
            return pd.read_feather(store_location)

class TracerouteImport(object):
    known_ip = {}
    own_as = None

    def download_dataset(self, measurement_id):
        """creates initial dataset"""
        print(f"collecting initial dataset for measurement: {measurement_id}")
        results_list = []
        yesterday = int(datetime.now().timestamp()) - 24 * 60 * 60
        response = requests.get(
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results?start={yesterday}",
            stream=True)
        parser = ijson.items(response, 'item')
        for measurement_data in parser:
            result = self.pre_process(measurement_data)
            results_list.append(result)
        df_traceroute: pd.DataFrame = pd.DataFrame(results_list)
        return df_traceroute

    def convert_dataset(self, dataset_path, store=False):
        """creates initial dataset from downloaded json file"""
        results_list = []
        with open(dataset_path) as f:
            parser = ijson.items(f, 'item')
            for measurement_data in parser:
                result = self.pre_process(measurement_data)
                results_list.append(result)
        df_traceroute: pd.DataFrame = pd.DataFrame(results_list)
        del results_list
        if store:
            store_location = dataset_path[:-4] + 'feather'
            df_traceroute.reset_index()
            df_traceroute.to_feather(store_location)
        return df_traceroute

    def read_dataset(self, dataset_path):
        store_location = dataset_path[:-4] + 'feather'
        if exists(store_location):
            return pd.read_feather(store_location)
        else:
            self.convert_dataset(dataset_path, store=True)
            return pd.read_feather(store_location)
                
    def pre_process(self, single_result_raw):
        measurement_result = TracerouteResult(single_result_raw,
                                              on_error=TracerouteResult.ACTION_IGNORE)
        hops = []
        for hop_object in measurement_result.hops:
            hop_number = hop_object.raw_data['hop']
            if 'error' in hop_object.raw_data:
                hops.append({
                    'hop': None,
                    'from': None,
                    'min_rtt': None,
                })
            else:
                try:
                    hop_pings = hop_object.raw_data['result']
                except KeyError:
                    print(hop_object.raw_data)

                hop_ip = None
                min_hop_rtt = float('inf')
                for ping in hop_pings:
                    if 'rtt' in ping:
                        if hop_ip == None:
                            hop_ip = ping['from']
                        if ping['rtt'] < min_hop_rtt:
                            min_hop_rtt = ping['rtt']

                min_hop_rtt = float(min_hop_rtt)
                hops.append({
                    'hop': hop_number,
                    'from': hop_ip,
                    'min_rtt': min_hop_rtt,
                })

        pre_entry_hop_min_rtt, pre_entry_hop_ip, pre_entry_as = np.nan, np.nan, np.nan

        # Make a variable that has the last ip adres
        as_ip = measurement_result.destination_address

        hops.reverse()
        for idx, hop in enumerate(hops):
            # Check if ip in as number, use the first one thats different AS
            if not self.ip_in_as(hop['from'], as_ip):
                # print('Hop not in AS')
                pre_entry_hop_ip = hop['from']
                pre_entry_hop_min_rtt = hops[idx - 1]['min_rtt']
                if idx - 1 == -1:
                    pre_entry_hop_min_rtt = float('inf')
                pre_entry_as = self.get_as(pre_entry_hop_ip)
                break
    
        clean_result = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'total_hops': measurement_result.total_hops,
            'pre_entry_hop_min_rtt': pre_entry_hop_min_rtt,
            'pre_entry_hop_ip': pre_entry_hop_ip,
            'pre_entry_as': pre_entry_as
        }

        return clean_result

    def get_as(self, ip):
        as_num = None
        if ip is not None:
            if ip in self.known_ip:
                as_num = self.known_ip[ip]
            else:
                r = requests.get(f"https://stat.ripe.net/data/network-info/data.json?resource={ip}").json()['data']['asns']
                if len(r) > 0:
                    as_num = r[0]
                else:
                    as_num = np.nan
                self.known_ip[ip] = as_num
        return as_num

    def ip_in_as(self, ip, goal_ip):
        in_as = False
        if self.own_as is None:
            self.own_as = self.get_as(goal_ip)
        if self.get_as(ip) == self.own_as:
            in_as = True
        return in_as
