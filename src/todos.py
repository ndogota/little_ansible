import os
import yaml


def check_format(file_name, data):
    for module in data:
        if "module" not in module:
            print("Error - Bad file syntax : " + file_name + " use <module> as the main key on the yaml.")
            return False
    return True


def todos(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            if check_format(file_name, data):
                return data
    else:
        print("Error - File : " + file_name + " doesnt exit.")
