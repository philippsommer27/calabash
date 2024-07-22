from analysis import Analysis
from visualizer import boxplot, power_plot
from preprocess import preprocess_scaphandre
from process_ptrace import resolve
from to_df import ScaphandreToDf
from misc.config import load_configuration
from misc.util import read_json, get_display_name, read_file, create_directory, write_json
from preflight import check
from scipy.stats import shapiro, ttest_rel
from numpy import sqrt
import pandas as pd
import logging
from typing import List, Dict, Any

SUMMARY_KEYS = [
    'host_energy_total', 'host_energy_per_repetition', 'process_energy_total',
    'process_energy_per_repetition', 'timestamp_running_time', 'host_power_mean'
]

def run(config_path: str) -> None:
    config = load_configuration(config_path)
    dfs: List[pd.DataFrame] = []
    host_power_dfs: List[List[pd.DataFrame]] = []
    summaries: List[pd.DataFrame] = []
    
    for image in config['images']:
        display_name = get_display_name(image)
        logging.info(f"Running analysis for %s", display_name)
        accumulated: Dict[int, Dict[str, Any]] = {}
        host_dfs: List[pd.DataFrame] = []
        
        for i in range(config['procedure']['external_repetitions']):
            logging.info("Repetition %d", i)
            directory = setup_directory(config['out'], display_name, i)

            if not check(directory):
                logging.error("Preflight check failed for %s", directory)
                exit()

            preprocess_data(directory, config['analysis'])
            converter = convert_to_dataframe(directory, config['analysis'])

            create_directory(f"{directory}/dfs")
            converter.export_dfs(f"{directory}/dfs")
            host_dfs.append(converter.dfs['host'])

            analysis_results = perform_analysis(converter.dfs, config['procedure']['internal_repetitions'])
            write_json(f"{directory}/analysis.json", analysis_results)
            accumulated[i] = analysis_results

        if config['procedure']['external_repetitions'] > 1:
            df = analyze_multiple_runs(accumulated)
            df.to_csv(f"{config['out']}/{display_name}/accumulated.csv")
            dfs.append(df)
            summary = df.describe()
            summary.to_csv(f"{config['out']}/{display_name}/summary.csv")
            summaries.append(summary)

            # Statistical Analysis
            shapiro_analysis = {}
            stat, p = shapiro(df['host_energy_total'])
            shapiro_analysis['host_analysis_shapiro'] = {'stat': stat, 'p': p}
            stat, p = shapiro(df['process_energy_total'])
            shapiro_analysis['process_analysis_shapiro'] = {'stat': stat, 'p': p}

            write_json(f"{config['out']}/{display_name}/shapiro_analysis.json", shapiro_analysis)

        host_power_dfs.append(host_dfs)

    if len(host_power_dfs) > 1:
        visualize_variations(dfs, host_power_dfs, config['out'])
        compare_variations(summaries, dfs, config['out'])

def setup_directory(out_path: str, display_name: str, iteration: int) -> str:
    curr_dir_prefix = f"/{iteration}"
    return f"{out_path}/{display_name}{curr_dir_prefix}"

def preprocess_data(directory: str, analysis_config: Dict[str, Any]) -> None:
    kwargs = {}
    if 'prune_mark' in analysis_config:
        kwargs['prune_mark'] = analysis_config['prune_mark']
    if 'prune_buffer' in analysis_config:
        kwargs['prune_buffer'] = analysis_config['prune_buffer']
    
    preprocess_scaphandre(f'{directory}/power.json', f'{directory}/power_processed.json', f'{directory}/timesheet.json', **kwargs)

def convert_to_dataframe(directory: str, analysis_config: Dict[str, Any]) -> ScaphandreToDf:
    json_data = read_json(f"{directory}/power_processed.json")
    converter = ScaphandreToDf(json_data)
    converter.host_to_df()
    
    if analysis_config['mode'] == 'pid':
        rpid = read_file(f"{directory}/rpid.txt")
        pids = resolve(f"{directory}/ptrace.txt", rpid)
        converter.pid_to_dfs(pids)
    else:
        converter.regex_to_dfs(analysis_config['regex'])

    return converter

def perform_analysis(dfs: Dict[str, pd.DataFrame], internal_repetitions: int) -> Dict[str, Any]:
    analysis = Analysis(dfs, internal_repetitions)
    analysis.do()
    return analysis.results

def analyze_multiple_runs(data: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    flattened_data = {outer_k: {f"{inner_k}_{k}": v for inner_k, inner_v in outer_v.items() for k, v in inner_v.items()} for outer_k, outer_v in data.items()}
    df = pd.DataFrame.from_dict(flattened_data, orient='index')
    df.columns = df.columns.str.replace('analysis_', '', regex=False)
    return df

def calculate_percentage_change(new_value: float, base_value: float) -> float:
    return round(((base_value - new_value) / base_value) * 100, 2)

def update_result_for_first_entry(result: Dict[str, Dict[int, Any]], summary: pd.DataFrame, index: int) -> None:
    for key in SUMMARY_KEYS:
        result[key][index] = summary.loc['mean', key]

def update_result_for_subsequent_entries(result: Dict[str, Dict[int, Any]], summaries: List[pd.DataFrame], index: int, dfs: List[pd.DataFrame]) -> None:
    for key in SUMMARY_KEYS:
        new_value = summaries[index].loc['mean', key]
        base_value = summaries[0].loc['mean', key]

        # Calculate difference and percentage change
        difference = new_value - base_value
        percentage_change = calculate_percentage_change(new_value, base_value)

        # Paired t-test
        stat, p = ttest_rel(dfs[0][key], dfs[index][key])

        # Cohen's d
        n = summaries[0].loc['count', key]
        s1, s2 = summaries[0].loc['std', key], summaries[index].loc['std', key]
        m1, m2 = summaries[0].loc['mean', key], summaries[index].loc['mean', key]
        pooled_std = sqrt(((n - 1) * s1 ** 2 + (n - 1) * s2 ** 2) / (2 * n - 2))
        d = (m1 - m2) / pooled_std
        
        result[key][index] = {'value': new_value, 
                              'difference': difference,
                              'change_perc' : percentage_change, 
                              'ttest': {'stat': stat, 'p': p},
                               'cohen_d': d}

def compare_variations(summaries: List[pd.DataFrame], dfs: List[pd.DataFrame], output_path: str) -> None:
    logging.info("Comparing variations")
    result = {key: {} for key in SUMMARY_KEYS}

    for i, summary in enumerate(summaries):
        if i == 0:
            update_result_for_first_entry(result, summary, i)
        else:
            update_result_for_subsequent_entries(result, summaries, i, dfs)
    
    write_json(f"{output_path}/comparison.json", result)

def visualize_variations(dfs: List[pd.DataFrame], host_power_dfs: List[List[pd.DataFrame]], output_path: str) -> None:
    logging.info("Creating visualizations")
    boxplot(dfs, 'host_energy_total', f"{output_path}/host_energy_total.png")
    boxplot(dfs, 'timestamp_running_time', f"{output_path}/timestamp_running_time.png")
    boxplot(dfs, 'host_power_mean', f"{output_path}/host_power_mean.png")
    boxplot(dfs, 'process_energy_total', f"{output_path}/process_energy_total.png")

    for i, power_dfs in enumerate(host_power_dfs):
        power_plot(power_dfs, f"{output_path}/host_power_{i}.png")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
    run("test.yaml")
