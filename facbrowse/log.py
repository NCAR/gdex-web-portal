import socket

from datetime import datetime


def add_to_log(message):
    host_parts = socket.gethostname().split(".")
    if "gdex-webserver" in host_parts:
        return

    with open("/data/logs/facbrowse_log." + host_parts[0], "a") as f:
        f.write(str(datetime.now()) + " " + message + "\n")