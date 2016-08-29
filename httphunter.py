#!/usr/bin/env python
# coding:utf-8
# Author: croxy

import re
import sys
import Queue
import threading
import optparse
import httplib
import random

printLock = threading.Semaphore(1)  # lock Screen print
TimeOut = 5  # request timeout

# User-Agent
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36',
    'Connection': 'close'}


class scan():
    def __init__(self, ip, threads_num):
        self.threads_num = threads_num
        self.ip = ip
        self.lock = threading.Lock()
        self.IPs = Queue.Queue()
        self.getnetwork()

    def getnetwork(self):
        ip = self.ip;
        targetip = listCIDR(ip)
        for i in range(len(targetip)):
            self.IPs.put(targetip[i])

    def request(self):
        with threading.Lock():
            while self.IPs.qsize() > 0:
                ip = self.IPs.get()
                #print ip
                try:
                    c = httplib.HTTPConnection(ip,timeout=TimeOut)
                    c.request('GET','/')
                    r2 = c.getresponse()
                    status = r2.status
                    text = r2.read()
                    c.close()
                    title = re.search(r'<title>(.*)</title>', text)  # get the title
                    if title:
                        title = title.group(1).strip().strip("\r").strip("\n")[:30]
                    else:
                        title = "None"
                    banner = ''
                    try:
                        banner += r2.getheader('Server')  # get the server banner
                    except:
                        pass
                    printLock.acquire()
                    print "\t   %s        %s        %s        %s\t" % (ip, status, banner, title),
                    #print ''
                    # Save log
                    with open("./log/" + self.ip[:-3]+'-'+ self.ip[-2:]+ ".log", 'a') as f:
                        f.write(ip + '\t' + str(status)+ '\t' + banner + '\t' + title+"\n")
                        f.close()

                except Exception, e:
                    #print e
                    printLock.acquire()
                finally:
                    printLock.release()

    # Multi thread
    def run(self):
        for i in range(self.threads_num):
            t = threading.Thread(target=self.request)
            t.start()




# convert an IP address from its dotted-quad format to its
# 32 binary digit representation
def ip2bin(ip):
	b = ""
	inQuads = ip.split(".")
	outQuads = 4
	for q in inQuads:
		if q != "":
			b += dec2bin(int(q),8)
			outQuads -= 1
	while outQuads > 0:
		b += "00000000"
		outQuads -= 1
	return b

# convert a decimal number to binary representation
# if d is specified, left-pad the binary number with 0s to that length
def dec2bin(n,d=None):
	s = ""
	while n>0:
		if n&1:
			s = "1"+s
		else:
			s = "0"+s
		n >>= 1
	if d is not None:
		while len(s)<d:
			s = "0"+s
	if s == "": s = "0"
	return s

# convert a binary string into an IP address
def bin2ip(b):
	ip = ""
	for i in range(0,len(b),8):
		ip += str(int(b[i:i+8],2))+"."
	return ip[:-1]

# print a list of IP addresses based on the CIDR block specified
def listCIDR(c):
	cidrlist=[]
	parts = c.split("/")
	baseIP = ip2bin(parts[0])
	subnet = int(parts[1])
	# Python string-slicing weirdness:
	# "myString"[:-1] -> "myStrin" but "myString"[:0] -> ""
	# if a subnet of 32 was specified simply print the single IP
	if subnet == 32:
		 bin2ip(baseIP)
	# for any other size subnet, print a list of IP addresses by concatenating
	# the prefix with each of the suffixes in the subnet
	else:
		ipPrefix = baseIP[:-(32-subnet)]
		for i in range(2**(32-subnet)):
			cidrlist.append(bin2ip(ipPrefix+dec2bin(i, (32-subnet))))
		return cidrlist


if __name__ == "__main__":
    parser = optparse.OptionParser("Usage: %prog [options] 192.168.1.1/24")
    parser.add_option("-t", "--thread", dest="threads_num",
                      default=10, type="int",
                      help="[optional]number of    theads,default=10")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    print "\t   ip        status        banner        title\t"
    s = scan(ip=args[0], threads_num=options.threads_num)
    s.run()
