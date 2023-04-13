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
            return "Request timed out.", 0, 0

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        icmpType, code, checksum, pID, sequence = struct.unpack("bbHHh", icmpHeader)

        ip_header = recPacket[:20]
        version, ihl, tos, total_length, identification, flags, fragment_offset, ttl, protocol, header_checksum, src_addr, dest_addr = struct.unpack("!BBHHHBBHII", ip_header)

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0 or pID != ID or icmpType != 0:
            return "Request timed out.", 0, 0
        else:
            bytes_received = len(recPacket)
            return howLongInSelect * 1000, bytes_received, ttl


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
    print("\nPinging " + dest + " using Python:")
    print("")

    response = pd.DataFrame(columns=['bytes', 'rtt', 'ttl'])

    for i in range(0, 4):
        delay, bytes_recv, ttl = doOnePing(dest, timeout)
        if delay != "Request timed out.":
            response = response.append({'bytes': bytes_recv, 'rtt': delay, 'ttl': ttl}, ignore_index=True)
        print(delay)
        time.sleep(1)

    packet_lost = 0
    packet_recv = 0

    for index, row in response.iterrows():
        if row['bytes'] == 0:
            packet_lost += 1
        else:
            packet_recv += 1

    vars = pd.DataFrame(columns=['min', 'avg', 'max', 'stddev'])
    vars = vars.append({'min': str(round(response['rtt'].min(), 2)), 'avg': str(round(response['rtt'].mean(), 2)),
                        'max': str(round(response['rtt'].max(), 2)), 'stddev': str(round(response['rtt'].std(), 2))}, ignore_index=True)
    print(vars)
    return vars


if __name__ == '__main__':
    ping("google.com")


