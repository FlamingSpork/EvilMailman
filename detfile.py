from detcord import display, action

env = {}
env['hosts'] = ['192.168.1.2']
env['user'] = 'root'
env['pass'] = 'toor'

@action
def DropIt(host):
    host.put("installer.sh", "/tmp/installer.sh")
    try:
        ret1 = host.run("chmod +x /tmp/installer.sh")
    except PermissionError as _:
        ret1 = host.run("chmod +x /tmp/installer.sh", sudo=True)
    ret2 = host.run("bash /tmp/installer.sh", sudo=True)