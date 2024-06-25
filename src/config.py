import yaml
from schema import Schema, SchemaError, And, Optional

def validate_regex(data):
    if data['analysis']['mode'] == 'regex' and 'pattern' not in data['analysis']:
        raise SchemaError("Regex analysis mode requires a pattern field")

    return True

config_schema = Schema(And({
    "images": [str],
    "out": str,
    "procedure":{
        "external_repetitions": int,
        "internal_repetitions": int,
        "freq": int,
        "cooldown": int 
        },
    "analysis": {
        Optional("mode"): And( lambda x: x in ['regex', 'pid']),
        Optional("pattern"): str,
        Optional("prune_mark"): str,
        Optional("prune_buffer"): str
    }},
    validate_regex
    ))

def load_configuration(config_path):
    with open(config_path) as file:
        config = yaml.safe_load(file)

        try:
            config_schema.validate(config)
        except SchemaError as se:
            raise se

        return config
