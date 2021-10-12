# Linux command df - report file system disk space usage
# Example:
# pi@raspberrypi ~ $ df -h /
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/root        30G  6.8G   22G  25% /
#
# This sample run "df -h /" in Python and get the result 
import os 

def getDfDescription():
    df = os.popen("df -h /")
    i = 0
    while True:
        i = i + 1
        line = df.readline()
        if i==1:
            return(line.split()[0:6])
                                 
def getDf():
    df = os.popen("df -h /")
    i = 0
    while True:
        i = i + 1
        line = df.readline()
        if i==2:
            return(line.split()[0:6])

# Disk information
description = getDfDescription()
disk_root = getDf()

print(disk_root)
print(description[0] + " : " + disk_root[0])
print(description[1] + " : " + disk_root[1])
print(description[2] + " : " + disk_root[2])
print(description[3] + " : " + disk_root[3])
print(description[4] + " : " + disk_root[4])
print(description[5] + " : " + disk_root[5])
