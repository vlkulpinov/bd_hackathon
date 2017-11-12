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
import requests

import binascii
import types
import sys
import argparse
import datetime

import time

PORT = 8333
SLEEP_TIMEOUT = 0.5

MINHEIGHT = 747814

def getcur():
    for i in range(3):
        try:
            r = requests.get('https://nodes.wavesnodes.com/blocks/last')
            break
        except:
            time.sleep(1)
            continue
    d = r.json()
    return d['height'], d['signature']

def getcertain(height):
    for i in range(3):
        try:
            r = requests.get('https://nodes.wavesnodes.com/blocks/at/{height}'.format(height=height))
            break
        except:
            time.sleep(1)
            continue
    d = r.json()
    return d['height'], d['signature']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, type=int)
    parser.add_argument('--output-prefix', required=True)
    args = parser.parse_args()

    if args.output_prefix is None:
        outputFile = './wata_{id:02d}'.format(id=args.id)
    else:
        outputFile = args.output_prefix + '{id:02d}'.format(id=args.id)

    blockchain = dict()
    hasSaved = False
    try:
        with open(outputFile, 'r') as f:
            f.read()
        hasSaved = True
    except:
        hasSaved = False

    max_height = MINHEIGHT
    if hasSaved:
        max_height -= 1
        with open(outputFile, 'r') as f:
            for line in f:
                try:
                    max_height += 1
                    height, cur, ts = line.strip().split(' ')
                    blockchain[max_height] = cur
                    # max_height = max(max_height, height)
                except Exception as ex:
                    print >>sys.stderr, ex

    try:
        _, blockchain[max_height] = getcertain(max_height)
    except:
        pass
    for h in range(max_height, getcur()[0] + 5):
        try:
            height, signature = getcertain(h)
        except:
            continue
        if height not in blockchain:
            blockchain[height] = signature
            print >>sys.stderr, height
            with open(outputFile, 'a') as f:
                try:
                    print >>f, blockchain[height - 1], blockchain[height], datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                except:
                    try:
                        _, blockchain[height - 1] = getcertain(height - 1)
                        print >>f, blockchain[height - 1], blockchain[height], datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                    except:
                        continue
                print >>sys.stderr, "New block", datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")



    while True:
        for i in range(3):
            try:
                r = requests.get('https://nodes.wavesnodes.com/blocks/last')
                break
            except:
                continue

        height, signature = getcur()
        if height not in blockchain:
            blockchain[height] = signature
            with open(outputFile, 'a') as f:
                try:
                    print >>f, blockchain[height - 1], blockchain[height], datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                except:
                    try:
                        _, blockchain[height - 1] = getcertain(height - 1)
                        print >>f, blockchain[height - 1], blockchain[height], datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                    except:
                        pass

                print >>sys.stderr, "New block", datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")

        elif blockchain[height] != signature:
            blockchain[height] = signature
            with open(outputFile, 'a') as f:
                try:
                    print >>f, blockchain[height - 1], blockchain[height], datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                except:
                    try:
                        _, blockchain[height - 1] = getcertain(height - 1)
                        print >>f, blockchain[height - 1], blockchain[height], datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
                    except:
                        pass
                print >>sys.stderr, "New permuation detected", datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")

        time.sleep(SLEEP_TIMEOUT)

try: __IPYTHON__
except NameError: main()
