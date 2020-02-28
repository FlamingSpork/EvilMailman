from detcord import display, action

env = {}
hosts = []
for i in range(11):
    hosts.append("10.{}.3.20".format(str(i)))
    hosts.append("10.{}.3.30".format(str(i)))
    hosts.append("10.{}.3.40".format(str(i)))
env['hosts'] = hosts
env['user'] = 'hannibal'
env['pass'] = 'N3xtGenH@ck3r101'

@action
def DropIt(host):
    host.put("installer.sh", "/tmp/installer.sh")
    try:
        ret1 = host.run("chmod +x /tmp/installer.sh")
    except PermissionError as _:
        ret1 = host.run("chmod +x /tmp/installer.sh", sudo=True)
    ret2 = host.run("bash /tmp/installer.sh", sudo=True)