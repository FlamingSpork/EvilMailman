"""
Due to how DNS works, it allows for much more robust beaconing, but there's tradeoffs
Requirements:
    Python 3
    dnslib module (pip install dnslib)
"""

from dnslib import *
from dnslib.server import *
from time import sleep

def perChar(letter):
    if ord(letter) - 32 < 10:
        return "0" + str(ord(letter)-32)
    else:
        return str(ord(letter)-32)

def encodeCmd(cmd):
    output = ""
    for ch in cmd:
        output += perChar(ch)
    return output

class MemeResolver:
    def resolve(self,request,handler):
        reply = request.reply()
        qname = request.get_q().get_qname()
        print("Qname:", str(qname))
        print("type:", type(qname))
        response = "asdf"
        reply.add_answer(*RR.fromZone(str(qname) + " 60 IN MX 10 "+response+"."))
        print(reply)
        return reply

def main():
    resolver = MemeResolver()
    server = DNSServer(resolver, port=53, address="localhost", tcp=False)
    server.start_thread()
    try:
        while 1:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

main()