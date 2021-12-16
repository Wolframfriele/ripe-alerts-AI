from os.path import exists
import datetime
import requests
import ijson
import pandas as pd
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
        clean_result = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'rtt_min': measurement_result.rtt_min,
            'rtt_average': measurement_result.rtt_average,
            'packets_sent': measurement_result.packets_sent,
            'packets_received': measurement_result.packets_received
        }
        return clean_result

    def read_dataset(self, dataset_path):
        store_location = dataset_path[:-4] + 'feather'
        if exists(store_location):
            return pd.read_feather(store_location)
        else:
            self.convert_dataset(dataset_path, store=True)
            return pd.read_feather(store_location)

class TracerouteImport(object):
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
            # hop_number = hop_object.raw_data['hop']
            hop_pings = hop_object.raw_data['result']
            hop_ip = None
            # hop_as = None
            min_hop_rtt = float('inf')
            for ping in hop_pings:
                if 'from' in ping:
                    if hop_ip is None:
                        hop_ip = ping['from']
                        # r = requests.get(f"https://stat.ripe.net/data/network-info/data.json?resource={hop_ip}").json()['data']['asns']
                        # if len(r) > 0:
                        #     hop_as = r[0]
                    if ping['rtt'] < min_hop_rtt:
                        min_hop_rtt = ping['rtt']
            hops.append({
                'from': hop_ip,
                'min_rtt': min_hop_rtt,
                # 'as_nummer': hop_as
            })
        
        pre_entry_hop_rtt = None
        pre_entry_hop_ip = None

        # Make a variable that has the last ip adres

        for hop in hops:
            pass
            # Check if ip in as number, use the first one thats different as

        clean_result = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'total_hops': measurement_result.total_hops,
            'last_rtt_average': measurement_result.last_median_rtt,
            'pre_entry_hop_rtt': test,
            'pre_entry_hop_ip': temp
            # 'hops': hops
        }
        return clean_result

    def ip_in_as(self, ip, prefixes):
        if ip[:7] == prefixes[:7]:
            return True

traceroute_import = TracerouteImport()
df_traceroute = traceroute_import.convert_dataset('measurement_data/small_traceroute_2.json')
# print(df_traceroute)