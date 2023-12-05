import os
import logging

from enum import Enum


class LogType(Enum):
    PROCESS = "process"
    TASK = "task"
    DONE = "done"
    STATUS = "status"


class Status(Enum):
    OK = "ok"
    KO = "ko"
    CHANGED = "changed"


def log(log_type, hosts=None, task_count=None, op_data=None):
    # improve the function for using "task" and "status" mode independently
    user = os.getlogin()
    logging.basicConfig(format='%(asctime)s - ' + user + ' - %(message)s', level=logging.INFO)

    if log_type.value == "process":
        logging.info("INFO - processing " + task_count + " task(s) on host(s): " + ", ".join(hosts))
    elif log_type.value == "task" or log_type.value == "status":
        logging.info("INFO - " + op_data)
    elif log_type.value == "done":
        logging.info("INFO - done processing tasks for hosts: " + ", ".join(hosts))

    # Type checking
    if not isinstance(log_type, LogType):
        raise TypeError('log_type must be an instance of LogType Enum')


def get_hosts(inventory_yaml):
    hosts = []

    for host in inventory_yaml["hosts"]:
        hosts.append(inventory_yaml["hosts"][host]["ssh_address"])

    return hosts
