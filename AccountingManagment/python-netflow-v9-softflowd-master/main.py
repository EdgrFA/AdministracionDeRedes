#!/usr/bin/env python3

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

from netflow import parse_packet, TemplateNotRecognized, UnknownNetFlowVersion

logger = logging.getLogger(__name__)

# Amount of time to wait before dropping an undecodable ExportPacket
PACKET_TIMEOUT = 60 * 60

RawPacket = namedtuple('RawPacket', ['ts', 'client', 'data'])


class QueuingRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]  # get content, [1] would be the socket
        self.server.queue.put(RawPacket(time.time(), self.client_address, data))
        logger.debug(
            "Received %d bytes of data from %s", len(data), self.client_address
        )


class QueuingUDPListener(socketserver.ThreadingUDPServer):
    """A threaded UDP server that adds a (time, data) tuple to a queue for
    every request it sees
    """
    def __init__(self, interface, queue):
        self.queue = queue
        super().__init__(interface, QueuingRequestHandler)


class NetFlowListener(threading.Thread):
    """A thread that listens for incoming NetFlow packets, processes them, and
    makes them available to consumers.

    - When initialized, will start listening for NetFlow packets on the provided
      host and port and queuing them for processing.
    - When started, will start processing and parsing queued packets.
    - When stopped, will shut down the listener and stop processing.
    - When joined, will wait for the listener to exit

    For example, a simple script that outputs data until killed with CTRL+C:
    >>> listener = NetFlowListener('0.0.0.0', 2055)
    >>> print("Listening for NetFlow packets")
    >>> listener.start() # start processing packets
    >>> try:
    ...     while True:
    ...         ts, export = listener.get()
    ...         print("Time: {}".format(ts))
    ...         for f in export.flows:
    ...             print(" - {IPV4_SRC_ADDR} sent data to {IPV4_DST_ADDR}"
    ...                   "".format(**f))
    ... finally:
    ...     print("Stopping...")
    ...     listener.stop()
    ...     listener.join()
    ...     print("Stopped!")
    """

    def __init__(self, host, port):
        logger.info("Starting the NetFlow listener on {}:{}".format(host, port))
        self.output = queue.Queue()
        self.input = queue.Queue()
        self.server = QueuingUDPListener((host, port), self.input)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self._shutdown = threading.Event()
        super().__init__()

    def get(self, block=True, timeout=None):
        """Get a processed flow.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a flow is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the queue.Empty exception if no flow was available within that time.
        Otherwise ('block' is false), return a flow if one is immediately
        available, else raise the queue.Empty exception ('timeout' is ignored
        in that case).
        """
        return self.output.get(block, timeout)

    def run(self):
        # Process packets from the queue
        try:
            templates = {}
            to_retry = []
            while not self._shutdown.is_set():
                try:
                    # 0.5s delay to limit CPU usage while waiting for new packets
                    pkt: RawPacket = self.input.get(block=True, timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    export = parse_packet(pkt.data, templates)
                except UnknownNetFlowVersion as e:
                    logger.error("%s, ignoring the packet", e)
                    continue
                except TemplateNotRecognized:
                    if time.time() - pkt.ts > PACKET_TIMEOUT:
                        logger.warning("Dropping an old and undecodable v9 ExportPacket")
                    else:
                        to_retry.append(pkt)
                        logger.debug("Failed to decode a v9 ExportPacket - will "
                                     "re-attempt when a new template is discovered")
                    continue

                logger.debug("Processed a v%d ExportPacket with %d flows.",
                             export.header.version, export.header.count)

                # If any new templates were discovered, dump the unprocessable
                # data back into the queue and try to decode them again
                if export.header.version == 9 and export.contains_new_templates and to_retry:
                    logger.debug("Received new template(s)")
                    logger.debug("Will re-attempt to decode %d old v9 ExportPackets",
                                 len(to_retry))
                    for p in to_retry:
                        self.input.put(p)
                    to_retry.clear()

                self.output.put((pkt.ts, pkt.client, export))
        finally:
            self.server.shutdown()
            self.server.server_close()

    def stop(self):
        logger.info("Shutting down the NetFlow listener")
        self._shutdown.set()

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)
        super().join(timeout=timeout)


def get_export_packets(host, port):
    """A generator that will yield ExportPacket objects until it is killed"""

    listener = NetFlowListener(host, port)
    listener.start()
    try:
        while True:
            yield listener.get()
    finally:
        listener.stop()
        listener.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A sample netflow collector.")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="collector listening address")
    parser.add_argument("--port", "-p", type=int, default=9000,
                        help="collector listener port")
    parser.add_argument("--file", "-o", type=str, dest="output_file",
                        default="flows.gz",
                        help="collector export multiline JSON file")
    parser.add_argument("--debug", "-D", action="store_true",
                        help="Enable debug output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")

    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # With every parsed flow a new line is appended to the output file. In previous versions, this was implemented
        # by storing the whole data dict in memory and dumping it regularly onto disk. This was extremely fragile, as
        # it a) consumed a lot of memory and CPU (dropping packets since storing one flow took longer than the arrival
        # of the next flow) and b) broke the exported JSON file, if the collector crashed during the write process,
        # rendering all collected flows during the runtime of the collector useless (the file contained one large JSON
        # dict which represented the 'data' dict).

        # In this new approach, each received flow is parsed as usual, but it gets appended to a gzipped file each time.
        # All in all, this improves in three aspects:
        # 1. collected flow data is not stored in memory any more
        # 2. received and parsed flows are persisted reliably
        # 3. the disk usage of files with JSON and its full strings as keys is reduced by using gzipped files
        # This also means that the files have to be handled differently, because they are gzipped and not formatted as
        # one single big JSON dump, but rather many little JSON dumps, separated by line breaks.
        for ts, client, export in get_export_packets(args.host, args.port):
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
        logger.info("Received KeyboardInterrupt, passing through")
        pass
