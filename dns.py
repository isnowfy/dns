 # -*- coding: UTF-8 -*-

import gevent
import dnslib
from gevent import socket
#import socket
from gevent import event

rev=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
rev.bind(('',53))
ip=[]
cur=0

def preload():
    for i in open('ip'):
        ip.append(i)
    print "load "+str(len(ip))+" ip"

def send_request(data):
    global cur
    ret=rev.sendto(data,(ip[cur],53))
    cur=(cur+1)%len(ip)

class Cache:
    def __init__(self):
        self.c={}
    def get(self,key):
        return self.c.get(key,None)
    def set(self,key,value):
        self.c[key]=value
    def remove(self,key):
        self.c.pop(key,None)

cache=Cache()

def handle_request(s,data,addr):
    req=dnslib.DNSRecord.parse(data)
    qname=str(req.q.qname)
    qid=req.header.id
    ret=cache.get(qname)
    if ret:
        ret=dnslib.DNSRecord.parse(ret)
        ret.header.id=qid;
        s.sendto(ret.pack(),addr)
    else:
        e=event.Event()
        cache.set(qname+"e",e)
        send_request(data)
        e.wait(10)
        tmp=cache.get(qname)
        if tmp:
            tmp=dnslib.DNSRecord.parse(tmp)
            tmp.header.id=qid;
            s.sendto(tmp.pack(),addr)

def handle_response(data):
    req=dnslib.DNSRecord.parse(data)
    qname=str(req.q.qname)
    print qname
    cache.set(qname,data)
    e=cache.get(qname+"e")
    cache.remove(qname+"e")
    if e:
        e.set()
        e.clear()

def handler(s,data,addr):
    req=dnslib.DNSRecord.parse(data)
    if req.header.qr:
        handle_response(data)
    else:handle_request(s,data,addr)

def main():
    preload()
    while True:
        data,addr=rev.recvfrom(8192)
        gevent.spawn(handler,rev,data,addr)

if __name__ == '__main__':
    main()


