#!/usr/bin/env python3

import random
from scapy.sendrecv import send, sr1, sr
from scapy.layers.inet import TCP, IP

###### TCP
# https://github.com/secdev/scapy/blob/v2.4.5/scapy/layers/inet.py#L678
# pkt[TCP].sport  # accessing a field in the TCP Layer

ip_packet = IP(dst="info.cern.ch")
seq = random.randint(10000, 19999)      # Random initial seq number
syn_packet = TCP(flags='S', seq=seq)

# Making a HTTP request
sport = seq # Fill in the source port
dport = 80 # Fill in the destination port

syn_packet[TCP].sport = sport
syn_packet[TCP].dport = dport

# Encapsulate TCP syn packet inside IP packet
packet = ip_packet/syn_packet   # Construct the IP packet here used to send TCP SYN

# send and receive 1 packet (sr1)
synack_response = sr1(packet)

# TCP necessary steps
next_seq = synack_response.ack
my_ack = synack_response.seq + 1

ack_packet = TCP(sport=sport, dport=dport, flags='A', seq=next_seq, ack=my_ack)

# Encapsulate TCP ack packet inside IP packet
packet = ip_packet/ack_packet # Construct the IP packet here used to send TCP ACK

# send packet and do not wait for response
send(packet)

payload_packet = TCP(sport=sport, dport=dport, flags='A', seq=next_seq, ack=my_ack) / "GET / HTTP/1.1\r\nHost: info.cern.ch\r\n\r\n"

# Encapsulate TCP payload packet inside IP packet
packet = ip_packet/payload_packet # Construct the IP packet here used to send HTTP Get request

# send and receive multiple packets (sr)
reply, error = sr(packet, multi=1, timeout=1)

result = bytes(reply[-1][1][TCP].payload)

print(result.decode('utf-8'))
