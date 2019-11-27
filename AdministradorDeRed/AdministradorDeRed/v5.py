"""
Netflow V5 collector and parser implementation in Python 3.
Created purely for fun. Not battled tested nor will it be.

Reference: https://www.cisco.com/c/en/us/td/docs/net_mgmt/netflow_collection_engine/3-6/user/guide/format.html

This script is specifically implemented in combination with softflowd.
See https://github.com/djmdjm/softflowd

"""

import struct

def intIp_to_string(ip):
        strIp = str((ip >> 24) & 255)
        strIp += '.' + str((ip >> 16) & 255)
        strIp += '.' + str((ip >> 8) & 255)
        strIp += '.' + str(ip & 255)
        return strIp

class DataFlow:
    length = 48

    def __init__(self, data):
        self.data = {}
        self.data['IPV4_SRC_ADDR'] = intIp_to_string(int(struct.unpack('!I', data[:4])[0]))
        self.data['IPV4_DST_ADDR'] = intIp_to_string(int(struct.unpack('!I', data[4:8])[0]))
        self.data['IN_PACKETS'] = struct.unpack('!I', data[16:20])[0]

    def __repr__(self):
        return "<DataRecord with data {}>".format(self.data)



class Header:
    """The header of the V5ExportPacket"""

    length = 24

    def __init__(self, data):
        header = struct.unpack('!HHIIIIBBH', data[:self.length])
        self.version = header[0]
        self.count = header[1]
        self.uptime = header[2]
        self.timestamp = header[3]
        self.timestamp_nano = header[4]
        self.sequence = header[5]
        self.engine_type = header[6]
        self.engine_id = header[7]
        self.sampling_interval = header[8]


class V5ExportPacket:
    """The flow record holds the header and data flowsets."""

    def __init__(self, data):
        self.flows = []
        self.header = Header(data)

        offset = self.header.length
        for flow_count in range(0, self.header.count):
            flow = DataFlow(data[offset:])
            self.flows.append(flow)
            offset += flow.length

    def __repr__(self):
        return "<ExportPacket v{} with {} records>".format(
                self.header.version, self.header.count)
