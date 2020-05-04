#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import math
import re
from collections import defaultdict, namedtuple
#from jlink import JLinkPool, JLinkLowVoltage, JlinkInvalidProgFile
import socket
import time
import signal
import sys
import binascii
import os
from pynrfjprog.MultiAPI import MultiAPI
import inspect
from datetime import datetime
import thread


def get_chunks(a, l):
    return [
        a[i:i + l]
        for i in range(0, len(a), l)
    ]

class JLink(MultiAPI):
    def write_rtt(self, message, encoding='ascii'):
        if not (message.endswith('\r\n') or message.endswith('\t')):
            message += '\r\n'
        for chunk in get_chunks(message, 14):
            self.rtt_write(0, chunk, encoding='ascii')
            time.sleep(0.051)
        time.sleep(.010)

    def read(self):
        out = self.rtt_read(0, 100000, None)
        return ''.join(chr(i) for i in out if 0 < i < 128)

    def program(self, hex_file_path, reset=False, erase_usrd=False):
        if self.is_rtt_started():
            self.rtt_stop()
        try:
            program = IHex(hex_file_path)
        except ValueError:
            raise JlinkInvalidProgFile
        if erase_usrd:
            self.erase_uicr()
        for segment in program:
            self.erase_page(segment.address)
            self.write(segment.address, segment.data, True)
        if reset:
            self.sys_reset()
            self.go()

class JLinkPool:
    def __init__(self, family='NRF52'):
        self.devices = {}
        self.family = family
        self.raw_log_files = {}
        self.sniff_log_files = {}

    def attach_device(self, snr):
        try:
            api = JLink(self.family)
            api.open()
            api.connect_to_emu_with_snr(int(snr))
            print(api.dll_version())
            api.rtt_start()
            time.sleep(1)
        except Exception as e:
            logging.error(e)
            if 'LOW_VOLTAGE' in str(e):
                raise JLinkLowVoltage
            raise e
        else:
            self.devices[snr] = api
        return True

    def disconnect_device(self, snr):
        success = True
        if self.devices.get(snr):
            try:
                self.devices[snr].rtt_stop()
                time.sleep(0.2)
                self.devices[snr].disconnect_from_emu()
                time.sleep(0.2)
                self.devices[snr].close()
                time.sleep(0.2)
            except Exception as e:
                logging.error(e)
                success = False
        return success

    def detach_device(self, snr):
        success = self.disconnect_device(snr)
        if success:
            self.devices[snr].close()
            del self.devices[snr]
        return success

    def discover(self):
        api = MultiAPI('NRF52')
        api.open()
        snrs = api.enum_emu_snr()
        api.close()
        return snrs or []

snr = 0;

JLINK_POOL = JLinkPool()


def jlink_connect(snr):
    success = False
    reason = None
    try:
        print ("connecting to ", snr)
        JLINK_POOL.attach_device(snr)
    except JLinkLowVoltage:
        reason = (
            'Low voltage detected on the device, '
            'check if it is properly connected'
        )
        print(reason)
    except Exception as e:
        reason = 'Could not connect to the device. {}'.format(e)
        print(reason)
    else:
        success = True
        print('connection success')

    return success

class JLinkException(Exception):
    pass


class JLinkLowVoltage(JLinkException):
    pass


class JlinkInvalidProgFile(JLinkException):
    pass

def read_imput(jlink):
    while True:
        inputcmd = raw_input('')
        jlink.write_rtt(inputcmd)

def main():

    jlinks = JLINK_POOL.discover()
    print("----------------")
    for j in jlinks:
        print(j)
    print("----------------")


    if len(jlinks) > 1:
        if len(sys.argv) < 2 :
            print("please, select JLink")
            return 1
        snr = sys.argv[1]
    else:
        snr = jlinks[0]


    print("******" + str(snr))

    jlink_connect(snr)
    time.sleep(2)
    jlink = JLINK_POOL.devices.get(snr)
    jlink.write_rtt("log enable debug")
    thread.start_new_thread( read_imput, (jlink,) )


    while True:
        for line in jlink.read().split('\r\n'):

            if line == "\x1b[1;32m$ \x1b[1;37m" : continue
            if line : print(line)
        time.sleep(1)

if __name__ == '__main__':
    main()

