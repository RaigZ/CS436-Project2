#!/usr/bin/env python3
import random
from typing import Tuple
from threading import Thread
from scapy.packet import Packet, Raw
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

    def __init__(self):
    # NAT translation table ... DONE
    # = WORK HERE = ... DONE
    # IMPLEMENT THIS ... DONE
        self.data = {}
    
    def _random_id(self):
        return random.randint(30001, 65535)

    def set(self, ip_src, id_src) -> Tuple[str, int]:

        new_ip_src = PUBLIC_IP #this is the WAN connection so it should be public so everyone will see it

        wanList = list(self.data.keys())
        lanList = list(self.data.values())

        lan_tup = (ip_src, id_src) ##create a dummy tuple to see if its in the list of lanAddresses and Ports
        if lan_tup in lanList:
            i = lanList.index(lan_tup)        #Get index of the tuple location 
            new_id_src =wanList[i][1]   #retrieve corresponding wan port number and set it as the port number for same key/value
        else:
            new_id_src = self._random_id()  #if not found, just make a random port number
        
        wan_tup = (new_ip_src, new_id_src)


        self.data.update({wan_tup: lan_tup}) #Append the whole thing in one big dictionary

        return new_ip_src, new_id_src


    def get(self, ip_dst, id_dst) -> Tuple[str, int]:
        valsList = list(self.data.values()) ##seperate values from the list
        list_len = len(valsList)

        ip_src = valsList[list_len-1][0]
        id_src = valsList[list_len-1][1]    
        return ip_src, id_src


icmp_mapping = NATTable()
tcp_mapping = NATTable()

def process_pkt_private(pkt: Packet):   
    print("received pkt from private interface", pkt.sniffed_on, pkt.summary())
    #incoming
    #if its outgoing, use NAT Table
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
    # if its outgoing, look at the two things below
    if ICMP in pkt:
        print('\tICMP Packet captured on private interface')
        
        # Get packet src IP and ICMP id
        src_ip = pkt[IP].src
        src_id = pkt[ICMP].id
        
        # Add it into icmp_mapping, if it doesn't already exist
        # remember: icmp does not handle ports
        src_pub_ip, _ = icmp_mapping.set(src_ip, src_id)
        # Make new packet by updating Network Layer header, using public IP, public src (the ICMP id), and info from pkt
        dst_ip = pkt[IP].dst
        new_pkt = IP(src=src_pub_ip, dst=dst_ip) / pkt[ICMP]
        print(pkt[IP].summary())

    elif TCP in pkt:
        print('\tTCP Packet captured on private interface')

        # Get packet src IP and TCP source port
        
        src_ip = pkt[IP].src
        src_port = pkt[TCP].sport

        # remember: TCP does handle ports

        # Add it into icmp_mapping, if it doesn't already exist
        src_pub_ip, pub_sport = tcp_mapping.set(src_ip, src_port)

        # UNDERSTAND: don't worry about internal, sending only private packets to public packets
        # NEW TCP HEADER PASS SRC PORT AND DST PORT
        # SAVE MESSAGE
        # CAPTURE ANY APPLICATION LAYER PACKETS
        dst_port = pkt[TCP].dport
        tcp_header = TCP(sport=pub_sport, dport=dst_port) # transport layer header
        dst_ip = pkt[IP].dst

        ##### creation of new_pkt needs application layer (pkt[Raw] will not work!) #####
        new_pkt = IP(src=src_pub_ip, dst=dst_ip) / tcp_header / pkt[Raw] # Change this: pkt[Raw]

    # create a new pkt depending on what is being requested
    # keep track of new and current connections inside a data structure

    # make sure to send new packet to the correct network interface
    send(new_pkt, iface=PUBLIC_IFACE, verbose=False)


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