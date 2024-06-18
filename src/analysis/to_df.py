import re
import pandas as pd

class ScaphandreToDf:

    def __init__(self, json_data, pids=None, regex=None):
        self.json_data = json_data
        self.dfs = {}

    def host_to_df(self):
        filtered = [
            {"timestamp" : entry['host']['timestamp'], "host" : entry['host']['consumption']  / 1000000}
            for entry in self.json_data
        ]
        df = pd.DataFrame(filtered).set_index('timestamp')
        self.dfs['host'] = df

    def travers_json(self, checker):
        results = {}
        for entry in self.json_data:
            for consumer in entry['consumers']:
                if checker(consumer):
                    pid = consumer['pid']
                    if pid not in results:
                        results[pid] = []
                    results[pid].append({
                        "timestamp": consumer['timestamp'],
                        "consumption": consumer['consumption'] / 1000000
                    })

        for pid in results:
            results[pid] = sorted(results[pid], key=lambda x: x['timestamp'])
            self.dfs[pid] = pd.DataFrame(results[pid]).set_index('timestamp')
        
    def pid_to_dfs(self, pids):
        self.travers_json(lambda x: x['pid'] in pids)

    def regex_to_dfs(self, regex):
        self.travers_json(lambda x: re.match(regex, x['exe']) or re.match(regex, x['cmdline']))

