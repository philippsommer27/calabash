import re
import pandas as pd
from typing import List, Dict, Any, Optional

class ScaphandreToDf:

    def __init__(self, json_data: List[Dict[str, Any]], pids: Optional[List[int]] = None, regex: Optional[str] = None) -> None:
        self.json_data = json_data
        self.pids = pids
        self.regex = regex
        self.fst_ts = self.find_fst_ts(json_data)
        self.dfs: Dict[str, pd.DataFrame] = {}

    def host_to_df(self) -> None:
        filtered = [
            {"timestamp": entry['host']['timestamp'] - self.fst_ts, "consumption": entry['host']['consumption'] / 1000000}
            for entry in self.json_data
        ]
        df = pd.DataFrame(filtered).set_index('timestamp')
        self.dfs['host'] = df

    def travers_json(self, checker) -> None:
        results: Dict[str, List[Dict[str, Any]]] = {}
        for entry in self.json_data:
            for consumer in entry['consumers']:
                if checker(consumer):
                    pid = consumer['pid']
                    if pid not in results:
                        results[pid] = []
                    results[pid].append({
                        "timestamp": consumer['timestamp'] - self.fst_ts,
                        "consumption": consumer['consumption'] / 1000000  # may be wrong due to https://github.com/hubblo-org/scaphandre/issues/378
                    })
                    
        for pid in results:
            results[pid] = sorted(results[pid], key=lambda x: x['timestamp'])
            self.dfs[pid] = pd.DataFrame(results[pid]).set_index('timestamp')
        
    def pid_to_dfs(self, pids: List[int]) -> None:
        self.travers_json(lambda x: x['pid'] in pids)

    def regex_to_dfs(self, regex: str) -> None:
        self.travers_json(lambda x: re.match(regex, x['exe']) or re.match(regex, x['cmdline']))

    def find_fst_ts(self, json_data: List[Dict[str, Any]]) -> float:
        return min(json_data[0]['host']['timestamp'], 
                   min([consumer['timestamp'] for consumer in json_data[0]['consumers']]))

    def export_dfs(self, output_path: str) -> None:
        for name, df in self.dfs.items():
            df.to_csv(f'{output_path}/{name}.csv')
