"""
Example collector script for NetFlow v1, v5, and v9.
This file belongs to https://github.com/bitkeks/python-netflow-v9-softflowd.

Copyright 2017-2019 Dominik Pataky <dev@bitkeks.eu>
Licensed under MIT License. See LICENSE.
"""

import argparse
from collections import namedtuple
from datetime import date
import queue
import gzip
import json
import logging
import sys
import socketserver
import threading
import time

from v5 import V5ExportPacket

PACKET_TIMEOUT = 60 * 60

RawPacket = namedtuple('RawPacket', ['ts', 'client', 'data'])


class QueuingRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]  # get content, [1] would be the socket
        self.server.queue.put(RawPacket(time.time(), self.client_address, data))


class QueuingUDPListener(socketserver.ThreadingUDPServer):
    def __init__(self, interface, queue):
        self.queue = queue
        super().__init__(interface, QueuingRequestHandler)


class NetFlowListener(threading.Thread):

    def __init__(self, host, port):
        self.output = queue.Queue()
        self.input = queue.Queue()
        self.server = QueuingUDPListener((host, port), self.input)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self._shutdown = threading.Event()
        super().__init__()

    def get(self, block=True, timeout=None):
        return self.output.get(block, timeout)

    def run(self):
        try:
            templates = {}
            to_retry = []
            while not self._shutdown.is_set():
                try:
                    pkt: RawPacket = self.input.get(block=True, timeout=0.5)
                except queue.Empty:
                    continue
                export = V5ExportPacket(pkt.data)
                print("Processed a v " + str(export.header.version) + " ExportPacket with " + str(export.header.count) + " flows.")
                if export.header.version == 9 and export.contains_new_templates and to_retry:
                    for p in to_retry:
                        self.input.put(p)
                    to_retry.clear()

                self.output.put((pkt.ts, pkt.client, export))
        finally:
            self.server.shutdown()
            self.server.server_close()

    def stop(self):
        self._shutdown.set()

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)
        super().join(timeout=timeout)


def get_export_packets(host, port):
    listener = NetFlowListener(host, port)
    listener.start()
    try:
        while True:
            yield listener.get()
    finally:
        listener.stop()
        listener.join()


#def netFlowService():
path = 'AdministradorDeRed/utils/'
try:
    for ts, client, export in get_export_packets("192.168.0.2", 9000):
        fecha = date.today()
        data = {
            "client": client[0],
            "year" : str(fecha.year),
            "month" : str(fecha.month),
            "day" : str(fecha.day),
            "flows" : [flow.data for flow in export.flows]
        }
        line = json.dumps(data).encode() + b"\n"  # byte encoded line
        with gzip.open( path + str(client[0]) + ".gz", "ab") as fh:  # open as append, not reading the whole file
            fh.write(line)
except KeyboardInterrupt:
    print("Received KeyboardInterrupt, passing through")
    pass