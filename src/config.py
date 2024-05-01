import yaml
from schema import Schema, SchemaError

config_schema = Schema({
    "images": [str],
    "measurement_engine": str,
    "procedure":
        {"repititions": int}
    })

def load_configuration(config_path):
    with open(config_path) as file:
        config = yaml.safe_load(file)

        try:
            config_schema.validate(config)
        except SchemaError as se:
            raise se

        return config
