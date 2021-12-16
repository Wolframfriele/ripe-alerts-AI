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
            hop_number = hop_object.raw_data['hop']
            hop_pings = hop_object.raw_data['result']
            hop_ip = None
            # hop_as = None
            min_hop_rtt = float('inf')
            mean_hop_rtt = 0
            for ping in hop_pings:
                if 'rtt' in ping:
                    mean_hop_rtt += ping['rtt']
                    if hop_ip == None:
                        hop_ip = ping['from']
                        # r = requests.get(f"https://stat.ripe.net/data/network-info/data.json?resource={hop_ip}").json()['data']['asns']
                        # if len(r) > 0:
                        #     hop_as = r[0]
                    if ping['rtt'] < min_hop_rtt:
                        min_hop_rtt = ping['rtt']
            
            if hop_ip is not None:
                hops.append({
                    'hop': hop_number,
                    'from': hop_ip,
                    'min_rtt': min_hop_rtt,
                    'mean_rtt': round(mean_hop_rtt / 3, 2)
                    # 'as_nummer': hop_as
                })
            
        pre_entry_hop_min_rtt = None
        pre_entry_hop_mean_rtt = None
        pre_entry_hop_ip = None

        # Make a variable that has the last ip adres
        as_ip = measurement_result.destination_address
        for hop in hops[::-1]:
            # Check if ip in as number, use the first one thats different as
            if not self.ip_in_as(hop['from'], as_ip):
                pre_entry_hop_ip = hop['from']
                pre_entry_hop_min_rtt = hop['min_rtt']
                pre_entry_hop_mean_rtt = hop['mean_rtt']
                break

        clean_result = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'total_hops': measurement_result.total_hops,
            'last_rtt_average': measurement_result.last_median_rtt,
            'pre_entry_hop_min_rtt': pre_entry_hop_min_rtt,
            'pre_entry_hop_mean_rtt': pre_entry_hop_mean_rtt,
            'pre_entry_hop_ip': pre_entry_hop_ip
            # 'hops': hops
        }
        return clean_result

    def ip_in_as(self, ip, start_ip):
        if ip[:7] == start_ip[:7]:
            return True
        else:
            return False

# traceroute_import = TracerouteImport()
# df_traceroute = traceroute_import.convert_dataset('measurement_data/small_traceroute_2.json')
# # print(df_traceroute)