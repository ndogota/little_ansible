import os
import yaml

ssh_argument = ["ssh_address", "ssh_port", "ssh_user", "ssh_password", "ssh_key_file"]


def check_format(file_name, data):
    # have to check if we have required arguments (cleanly)
    if "hosts" not in data:
        print("Error - Bad file syntax : " + file_name + " use <hosts> as the main key on the yaml.")
        return False

    for host in data["hosts"]:
        for argument in data["hosts"][host]:
            if argument not in ssh_argument:
                print("Error - Bad file syntax : " + file_name + " use <ssh_address>, <ssh_port>, <ssh_user>, "
                                                                 "<ssh_password> or <ssh_key_file> as arguments.")
                return False

    return True


def inventory(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            if check_format(file_name, data):
                return data
    else:
        print("Error - File : " + file_name + " doesnt exit.")
