#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import urllib
import argparse
import logging; LOG = logging.getLogger(__name__)

import json
import requests

from utils import comm

def retArgParser(throwException=True):
    if throwException: parser = comm.ThrowingArgumentParser()
    else: parser = argparse.ArgumentParser()
    
    parser.add_argument('-m', '--machine', help='<machine>')
    parser.add_argument('-p', '--port', default='8088', help='port')
    parser.add_argument('-c', '--cmd', default='getconf', help='command')    
    return parser

if __name__ == '__main__':
    logging.basicConfig(format=comm.LOGFMT,datefmt=comm.LOGDATEFMT)
    logging.getLogger().setLevel(logging.INFO)

    parser = retArgParser()
    args = parser.parse_args(sys.argv[1:])

    cmd = args.cmd.lower()
    if cmd == 'getconf': cmd = 'getConf'
    elif cmd == 'setconf': cmd = 'setConf'
    else: cmd = 'runCmd'

    url = 'http://{host}:{port}/api/v1/{cmd}'.format(host=args.machine, port=args.port, cmd=cmd)

    if cmd == 'getConf':
        req = requests.get(url)
        dct = req.json()
        print json.dumps(dct, sort_keys=True, indent=4)
    elif cmd == 'runCmd':
        headers = {'content-type': 'text'}
        req = requests.post(url, data=args.cmd, headers=headers)
        dct = req.json()
        if dct['stdout']: sys.stdout.write(dct['stdout'])
        if dct['stderr']: sys.stdout.write(dct['stderr'])
    else: pass
