import numpy as np
from typing import Dict, Any

class Analysis:

    def __init__(self, dfs: Dict[str, Any], repetitions: int):
        self.dfs = dfs
        self.results: Dict[str, Any] = {}
        self.repetitions = repetitions

    def timestamp_analysis(self) -> None:
        ts_differences = self.dfs['host'].index.to_series().diff().dropna()
        self.results['timestamp_analysis'] = {
            "mean": ts_differences.mean(),
            "std": ts_differences.std(),
            "min": ts_differences.min(),
            "max": ts_differences.max(),
            "median": ts_differences.median(),
            "running_time": self.dfs['host'].index.to_list()[-1]
        }

    def host_energy_analysis(self) -> None:
        self.energy_consumption: float = np.trapz(self.dfs['host']['consumption'], x=self.dfs['host'].index)
        self.results['host_energy_analysis'] = {
            "total": self.energy_consumption,
            "per_repetition": self.energy_consumption / self.repetitions
        }

    def host_power_analysis(self) -> None:
        self.results['host_power_analysis'] = {
            "mean": self.dfs['host']['consumption'].mean(),
            "std": self.dfs['host']['consumption'].std(),
            "min": self.dfs['host']['consumption'].min(),
            "max": self.dfs['host']['consumption'].max(),
            "median": self.dfs['host']['consumption'].median()
        }

    def process_energy_analysis(self) -> None:
        total_consumption: float = 0
        for pid, df in self.dfs.items():
            if pid != 'host':
                total_consumption += np.trapz(df['consumption'], x=df.index)

        self.results['process_energy_analysis'] = {
            "total": total_consumption,
            "per_repetition": total_consumption / self.repetitions
        }        

    def do(self) -> None:
        self.timestamp_analysis()
        self.host_energy_analysis()
        self.host_power_analysis()
        self.process_energy_analysis()