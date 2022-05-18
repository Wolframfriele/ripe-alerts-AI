import subprocess
import radix
import pickle
import numpy as np
from os.path import exists, getmtime
from time import time


class ASLookUp:
    """
    Class that uses riswhois data to return the corresponding AS number for an IP adress.
    """
    FIRST_IP_INDEX = 12
    LAST_IP_INDEX = -4

    def __init__(self) -> None:
        if exists('rtree.pickle'):
            day_length = 86400
            modified_time = getmtime('rtree.pickle')
            older_then_day = (time() - modified_time) > day_length
            print(f'RIS data older then day: {older_then_day}')
            if older_then_day:
                self.get_ris()
            else:
                print('Opening Existing RIS data')
                with open('rtree.pickle', 'rb') as f:
                    self.rtree = pickle.load(f)
        else:
            self.get_ris()

    def get_ris(self) -> None:
        """
        Connects to riswhois.ripe.net and stores IP adresses in a radix tree.
        """
        routing_ip = subprocess.run(['whois', '-h', 'riswhois.ripe.net', 'dump'],
                                    stdout=subprocess.PIPE).\
            stdout.decode(
            'utf-8').split("\n")[self.FIRST_IP_INDEX:self.LAST_IP_INDEX]

        routing_ip.extend(subprocess.run(['whois', '-h', 'riswhois.ripe.net', 'dump6'],
                          stdout=subprocess.PIPE).
                          stdout.decode('utf-8').split("\n")[self.FIRST_IP_INDEX:self.LAST_IP_INDEX])
        self.store_ris(routing_ip)
        print('Updated RIS data')

    def store_ris(self, routing_ip: list) -> None:
        """
        Takes list of ris info and store in radix tree, then saves to a pickle.
        """
        self.rtree = radix.Radix()
        for row in routing_ip:
            columns = row.split('\t')
            rnode = self.rtree.add(columns[1])
            rnode.data["asn"] = columns[0]
            rnode.data["seen_by"] = columns[2]

        with open('rtree.pickle', 'wb') as f:
            pickle.dump(self.rtree, f)

    def get_as(self, ip: str):
        """
        Finds AS for a given IP, returns NaN when AS is not found.

        Parameters:
                ip (str): A valid IP4 or IP6 adress.

        Returns:
                asn (str): corresponding AS number if found in radix tree.
        """
        try:
            asn = self.rtree.search_best(ip).data["asn"]
        except:
            print(ip)
            raise ValueError
        # except ValueError:
        #     asn = np.nan
        # except AttributeError:
        #     asn = np.nan
        # except TypeError:
        #     asn = np.nan
        return asn

if __name__ == '__main__':
    as_look_up = ASLookUp()
    # as_look_up.get_ris()
    print(as_look_up.get_as('145.89.252.43'))