import json

def correct_json(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip()

    parts = content.split('}{')

    corrected_content = '[' + '},{'.join(parts) + ']'

    with open('out/corrected_output.json', 'w') as file:
        file.write(corrected_content)

    return corrected_content

def 