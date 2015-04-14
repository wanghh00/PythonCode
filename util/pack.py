#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys, time
import cPickle, struct
import select, socket
import bz2, zlib
import logging; LOG = logging.getLogger(__name__)
import simplejson as json

class PackerException(Exception): pass

class iPack(object):
    def dumps(self, *args, **kwargs): raise NotImplementedError
    def loads(self, *args, **kwargs): raise NotImplementedError

class Packer(iPack):
    # Support Type  : 'PCK':cPickle; 'JSN':Json; 'NAN':None; '   '/'':Default
    # Support Format: 'ZIP':zlib; 'BZ2':bz2; 'NAN':None; '   '/'':Default
    def __init__(self, ver='1 ', typ='PCK', fmt='ZIP', thresh=1024*4):
        self.typ = typ; self.fmt = fmt; self.thresh = thresh; self.ver = ver
    
    def dumps(self, obj, ver=None, typ=None, fmt=None, thresh=0, clvl=6):
        exe_thresh = thresh or self.thresh
        exe_fmt = fmt or self.fmt
        exe_type = typ or self.typ
        exe_ver = self.ver if ver == None else ver
        
        if exe_type == 'PCK': outstr = cPickle.dumps(obj, cPickle.HIGHEST_PROTOCOL)
        elif exe_type == 'JSN': outstr = json.dumps(obj)
        elif exe_type == 'NAN': outstr = obj
        elif exe_type.strip(): raise PackerException('Unknown packer typ[%s]' % exe_type)
        else: exe_type = '   '
                
        if exe_fmt != 'NAN':
            exe_fmt = exe_fmt if len(outstr) >= exe_thresh else '   '
        if exe_fmt == 'ZIP': outstr = zlib.compress(outstr, clvl)
        elif exe_fmt == 'BZ2': outstr = bz2.compress(outstr)
        elif exe_fmt == 'NAN': pass
        elif exe_fmt.strip(): raise PackerException('Unknown packer fmt[%s]' % exe_fmt)
        else: exe_fmt = '   '
        
        if not exe_ver: return outstr
        return struct.pack("8s", exe_ver+exe_fmt+exe_type)+outstr
    
    def loads(self, objstr, dctMeta=None):
        stat = 0; fmt = ''; typ = ''; ver = ''; obj = None; errmsg = ''
        try:
            if objstr[0] != '{':
                ver = objstr[:2]; fmt = objstr[2:5].strip(); typ = objstr[5:8].strip(); obj = objstr[8:]
            else: typ = 'JSN'; fmt = 'NAN'; obj = objstr
            
            if fmt == 'ZIP': obj = zlib.decompress(obj)
            elif fmt == 'BZ2': obj = bz2.decompress(obj)
            elif fmt == 'NAN': pass
            elif fmt: stat = 'ErrPacker:fmt'; raise PackerException('Unknown packer fmt[%s]' % fmt)
            
            if typ == 'PCK': obj = cPickle.loads(obj)
            elif typ == 'JSN': obj = json.loads(obj)
            elif typ == 'NAN': pass
            elif typ: stat = 'ErrPacker:typ'; raise PackerException('Unknown packer typ[%s]' % typ)
        except PackerException as inst:
            LOG.exception(inst); errmsg = "[%s] %s: %s" % (type(inst), inst.args, inst)
        except Exception as inst:
            LOG.exception(inst); obj = None; stat = 'ErrPacker'; errmsg = "[%s] %s: %s" % (type(inst), inst.args, inst)    
             
        if not dctMeta == None:
            dctMeta.update({'stat':stat, 'ver':ver, 'fmt':fmt, 'typ':typ})
            if errmsg: dctMeta['errmsg'] = errmsg
            
        return obj
        