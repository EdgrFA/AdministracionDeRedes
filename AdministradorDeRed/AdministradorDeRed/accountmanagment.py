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
        print("Received %d bytes of data from %s", len(data), self.client_address)


class QueuingUDPListener(socketserver.ThreadingUDPServer):
    def __init__(self, interface, queue):
        self.queue = queue
        super().__init__(interface, QueuingRequestHandler)


class NetFlowListener(threading.Thread):

    def __init__(self, host, port):
        print("Starting the NetFlow listener on {}:{}".format(host, port)))
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

                try:
                    export = V5ExportPacket(pkt.data, templates)
                except UnknownNetFlowVersion as e:
                    logger.error("%s, ignoring the packet", e)
                    continue
                except TemplateNotRecognized:
                    if time.time() - pkt.ts > PACKET_TIMEOUT:
                        logger.warning("Dropping an old and undecodable v9 ExportPacket")
                    else:
                        to_retry.append(pkt)
                        print("Failed to decode a v9 ExportPacket - will "
                                     "re-attempt when a new template is discovered")
                    continue

                print("Processed a v%d ExportPacket with %d flows.",
                             export.header.version, export.header.count)

                if export.header.version == 9 and export.contains_new_templates and to_retry:
                    print("Received new template(s)")
                    print("Will re-attempt to decode %d old v9 ExportPackets",
                                 len(to_retry))
                    for p in to_retry:
                        self.input.put(p)
                    to_retry.clear()

                self.output.put((pkt.ts, pkt.client, export))
        finally:
            self.server.shutdown()
            self.server.server_close()

    def stop(self):
        print("Shutting down the NetFlow listener")
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


def netFlowService():

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
            with gzip.open(args.output_file, "ab") as fh:  # open as append, not reading the whole file
                fh.write(line)
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, passing through")
        pass