import argparse
import socket
import struct
import random
import time

ECHO_REQUEST = 8

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", metavar="payload", help="the string to include in the payload", type=str)
    parser.add_argument("-c", metavar="count", help="the number of packets used to compute RTT, default 10", type=int)
    parser.add_argument("-d", metavar="dst", help="the destination IP for the ping message", type=str)
    parser.add_argument("-l", metavar="logfile", help="log file", type=str)

    args = parser.parse_args()
    if not args.p or not args.d:
        print("Please enter the command as follows:")
        print("\tpinger.py -p payload -c count -d dst -l logfile")
        print("where")
        print("\t-p payload\tthe string to include in the payload")
        print("\t-c count\tthe number of packets used to compute RTT, default 10 (OPTIONAL)")
        print("\t-d dst\tthe destination IP for the ping message")
        print("\t-l logfile\tlog file (OPTIONAL)")
        exit()
    if not args.c:
        args.c = 10
    return args


def write_to_log(logfile, msg):
    log_file = open(logfile, 'a')
    log_file.write(msg + '\n')
    log_file.close()


class Pinger:

    def __init__(self):
        self.args = parse_args()
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
            self.socket.settimeout(4)

        except socket.error, msg:
            print("Error: could not create raw socket, Error Code: " + str(msg[0]) + " Message: " + str(msg[1]))
            print("Note: ICMP messages can only be sent from processes running as root ")
            exit()

        if self.args.l:
            log_file = open(self.args.l, 'w')
            log_file.close()

        # tracking variables
        self.sent = 0
        self.received = 0
        self.rtt = []
        self.get_dst_addr()
        self.run()

    def get_dst_addr(self):
        # convert dst to dst addr if its not already
        temp = self.args.d.split(".")
        is_addr = True
        for s in temp:
            if not s.isdigit():
                is_addr = False
                break
        if not is_addr:
            self.args.d = socket.gethostbyname(self.args.d)
            if not self.args.d:
                print("Destination not valid")
                exit()

    def run(self):
        random.seed(time.time())
        msg = "Pinging {} with {} bytes of data \"{}\"".format(self.args.d, len(self.args.p), self.args.p)
        print(msg)
        if self.args.l:
            write_to_log(self.args.l, msg)

        for i in range(self.args.c):
            # make random id to check
            packet_id = (random.randint(0, (2**16 - 1)))
            packet = self.make_packet(self.args.p, packet_id, i)

            self.sent += 1
            self.socket.sendto(packet, (self.args.d, 1))

            send_time = time.time()
            self.receive_ping(send_time, i)
        print("Ping statistics for {}:".format(self.args.d))
        print("Packets: Sent = {}, Received = {}, Lost = {} ({}% loss)"
              .format(self.sent, self.received, self.sent-self.received,
                      round(((self.sent-self.received)/float(self.sent))*100, 1)))
        print("Approximate round trip times in millis-seconds:")
        print("Minimum = {}ms, Maximum = {}ms, Average = {}ms"
              .format(min(self.rtt), max(self.rtt), sum(self.rtt)/len(self.rtt)))

    def receive_ping(self, send_time, seq):
        try:
            packet, addr = self.socket.recvfrom(1024)
            rec_time = time.time()
            payload_size = len(packet[28:])
            time_diff = round((rec_time - send_time) * 1000, 3)

            # ip header
            ip_header = struct.unpack('BBHHHBBH4s4s', packet[:20])

            # icmp header
            icmp_header = struct.unpack("bbHHh", packet[20:28])

            msg = "Reply from {}: bytes={} time={}ms TTL={}".format(addr[0], payload_size, time_diff, ip_header[5])
            print(msg)
            if self.args.l:
                write_to_log(self.args.l, msg)
                write_to_log(self.args.l, "ip header:" + str(ip_header))
                write_to_log(self.args.l, "icmp header:" + str(icmp_header))
                write_to_log(self.args.l, "payload received: " + packet[28:])
            self.received += 1
            self.rtt.append(time_diff)

        except socket.timeout:
            msg = "Request timeout for icmp_seq " + str(seq)
            print(msg)
            if self.args.l:
                write_to_log(self.args.l, msg)

    def make_packet(self, msg, identifier, seq):
        # 64 bit header: type(8), code(8), checksum(16), id(16), sequence(16)
        header = struct.pack("bbHHh", ECHO_REQUEST, 0, 0, identifier, seq)
        checksum = self.checksum(header + msg)
        header = struct.pack("bbHHh", ECHO_REQUEST, 0, socket.htons(checksum), identifier,  seq)
        if self.args.l:
            write_to_log(self.args.l, "Sending packet size {}".format(len(header + msg)))
            write_to_log(self.args.l, "icmp packet: " + str((ECHO_REQUEST, 0, socket.htons(checksum), identifier, seq, msg)))
        return header + msg

    def checksum(self, msg):
        sum = 0
        # loop taking 2 characters at a time
        for i in range(0, len(msg), 2):
            w = ord(msg[i]) + (ord(msg[i + 1]) << 8) if i + 1 < len(msg) else ord(msg[i])
            sum = sum + w
        sum = (sum >> 16) + (sum & 0xffff)
        sum = sum + (sum >> 16)
        sum = ~sum & 0xffff
        sum = sum >> 8 | (sum << 8 & 0xff00)
        return sum


def main():
    pinger = Pinger()


if __name__ == "__main__":
    main()