import json

def read(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip()
    return content
    
def write(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def prune(content):
    return content[0:content.rindex('{"host"')]

def correct_format(content):
    parts = content.split('}{')

    corrected_content = '[' + '},{'.join(parts) + ']'

    return corrected_content
