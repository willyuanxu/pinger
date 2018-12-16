Pinger is a ping tool to send periodic ping messages to the specified IP address or domain and compute the estimated RTT based on the received responses

Please run program with python 2.7
Please enter the command as follows:
sudo python pinger.py -p payload -c count -d dst -l logfile
        where
        -p payload      the string to include in the payload
        -c count        the number of packets used to compute RTT, default 10 (OPTIONAL)
        -d dst          the destination IP or domain name for the ping message
        -l logfile      log file (OPTIONAL)
