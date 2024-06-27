from analysis import Analysis
from preprocess import preprocess_scaphandre
from process_ptrace import resolve
from to_df import ScaphandreToDf
from misc.config import load_configuration
from misc.util import read_json, get_display_name, read_file, create_directory, write_json

def run(config_path):
    config = load_configuration(config_path)
    
    for image in config['images']:
        display_name = get_display_name(image)
        print(f"Running analysis for {display_name}")
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

            # Analysis
            analysis = Analysis(converter.dfs, config['procedure']['internal_repetitions'])
            analysis.do()
            write_json(f"{directory}/analysis.json", analysis.results)
    
def analyze_multiple():
    pass

if __name__ == '__main__':
    run("test.yaml")
