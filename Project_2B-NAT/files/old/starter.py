#!/usr/bin/env python3
import random
from typing import Tuple
from threading import Thread
from scapy.packet import Packet
from scapy.sendrecv import send, sniff
from scapy.layers.inet import TCP, IP, Ether, ICMP

PRIVATE_IFACE = "eth0"
PRIVATE_IP = "10.0.0.2"

PUBLIC_IFACE = "eth1"
PUBLIC_IP = "172.16.20.2"

# Use "icmp" to test icmp only
# Use "tcp port 80" to test tcp only
FILTER = "icmp or tcp port 80"

# COPY NATTable HERE
class NATTable:
    pass

icmp_mapping = NATTable()
tcp_mapping = NATTable()

def process_pkt_private(pkt: Packet):   
    print("received pkt from private interface", pkt.sniffed_on, pkt.summary())

    pkt[Ether].src      # accessing a field in the Ether Layer, not necessary for this lab

    # https://github.com/secdev/scapy/blob/v2.4.5/scapy/layers/inet.py#L502
    pkt[IP].src         # accessing a field in the IP Layer

    try:
        # https://github.com/secdev/scapy/blob/v2.4.5/scapy/layers/inet.py#L874
        pkt[ICMP].id    # accessing a field in the ICMP Layer, will fail in a TCP packet
    
        # https://github.com/secdev/scapy/blob/v2.4.5/scapy/layers/inet.py#L678
        pkt[TCP].sport  # accessing a field in the TCP Layer, will fail in a ICMP packet
    except:
        pass

    # https://scapy.readthedocs.io/en/latest/usage.html#stacking-layers
    # Stack a new packet like so
    # IP(src="xxx.xxx.xxx.xxx", dst="xxx.xxx.xxx.xxx", ttl=???) / ptk[TCP or ICMP, depends on pkt]

    if ICMP in pkt:
        print('\tICMP Packet captured on private interface')
        # remember: icmp does not handle ports
        # src, id = icmp_mapping.set(src, id)

    elif TCP in pkt:
        print('\tTCP Packet captured on private interface')
        # src, port = tcp_mapping.set(src, port)

    # create a new pkt depending on what is being requested
    # keep track of new and current connections inside a data structure

    # make sure to send new packet to the correct network interface
    # send(new_pkt, iface=PUBLIC_IFACE, verbose=False)


def process_pkt_public(pkt: Packet):
    if pkt[IP].src == PUBLIC_IP:
        return # skip unecessary packets
    
    # almost the same as the function before
    # dst, port = tcp_mapping.get(src, port)
    pass

def private_listener():
    print("sniffing packets on the private interface")
    sniff(prn=process_pkt_private, iface=PRIVATE_IFACE, filter=FILTER)


def public_listener():
    print("sniffing packets on the public interface")
    sniff(prn=process_pkt_public, iface=PUBLIC_IFACE, filter=FILTER)


def main():
    thread1 = Thread(target=private_listener)
    thread2 = Thread(target=public_listener)

    print("starting multiple sniffing threads...")
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()


main()
