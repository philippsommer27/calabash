from analysis import Analysis
from visualizer import boxplot, power_plot
from preprocess import preprocess_scaphandre
from process_ptrace import resolve
from to_df import ScaphandreToDf
from misc.config import load_configuration
from misc.util import read_json, get_display_name, read_file, create_directory, write_json
import pandas as pd

def run(config_path):
    config = load_configuration(config_path)
    dfs = []
    host_power_dfs = []
    summaries = []
    
    for image in config['images']:
        display_name = get_display_name(image)
        print(f"Running analysis for {display_name}")
        accumulated = {}
        host_dfs = []
        for i in range(config['procedure']['external_repetitions']):
            print(f"Repetition {i}")
            # Setup

            if config['procedure']['external_repetitions'] > 1:
                curr_dir_prefix = f"/{i}"
            else:
                curr_dir_prefix = ""
            directory = config['out'] + "/" + display_name + curr_dir_prefix
            
            # Preprocess

            kwargs = {}
            analysis_config = config.get('analysis', {})
            if 'prune_mark' in analysis_config:
                kwargs['prune_mark'] = analysis_config['prune_mark']
            if 'prune_buffer' in analysis_config:
                kwargs['prune_buffer'] = analysis_config['prune_buffer']

            preprocess_scaphandre(f'{directory}/power.json', f'{directory}/power_processed.json', f'{directory}/timesheet.json', **kwargs)

            # DF Conversion
            json_data = read_json(f"{directory}/power_processed.json")
            converter = ScaphandreToDf(json_data)
            converter.host_to_df()

            if config['analysis']['mode'] == 'pid':
                rpid = read_file(f"{directory}/rpid.txt")
                pids = resolve(f"{directory}/ptrace.txt", rpid)
                converter.pid_to_dfs(pids)
            else:
                converter.regex_to_dfs(config['analysis']['regex'])
            
            create_directory(f"{directory}/dfs")
            converter.export_dfs(f"{directory}/dfs")
            host_dfs.append(converter.dfs['host'])

            # Analysis
            analysis = Analysis(converter.dfs, config['procedure']['internal_repetitions'])
            analysis.do()
            write_json(f"{directory}/analysis.json", analysis.results)
            accumulated[i] = analysis.results

        # Analyze Multiple
        if config['procedure']['external_repetitions'] > 1:
            df = analyze_multiple_runs(accumulated)
            dfs.append(df)
            summary = df.describe()
            summary.to_csv(f"{config['out']}/{display_name}/summary.csv")
            summaries.append(summary)

        host_power_dfs.append(host_dfs)

    # Compare Variations
    if len(host_power_dfs) > 1:
        visualize_variations(dfs, host_power_dfs, config['out'])
        compare_variations(summaries, config['out'])
    
def analyze_multiple_runs(data):
    flattened_data = {outer_k: {f"{inner_k}_{k}": v for inner_k, inner_v in outer_v.items() for k, v in inner_v.items()} for outer_k, outer_v in data.items()}

    df = pd.DataFrame.from_dict(flattened_data, orient='index')

    df.columns = df.columns.str.replace('analysis_', '', regex=False)

    return df

SUMMARY_KEYS = [
    'host_energy_total', 'host_energy_per_repetition', 'process_energy_total',
    'process_energy_per_repetition', 'timestamp_running_time', 'host_power_mean'
]

def calculate_percentage_change(new_value, base_value):
    return round(((base_value - new_value) / base_value) * 100, 2)

def update_result_for_first_entry(result, summary, index):
    for key in SUMMARY_KEYS:
        result[key][index] = summary.loc['mean', key]

def update_result_for_subsequent_entries(result, summary, index):
    for key in SUMMARY_KEYS:
        new_value = summary.loc['mean', key]
        base_value = result[key][0]
        percentage_change = calculate_percentage_change(new_value, base_value)
        result[key][index] = [new_value, percentage_change]

def compare_variations(summaries, output_path):
    result = {key: {} for key in SUMMARY_KEYS}

    for i, summary in enumerate(summaries):
        if i == 0:
            update_result_for_first_entry(result, summary, i)
        else:
            update_result_for_subsequent_entries(result, summary, i)
    
    write_json(f"{output_path}/comparison.json", result)


def visualize_variations(dfs, host_power_dfs, output_path):
    boxplot(dfs, 'host_energy_total', f"{output_path}/host_energy_total.png")
    boxplot(dfs, 'timestamp_running_time', f"{output_path}/timestamp_running_time.png")
    boxplot(dfs, 'host_power_mean', f"{output_path}/host_power_mean.png")
    boxplot(dfs, 'process_energy_total', f"{output_path}/process_energy_total.png")

    for i, set in enumerate(host_power_dfs):
        power_plot(set, f"{output_path}/host_power_{i}.png")

if __name__ == '__main__':
    run("test.yaml")
