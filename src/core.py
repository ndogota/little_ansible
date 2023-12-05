import src.utils
import paramiko
import os
import getpass

from paramiko.client import SSHClient, AutoAddPolicy
from jinja2 import Environment, FileSystemLoader


# copy all files and folders of a specific local path to a remote path
def copy_all(ssh_client, local_file_path, remote_file_path):
    status = src.utils.Status.CHANGED
    sftp = ssh_client.open_sftp()

    os.chdir(os.path.split(local_file_path)[0])
    parent = os.path.split(local_file_path)[1]

    # check if the folder exist
    if not remotely_exist(sftp, remote_file_path):
        sftp.mkdir(remote_file_path)

    for path, directories, files in os.walk(parent):
        for directory in directories:
            if remote_file_path[0] == '/':
                if not remotely_exist(sftp, "/" + path + "/" + directory):
                    sftp.mkdir(remote_file_path.rsplit('/', 1)[0] + "/" + path + "/" + directory)
                    status = src.utils.Status.OK
            else:
                if not remotely_exist(sftp, path + "/" + directory):
                    sftp.mkdir(remote_file_path.rsplit('/', 1)[0] + path + "/" + directory)
                    status = src.utils.Status.OK
        for file in files:
            if remote_file_path[0] == '/':
                sftp.put(path + "/" + file, remote_file_path.rsplit('/', 1)[0] + "/" + path + "/" + file)
                status = src.utils.Status.OK
            else:
                sftp.put(path + "/" + file, remote_file_path.rsplit('/', 1)[0] + "/" + path + "/" + file)
                status = src.utils.Status.OK

    sftp.close()
    return status


# check if the folder or file exist remotely
def remotely_exist(sftp, path):
    try:
        sftp.stat(path)
        return True
    except FileNotFoundError:
        return False


# copy function using yaml configuration <todos.yaml>
def copy(ssh_client, ssh_address, params, index, dry_run):
    src_path = params["src"]
    dest_path = params["dest"]
    # TODO - what does at mean ?
    backup = params["backup"]
    backup_path = "/home/user/backup"

    src.utils.log(src.utils.LogType.TASK, op_data="[" + index + "] host=" + ssh_address +
                                                  " op=copy src=" + src_path +
                                                  " dest=" + dest_path +
                                                  " backup=" + str(backup))

    if dry_run:
        return src.utils.Status.OK

    if backup:
        copy_all(ssh_client, src_path, "backup")

    # returning status of copying
    return copy_all(ssh_client, src_path, dest_path)


# template function using yaml configuration <todos.yaml>
def template(ssh_client, ssh_address, params, index, dry_run):
    src.utils.log(src.utils.LogType.TASK, op_data="[" + index + "] host=192.168.1.22 op=apt name=nginx-common "
                                                                "state=present")
    src_path = params["src"]
    dest_path = params["dest"]
    listen_port = params["vars"]["listen_port"]
    server_name = "localhost"

    if dry_run:
        return src.utils.Status.OK

    if "server_name" in params["vars"]:
        server_name = params["vars"]["server_name"]

    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template(src_path)

    rendered_template = template.render(listen_port=listen_port, server_name=server_name)

    with open('default.conf', 'w') as f:
        f.write(rendered_template)

    sftp = ssh_client.open_sftp()
    sftp.put(src_path[:-3], dest_path + src_path[:-3])
    sftp.close()

    os.remove(src_path[:-3])

    return src.utils.Status.OK


# service function using yaml configuration <todos.yaml>
def service(ssh_client, ssh_address, params, index, password, debug, dry_run):
    src.utils.log(src.utils.LogType.TASK, op_data="[" + index + "] host=192.168.1.22 op=apt name=nginx-common "
                                                                "state=present")

    if dry_run:
        return src.utils.Status.OK

    name = params["name"]
    state = check_state(params["state"])

    if state is False:
        return src.utils.Status.KO

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command("echo '" + password + "' | sudo -S systemctl " + state + " " + name)

    if ssh_stdout.channel.recv_exit_status() != 0:
        if debug:
            print(ssh_stderr.read().decode())
        return src.utils.Status.KO

    return src.utils.Status.OK


def check_state(state):
    if state == "started":
        return "start"
    elif state == "restarted":
        return "restart"
    elif state == "stopped":
        return "stop"
    elif state == "enabled":
        return "enable"
    elif state == "disabled":
        return "disable"
    else:
        return False


# sysctl function using yaml configuration <todos.yaml>
def sysctl(ssh_client, ssh_address, params, index, debug, dry_run):
    src.utils.log(src.utils.LogType.TASK, op_data="[" + index + "] host=192.168.1.22 op=apt name=nginx-common "
                                                                "state=present")

    if dry_run:
        return src.utils.Status.OK

    attribute = params["attribute"]
    value = params["value"]
    permanent = params["permanent"]

    if permanent is False:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command("echo user | sudo -S sysctl -w " + attribute + "=" + str(value))

        if ssh_stdout.channel.recv_exit_status() != 0:
            if debug:
                print(ssh_stderr.read().decode())
            return src.utils.Status.KO
    elif permanent is True:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command("echo user | sudo -S echo \"\'" + attribute + "=" + str(value) + "\' >> /etc/sysctl.conf\"")
        if ssh_stdout.channel.recv_exit_status() != 0:
            if debug:
                print(ssh_stderr.read().decode())
            return src.utils.Status.KO
    else:
        return src.utils.Status.KO

    return src.utils.Status.OK


# apt function using yaml configuration <todos.yaml>
def apt(ssh_client, ssh_address, params, index, password, debug, dry_run):
    name = params["name"]
    state = params["state"]

    src.utils.log(src.utils.LogType.TASK, op_data="[" + index + "] host=" + ssh_address + " op=apt name=" + name +
                                                  " state=" + state)
    if dry_run:
        return src.utils.Status.OK

    if state == "present":
        apt_install(ssh_client, name, password, debug)
    elif state == "absent":
        apt_remove(ssh_client, name, password, debug)
    else:
        return src.utils.Status.KO

    return src.utils.Status.OK


def apt_install(ssh_client, package, password, debug):
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command("dpkg -l " + package)

    if ssh_stdout.channel.recv_exit_status() == 0:
        return src.utils.Status.CHANGED

    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "echo " + password + " | sudo -S apt-get install " + package + " -y")

    if ssh_stdout.channel.recv_exit_status() != 0:
        if debug:
            print("error: ", ssh_stderr.read().decode())
        return src.utils.Status.KO


def apt_remove(ssh_client, package, password, debug):
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(
        "echo " + password + " | sudo -S apt-get remove " + package + " -y")

    if ssh_stdout.channel.recv_exit_status() != 0:
        if debug:
            print("error: ", ssh_stderr.read().decode())
        return src.utils.Status.KO


# command function using yaml configuration <todos.yaml>
def command(ssh_client, ssh_address, params, index, debug, dry_run):
    # TODO : - handle multiple commands

    cmd_list = list(filter(None, params["command"].split('\n')))
    shell = "/bin/bash"

    if "shell" in params:
        shell = params["shell"]

    for cmd in cmd_list:
        src.utils.log(src.utils.LogType.TASK, op_data="[" + index + "]"
                                                                    " host=" + ssh_address +
                                                      " op=command "
                                                      " cmd=" + cmd +
                                                      " shell=" + shell)

        if not dry_run:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)
            if ssh_stdout.channel.recv_exit_status() != 0:
                if debug:
                    print(ssh_stderr.read().decode())
                return src.utils.Status.KO
            '''
            else:
                print(ssh_stdout.read().decode())
            '''

    return src.utils.Status.OK


# processing modules using yaml configuration <todos.yaml>
def module_processing(ssh_client, ssh_address, todos_yaml, index, password, debug, dry_run):
    modules_status = []

    for module in todos_yaml:
        if "copy" in module["module"]:
            modules_status.append(copy(ssh_client, ssh_address, module["params"], index, dry_run))
        elif "template" in module["module"]:
            modules_status.append(template(ssh_client, ssh_address, module["params"], index, dry_run))
        elif "service" in module["module"]:
            modules_status.append(service(ssh_client, ssh_address, module["params"], index, password, debug, dry_run))
        elif "sysctl" in module["module"]:
            modules_status.append(sysctl(ssh_client, ssh_address, module["params"], index, debug, dry_run))
        elif "apt" in module["module"]:
            modules_status.append(apt(ssh_client, ssh_address, module["params"], index, password, debug, dry_run))
        elif "command" in module["module"]:
            modules_status.append(command(ssh_client, ssh_address, module["params"], index, debug, dry_run))

    return modules_status


# processing ssh connections using yaml configuration <todos.yaml>
def ssh(ssh_client, ssh_address, inventory_yaml, host, ssh_port=22):
    if "ssh_user" and "ssh_password" in inventory_yaml["hosts"][host]:
        ssh_user = inventory_yaml["hosts"][host]["ssh_user"]
        ssh_password = inventory_yaml["hosts"][host]["ssh_password"]

        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(ssh_address, username=ssh_user, password=ssh_password, port=ssh_port)
    elif "ssh_key_file" in inventory_yaml["hosts"][host]:
        ssh_user = inventory_yaml["hosts"][host]["ssh_user"]
        ssh_password = inventory_yaml["hosts"][host]["ssh_password"]
        ssh_key_file = inventory_yaml["hosts"][host]["ssh_key_file"]

        ssh_client.connect(ssh_address, username=ssh_user, password=ssh_password,
                           key_filename=ssh_key_file)
    else:
        user = os.getlogin()

        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(ssh_address, username=user, port=ssh_port)
    return ssh_client


# logical core of this project using two yaml configuration files <inventory.yaml>, <todos.yaml> :
# - iterate through all host from the hosts files <inventory.yml>
# - creating an ssh connection for all of them
# - sending to the <module_processing> function the ssh connection with the todos configuration file <todos.yml>.
# each ssh connections run the different task from todos file.
def core(inventory_yaml, todos_yaml, debug, dry_run):
    hosts_status = []
    task_count = str(len(todos_yaml))
    hosts = src.utils.get_hosts(inventory_yaml)
    index_i = 0
    index_j = 0

    src.utils.log(src.utils.LogType.PROCESS, hosts=hosts, task_count=task_count)

    # processing each task of each module we have
    for host in inventory_yaml["hosts"]:
        ssh_client = SSHClient()

        ssh_address = inventory_yaml["hosts"][host]["ssh_address"]
        ssh_port = inventory_yaml["hosts"][host]["ssh_port"]

        ssh_password = None

        if inventory_yaml["hosts"][host]["ssh_password"]:
            ssh_password = inventory_yaml["hosts"][host]["ssh_password"]

        ssh_client = ssh(ssh_client, ssh_address, inventory_yaml, host, ssh_port=ssh_port)

        # adding each status of each module into <hosts_status> list
        hosts_status.append(module_processing(ssh_client, ssh_address, todos_yaml, str(index_i + 1), ssh_password, debug, dry_run))

        ssh_client.close()

        index_i += 1

    # reporting status of each host individually
    for host in inventory_yaml["hosts"]:
        ok = str(hosts_status[index_j].count(src.utils.Status.OK))
        changed = str(hosts_status[index_j].count(src.utils.Status.CHANGED))
        fail = str(hosts_status[index_j].count(src.utils.Status.KO))

        src.utils.log(src.utils.LogType.STATUS, hosts=hosts, op_data="host=" + inventory_yaml["hosts"][host][
            "ssh_address"] + " ok=" + ok + " changed=" + changed + " fail=" + fail)
        index_j += 1

    src.utils.log(src.utils.LogType.DONE, hosts=hosts)
