"""
TBH, this could be called cargocult.py because that's what it is
"""

import asyncore
import asynchat
import socket
import time
import errno
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
        self.push("250 WORDS")
    # def smtp_RCPT(self, arg):
    #     self.push("250 NANI?")

class MailmanServer(SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print("Message received from: ", mailfrom)
        print("Data: ", data)

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


def run():
    foo = MailmanServer(("localhost", 25), None)
    print("Server launched")
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass

run()