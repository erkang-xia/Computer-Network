from socket import *
import os
import sys
import struct
import time
import select
import binascii
import pandas as pd
from socket import gethostbyname, gethostbyaddr, herror, AF_INET, SOCK_RAW, IPPROTO_ICMP, IPPROTO_IP, IP_TTL, htons


ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 1

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

def build_packet():
    myChecksum = 0
    myID = os.getpid() & 0xFFFF
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, myID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, htons(myChecksum), myID, 1)
    packet = header + data
    return packet



def get_route(hostname):
    timeLeft = TIMEOUT
    df = pd.DataFrame(columns=['Hop Count', 'Try', 'IP', 'Hostname', 'Response Code'])
    destAddr = gethostbyname(hostname)
    
    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            mySocket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)
            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)
            
            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t = time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)

                if not whatReady[0]:  # Timeout
                    df = df.append({
                        'Hop Count': ttl,
                        'Try': tries,
                        'IP': 'N/A',
                        'Hostname': 'N/A',
                        'Response Code': 'timeout'
                    }, ignore_index=True)
                    continue

                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect

                icmpHeader = recvPacket[20:28]
                types, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

                try:
                    hostName = gethostbyaddr(addr[0])[0]
                except herror:
                    hostName = "hostname not returnable"

                response = {
                    'Hop Count': ttl,
                    'Try': tries,
                    'IP': addr[0],
                    'Hostname': hostName,
                    'Response Code': f'ICMP {types}, {code}'
                }

                df = df.append(response, ignore_index=True)

                if addr[0] == destAddr:
                    print("Destination reached!")
                    return df
                elif timeLeft <= 0:
                    df = df.append({
                        'Hop Count': ttl,
                        'Try': tries,
                        'IP': 'N/A',
                        'Hostname': 'N/A',
                        'Response Code': 'timeout'
                    }, ignore_index=True)
                elif types not in [0, 3, 11]:
                    df = df.append({
                        'Hop Count': ttl,
                        'Try': tries,
                        'IP': addr[0],
                        'Hostname': hostName,
                        'Response Code': f'Unhandled ICMP type {types}'
                    }, ignore_index=True)
                    break

            except Exception as e:
                print(e)
                continue

    return df




if __name__ == '__main__':
    df = get_route("google.com")

