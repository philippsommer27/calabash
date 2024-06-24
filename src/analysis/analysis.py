import json
import numpy as np

from to_df import ScaphandreToDf
from preprocess import read_json

class Analysis:

    def __init__(self, dfs, timesheet, config):
        self.timesheet = timesheet
        self.config = config
        self.dfs = dfs
        self.results = {}

    def write_json(self):
        with open(f'{config['out']}/analysis.json', 'w') as file:
            json.dump(self.results, file, indent=4)

    def write_dfs(self):
        for pid, df in self.dfs.items():
            df.to_csv(f'{config['out']}/{pid}.csv', index=False)

    def export(self):
        self.write_json()
        self.write_dfs()

    def timestamp_analysis(self):
        ts_differences = self.dfs['host'].index.to_series().diff().dropna()
        self.results['timestamp_analysis'] = {
            "mean": ts_differences.mean(),
            "std": ts_differences.std(),
            "min": ts_differences.min(),
            "max": ts_differences.max(),
            "median": ts_differences.median(),
            "running_time": self.dfs['host'].index.to_list()[-1]
        }

    def host_energy_analysis(self):
        self.energy_consumption = np.trapz(self.dfs['host']['consumption'], x=self.dfs['host'].index)
        self.results['host_energy_analysis'] = {
            "total": self.energy_consumption,
            "per_repetition": self.energy_consumption / self.config['procedure']['repetitions']
        }

    def host_power_analysis(self):
        self.results['host_ower_analysis'] = {
            "mean": self.dfs['host']['consumption'].mean(),
            "std": self.dfs['host']['consumption'].std(),
            "min": self.dfs['host']['consumption'].min(),
            "max": self.dfs['host']['consumption'].max(),
            "median": self.dfs['host']['consumption'].median()
        }

    def process_energy_analysis(self):
        total_consumption = 0
        for pid, df in self.dfs.items():
            if pid != 'host':
                total_consumption += np.trapz(df['consumption'], x=df.index)

        self.results['process_energy_analysis'] = {
            "total": total_consumption,
            "per_repetition": total_consumption / self.config['procedure']['repetitions']
        }

if __name__ == '__main__':
    filepath = 'out/ce-t3-0.json'
    timesheet_path = 'out/ce-t3-0_t.json'
    marker = 't3'
    config = {
        "procedure": {
            "repetitions": 10000000
        }
    }

    json_data = read_json(filepath)
    timesheet = read_json(timesheet_path)

    converter = ScaphandreToDf(json_data)
    converter.host_to_df()

    analysis = Analysis(converter.dfs, timesheet, config)
    analysis.timestamp_analysis()
    analysis.host_energy_analysis()
    analysis.host_power_analysis()

    print(json.dumps(analysis.results, indent=2))