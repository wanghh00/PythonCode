#!/usr/bin/env python
# -*- coding: utf-8  -*-

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading, subprocess
import re, sys, os, getpass
import time
import json
import cgi

import logging; LOG = logging.getLogger(__name__)

LOGFMT = '[%(asctime)s %(filename)s:%(lineno)d] %(message)s'
LOGDATEFMT = '%Y%m%d-%H:%M:%S'

DctConf = { }

def getConf(handler):
    sendAsJson(handler, DctConf)

def setConf(handler):
    ctype, pdict = cgi.parse_header(handler.headers.getheader('content-type'))
    if ctype == 'application/json':
        length = int(handler.headers.getheader('content-length'))
        DctConf = json.loads(handler.rfile.read(length))

    getConf(handler)

def runCmd(handler):
    ctype, pdict = cgi.parse_header(handler.headers.getheader('content-type'))

    length = int(handler.headers.getheader('content-length'))
    cmd = handler.rfile.read(length)
    LOG.info(cmd)

    dct = runLocalCmd(cmd)
    sendAsJson(handler, dct)

def sendAsJson(handler, dct, code=200):
    data = json.dumps(dct)

    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json')

    if handler._info.get('gzip'):
        handler.send_header('Content-Encoding', 'gzip')
        data = gzipBuf(data)

    handler.send_header("Content-length", len(data))
    handler.end_headers()
    LOG.info('Output-Size: %s' % len(data))
    handler.wfile.write(data)

def runLocalCmd(cmd):
    dct = {}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    dct['stdout'], dct['stderr'] = proc.communicate()
    dct['returncode '] = proc.returncode
    return dct

def handleError(handler, ex):
    handler.send_response(500)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps({"error":"%s" % ex}))

def logReq(handler):
    LOG.info(handler.client_address)
    LOG.info(handler.path)
    LOG.info(handler.headers)
    LOG.info('Customized request infor: %s' % handler._info)

def initRequest(handler):
    handler._info = {}
    if (handler.headers.getheader('accept-encoding') or '').find('gzip') != -1:
        handler._info['gzip'] = 1

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            initRequest(self); logReq(self)

            if self.path == '/api/v1/setConf':
                setConf(self)
            elif self.path == '/api/v1/runCmd':
                runCmd(self)
            else:
                dct = {'error': 'Unknown request [%s]' % self.path}
                sendAsJson(self, dct, 400)
        except Exception as ex:
            LOG.exception(ex)
            handleError(self, ex)

    def do_GET(self):
        try:
            initRequest(self); logReq(self)

            if self.path == '/api/v1/getConf':
                getConf(self)
            else:
                dct = {'error': 'Unknown request [%s]' % self.path}
                sendAsJson(self, dct, 400)
        except Exception as ex:
            LOG.exception(ex)
            handleError(self, ex)

def gzipBuf(buf, level=6):
    import cStringIO, gzip
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode = 'wb', fileobj = zbuf, compresslevel = level)
    zfile.write(buf); zfile.close()
    return zbuf.getvalue()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    logging.basicConfig(format=LOGFMT,datefmt=LOGDATEFMT)
    logging.getLogger().setLevel(logging.INFO)

    DctConf['sys.argv'] = sys.argv
    DctConf['cwd'] = os.getcwd()
    DctConf['start_time'] = time.strftime(LOGDATEFMT + ' %Z')
    DctConf['pid'] = os.getpid()
    DctConf['user'] = getpass.getuser()
    DctConf['userid'] = os.getuid()

    LOG.info(sys.argv)
    port = len(sys.argv) > 1 and sys.argv[1] or 8088

    server = ThreadedHTTPServer(('0.0.0.0', int(port)), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()