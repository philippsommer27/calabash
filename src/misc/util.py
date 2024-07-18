import json
import os

def get_display_name(image_name):
    return image_name[image_name.find('/')+1:]

def get_display_name_tagged(image_name):
    return image_name[image_name.find('/')+1:image_name.find(':')]  

def read_json(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)
    
def read_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip()
    return content

def write_json(file_path, content):
    with open(file_path, 'w') as file:
        json.dump(content, file, indent=4)

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
