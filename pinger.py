import os
import sys
import struct
import time
import select
import socket
from socket import getprotobyname, gethostbyname, AF_INET, SOCK_RAW
import pandas as pd


ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer



def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start

        # Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        icmpType, code, checksum, pID, sequence = struct.unpack("bbHHh", icmpHeader)
        #print("Header: ", icmpType, code, checksum, pID, sequence)


        # Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0 or pID != ID or icmpType != 0:
            return "Request timed out."
        else:
            return howLongInSelect *1000

def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)


    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str


    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")


    # SOCK_RAW is a powerful socket type. For more details:   https://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")

    delayRTT = []

    for i in range(0, 4):  # Four pings will be sent (loop runs for i=0, 1, 2, 3)
        delay = doOnePing(dest, timeout)
        print(delay)
        if delay != "Request timed out.":
            delayRTT.append(delay)
        time.sleep(1)  # one second

    if len(delayRTT) == 0:
        data = {'min': [0], 'avg': [0.0], 'max': [0], 'stddev': [0.0]}
    else:
        df = pd.DataFrame(delayRTT, columns=['RTT'])
        data = {
            'min': [df['RTT'].min()],
            'avg': [df['RTT'].mean()],
            'max': [df['RTT'].max()],
            'stddev': [df['RTT'].std()]
        }

    results = pd.DataFrame(data)
    print(results)
    return results

if __name__ == '__main__':
    # Test the pinger
    ping("127.0.0.1")
    ping("google.com")
    ping("nyu.edu")
