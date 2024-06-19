import re
import pandas as pd

class ScaphandreToDf:

    def __init__(self, json_data, pids=None, regex=None):
        self.json_data = json_data
        self.fst_ts = self.find_fst_ts(json_data)
        self.dfs = {}

    def host_to_df(self):
        filtered = [
            {"timestamp" : entry['host']['timestamp'] - self.fst_ts, "consumption" : entry['host']['consumption']  / 1000000}
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
                        "timestamp": consumer['timestamp'] - self.fst_ts,
                        "consumption": consumer['consumption'] / 1000000
                    })

        for pid in results:
            results[pid] = sorted(results[pid], key=lambda x: x['timestamp'])
            self.dfs[pid] = pd.DataFrame(results[pid]).set_index('timestamp')
        
    def pid_to_dfs(self, pids):
        self.travers_json(lambda x: x['pid'] in pids)

    def regex_to_dfs(self, regex):
        self.travers_json(lambda x: re.match(regex, x['exe']) or re.match(regex, x['cmdline']))

    def find_fst_ts(self, json_data):
        return min(json_data[0]['host']['timestamp'], 
                   min([consumer['timestamp'] for consumer in json_data[0]['consumers']]))
    
    def export_dfs(self, output_path):
        for name, df in self.dfs.items():
            df.to_csv(f'{output_path}/{name}.csv')
