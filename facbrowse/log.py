import socket

from datetime import datetime


def add_to_log(message):
    with open("/data/logs/facbrowse_log." +
              socket.gethostname().split(".")[0], "a") as f:
        f.write(str(datetime.now()) + " " + message + "\n")
