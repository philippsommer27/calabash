import json
import numpy as np

class Analysis:

    def __init__(self, dfs, output_dir, repetitions):
        self.dfs = dfs
        self.results = {}
        self.output_dir = output_dir
        self.repetitions = repetitions

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
            "per_repetition": self.energy_consumption / self.repetitions
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
            "per_repetition": total_consumption / self.repetitions
        }        

    def do(self):
        self.timestamp_analysis()
        self.host_energy_analysis()
        self.host_power_analysis()
        self.process_energy_analysis()