import json

def correct_json(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip()

    parts = content.split('}{')

    corrected_content = '[' + '},{'.join(parts) + ']'

    with open('out/corrected_output.json', 'w') as file:
        file.write(corrected_content)

    return corrected_content

# corrected_json = correct_json('path_to_your_malformed_json_file.json')
# print("JSON corrected and saved to 'corrected_file.json'")
