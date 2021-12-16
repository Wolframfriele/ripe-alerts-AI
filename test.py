import ijson
from ripe.atlas.sagan import PingResult, TracerouteResult

dataset_path = '/home/wolframfriele/hu/prj/ripe-alerts-AI/measurement_data/small_traceroute_1.json'
results_list = []
with open(dataset_path) as f:
    parser = ijson.items(f, 'item')
    for measurement_data in parser:
        measurement_result = TracerouteResult(measurement_data, parse_hops=True, on_error=TracerouteResult.ACTION_IGNORE)
        # hops_raw =  measurement_result.raw_data["result"]
        # hops_cleaned = []
        # for hop in hops_raw[:2]:
        #     hops_cleaned.append(hop)
        row = {
            'probe_id': measurement_result.probe_id,
            'created': measurement_result.created,
            'total_hops': measurement_result.total_hops,
            'hops': measurement_result.hops
        }
        results_list.append(row)

for i in results_list[:1]:
    print(i["hops"][6].__dict__)


# "https://stat.ripe.net/data/network-info/data.json?resource=185.28.46.15"