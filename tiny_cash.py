#! python2.7
# coding: utf-8
#
# tinybitcoinpeer.py
# A toy bitcoin node in Python. Connects to a random testnet
# node, shakes hands, reacts to pings, and asks for pongs.
# - Andrew Miller https://soc1024.com/
#
# Dependencies: 
# - gevent
# - https://github.com/petertodd/python-bitcoinlib
# 
# This file is intended to be useful as a starting point 
# for building your own Bitcoin network tools. Rather than
# choosing one way to do things, it illustrates several 
# different ways... feel free to pick and choose.
# 
# - The msg_stream() function handily turns a stream of raw
#     Bitcoin p2p socket data into a stream of parsed messages.
#     Parsing is provided by the python-bitcoinlib dependency.
#
# - The handshake is performed with ordinary sequential code.
#    You can get a lot done without any concurrency, such as
#     connecting immediately to fetching blocks or addrs,
#     or sending payloads of data to a node.

# - The node first attempts to resolve the DNS name of a Bitcoin
#     seeder node. Bitcoin seeder speak the DNS protocol, but
#     actually respond with IP addresses for random nodes in the
#     network.
#
# - After the handshake, a "message handler" is installed as a 
#     background thread. This handler logs every message 
#     received, and responds to "Ping" challenges. It is easy 
#     to add more reactive behaviors too.
# 
# - This shows off a versatile way to use gevent threads, in
#     multiple ways at once. After forking off the handler 
#     thread, the main thread also keeps around a tee of the
#     stream, making it easy to write sequential schedules.
#     This code periodically sends ping messages, sleeping 
#     in between. Additional threads could be given their 
#     own tees too.
#
import gevent, gevent.socket as socket
from gevent.queue import Queue
import bitcoin
from bitcoin.messages import *
from bitcoin.net import CAddress, CInv
import time, sys, contextlib

import binascii
import types
import sys
import argparse
import datetime

PORT = 8333
SLEEP_TIMEOUT = 2
gen = '0000000000000000007acb0dc26c4eca7fa4cc53eb31a72e3d333e1cb5a3f1f5'

knownNodes = [
    ('66.128.82.74', 'US'),
    ('97.100.98.114', 'US'),
    ('52.41.36.27', 'US'),
    ('45.58.60.119', 'US'),
    ('93.228.73.243', 'GE'),
    ('138.68.79.40', 'GE'),
    ('88.99.185.194', 'GE'),
    ('139.59.208.141', 'GE'),
    ('123.57.226.57', 'CH'),
    ('101.201.46.219', 'CH'),
    ('60.191.146.186', 'CH'),
    ('219.132.194.83', 'CH'),
    ('60.190.46.74', 'CH'),
    ('223.167.7.88', 'CH'),
    ('86.245.43.136', 'FR'),
    ('62.75.244.78', 'FR'),
    ('91.121.110.184', 'FR'),
    ('176.159.108.180', 'FR'),
    ('77.204.29.197', 'FR'),
    ('82.241.64.219', 'FR'),
    ('109.195.150.106', 'RU'),
    ('87.224.209.34', 'RU'),
    ('95.165.158.177', 'RU'),
    ('81.174.148.47', 'UK'),
    ('176.58.114.235', 'UK')
]

outputFile = ''

# bitcoin.SelectParams('testnet')

# Turn a raw stream of Bitcoin p2p socket data into a stream of 
# parsed messages.
def msg_stream(f):
    while True:
        yield MsgSerializable.stream_deserialize(f)

def prhash(hh):
    return binascii.hexlify(hh[::-1])

def uprhash(hh):
    return binascii.unhexlify(hh)[::-1]

def tee_and_handle(sock, msgs):
    blockchain = dict()
    fileExists = True
    try:
        with open(outputFile, 'r') as f:
            f.read()
    except:
        fileExists = False

    if fileExists:
        with open(outputFile, 'r') as f:
            for line in f:
                try:
                    prev, cur, ts = line.strip().split(' ')
                    blockchain[uprhash(prev)] = uprhash(cur)
                except Exception as ex:
                    print >>sys.stderr, ex

    queue = Queue() # unbounded buffer

    def _run():
        for msg in msgs:
            sys.stdout.write('Received: %s\n' % msg)

            if msg.command == 'ping':
                print 'Handler: Sending pong'
                sock.send(msg_pong(nonce=msg.nonce).to_bytes())

            ok = False
            if msg.command == 'inv':
                if len(msg.inv) >= 3 and CInv.typemap[msg.inv[0].type] == "Block" and CInv.typemap[msg.inv[1].type] == "Block" and CInv.typemap[msg.inv[2].type] == "Block":
                    ok = True

            if ok:
                # blockchain = [node] -> next
                for i in range(0, len(msg.inv) - 1):
                    if not prhash(msg.inv[i].hash).startswith('000000000000'):
                        break
                    if not prhash(msg.inv[i + 1].hash).startswith('000000000000'):
                        break
                    if msg.inv[i].hash not in blockchain:
                        with open(outputFile, 'a') as f:
                            print >>sys.stderr, "New block found ", datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                            print >>f, prhash(msg.inv[i].hash), prhash(msg.inv[i + 1].hash), datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                        blockchain[msg.inv[i].hash] = msg.inv[i + 1].hash
                    else:
                        if blockchain[msg.inv[i].hash] != msg.inv[i + 1].hash:
                            if msg.inv[i].hash == msg.inv[i + 1].hash:
                                continue
                            msg.inv[i].hash = msg.inv[i + 1].hash
                            with open(outputFile, 'a') as f:
                                print >>sys.stderr, "New permutation detected ", datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                                print >>f, prhash(msg.inv[i].hash), prhash(msg.inv[i + 1].hash), datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")


            queue.put(msg)

    t = gevent.Greenlet(_run)
    t.start()
    while True: yield(queue.get())

def version_pkt(client_ip, server_ip):
    msg = msg_version()
    msg.nVersion = 70002
    msg.addrTo.ip = server_ip
    msg.addrTo.port = PORT
    msg.addrFrom.ip = client_ip
    msg.addrFrom.port = PORT
    msg.strSubVer = "/tinybitcoinpeer.py/"
    return msg

def addr_pkt( str_addrs ):
    msg = msg_addr()
    addrs = []
    for i in str_addrs:
        addr = CAddress()
        addr.port = 8333
        addr.nTime = int(time.time())
        addr.ip = i
        addrs.append( addr )
    msg.addrs = addrs
    return msg

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, type=int)
    parser.add_argument('--output-prefix', required=True)
    args = parser.parse_args()

    if args.output_prefix is None:
        global outputFile
        outputFile = './cata_{id:02d}'.format(id=args.id)
    else:
        outputFile = args.output_prefix + '{id:02d}'.format(id=args.id)

    with contextlib.closing(socket.socket()) as s, \
         contextlib.closing(s.makefile("r+b", bufsize=0)) as cf:

        # This will actually return a random testnet node
        their_ip = socket.gethostbyname("seed.tbtc.petertodd.org")
        # their_ip = knownNodes[args.id][0]
        their_ip = '188.68.38.210'
        print 'Connecting to:', their_ip

        my_ip = "127.0.0.1"

        s.connect( (their_ip,PORT) )
        stream = msg_stream(cf)

        # Send Version packet
        s.send( version_pkt(my_ip, their_ip).to_bytes() )
        print "Send version"

        # Receive their Version
        their_ver = stream.next()
        print 'Got', their_ver

        # Send Version acknolwedgement (Verack)
        s.send( msg_verack().to_bytes() )
        print 'Sent verack'

        # Fork off a handler, but keep a tee of the stream
        stream = tee_and_handle(s, stream)

        # Get Verack
        their_verack = stream.next()
        print 'Got', their_verack

        while True:
            s.send(msg_ping().to_bytes())
            gevent.sleep(5)

try: __IPYTHON__
except NameError: main()
