import yaml
from schema import Schema, SchemaError, And, Optional, Or

def validation_logic(data):
    if data['analysis'].get('mode') == 'regex' and 'pattern' not in data['analysis']:
        raise SchemaError("Regex analysis mode requires a pattern field")

    external_repetitions = data['procedure']['external_repetitions']
    num_images = len(data['images'])

    if isinstance(external_repetitions, list):
        if len(external_repetitions) != num_images:
            raise SchemaError(f"When external_repetitions is a list, its length ({len(external_repetitions)}) must match the number of images ({num_images})")

    return True

config_schema = Schema(And({
    "images": [str],
    "out": str,
    "procedure":{
        "external_repetitions": Or(int, [int]),
        "internal_repetitions": int,
        "freq": int,
        Optional("cooldown"): int,
        Optional("scaph_warmup"): int,
        Optional("experiment_warmup"): int
        },
    "analysis": {
        Optional("mode"): And(lambda x: x in ['regex', 'pid']),
        Optional("pattern"): str,
        Optional("prune_mark"): str,
        Optional("prune_buffer"): str
    }},
    validation_logic
    ))

def load_configuration(config_path):
    with open(config_path) as file:
        config = yaml.safe_load(file)

        try:
            config_schema.validate(config)
        except SchemaError as se:
            raise se

        if isinstance(config['procedure']['external_repetitions'], int):
            num_images = len(config['images'])
            repetitions = config['procedure']['external_repetitions']
            config['procedure']['external_repetitions'] = [repetitions] * num_images

        return config
