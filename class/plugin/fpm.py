# coding:utf-8


import json
import os
import time
import re
import sys
import time
import struct
import fcgi_client

FCGI_Header = '!BBHHBx'

if sys.version_info[0] == 2:
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO
else:
    from io import BytesIO as StringIO


def get_header_data(sock):
    headers_data = b''
    total_len = 0
    header_len = 1024 * 128
    while True:
        fastcgi_header = sock.recv(8)
        if not fastcgi_header:
            break
        if len(fastcgi_header) != 8:
            headers_data += fastcgi_header
            break
        fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
        if fast_pack[1] == 3:
            break

        tlen = fast_pack[3]
        while tlen > 0:
            sd = sock.recv(tlen)
            if not sd:
                break
            headers_data += sd
            tlen -= len(sd)

        total_len += fast_pack[3]
        if fast_pack[4]:
            sock.recv(fast_pack[4])
        if total_len > header_len:
            break
    return headers_data


def format_header_data(headers_data):
    status = '200 OK'
    headers = {}
    pos = 0
    while True:
        eolpos = headers_data.find(b'\n', pos)
        if eolpos < 0:
            break
        line = headers_data[pos:eolpos - 1]
        pos = eolpos + 1
        line = line.strip()
        if len(line) < 2:
            break
        if line.find(b':') == -1:
            continue
        header, value = line.split(b':', 1)
        header = header.strip()
        value = value.strip()
        if isinstance(header, bytes):
            header = header.decode()
            value = value.decode()
        if header == 'Status':
            status = value
            if status.find(' ') < 0:
                status += ' BTPanel'
        else:
            headers[header] = value
    bdata = headers_data[pos:]
    status = int(status.split(' ')[0])
    return status, headers, bdata


def resp_sock(sock, bdata):
    yield bdata
    while True:
        fastcgi_header = sock.recv(8)
        if not fastcgi_header:
            break
        if len(fastcgi_header) != 8:
            yield fastcgi_header
            break
        fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
        if fast_pack[1] == 3:
            break
        tlen = fast_pack[3]
        while tlen > 0:
            sd = sock.recv(tlen)
            if not sd:
                break
            tlen -= len(sd)
            if sd:
                yield sd

        if fast_pack[4]:
            sock.recv(fast_pack[4])
    sock.close()


class fpm(object):

    def __init__(self, sock=None, document_root='', last_path=''):
        if sock:
            self.fcgi_sock = sock
            if document_root[-1:] != '/':
                document_root += '/'
            self.document_root = document_root
            self.last_path = last_path

    def load_url_public(self, url, content=b'', method='GET', content_type='application/x-www-form-urlencoded'):
        fcgi = fcgi_client.FCGIApp(connect=self.fcgi_sock)
        try:
            script_name, query_string = url.split('?')
        except ValueError:
            script_name = url
            query_string = ''

        content_length = len(content)
        if content:
            content = StringIO(content)

        env = {
            'SCRIPT_FILENAME': '%s%s' % (self.document_root, script_name),
            'QUERY_STRING': query_string,
            'REQUEST_METHOD': method,
            'SCRIPT_NAME': self.last_path + script_name,
            'REQUEST_URI': url,
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_SOFTWARE': 'SLEMP-Panel',
            'REDIRECT_STATUS': '200',
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': str(content_length),
            'DOCUMENT_URI': script_name,
            'DOCUMENT_ROOT': self.document_root,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REMOTE_ADDR': '127.0.0.1',
            'REMOTE_PORT': '7200',
            'SERVER_ADDR': '127.0.0.1',
            'SERVER_PORT': '80',
            'SERVER_NAME': 'SLEMP-Panel'
        }

        fpm_sock = fcgi(env, content)

        _data = b''
        while True:
            fastcgi_header = fpm_sock.recv(8)
            if not fastcgi_header:
                break
            if len(fastcgi_header) != 8:
                _data += fastcgi_header
                break
            fast_pack = struct.unpack(FCGI_Header, fastcgi_header)
            if fast_pack[1] == 3:
                break
            tlen = fast_pack[3]
            while tlen > 0:
                sd = fpm_sock.recv(tlen)
                if not sd:
                    break
                tlen -= len(sd)
                _data += sd
            if fast_pack[4]:
                fpm_sock.recv(fast_pack[4])
        status, headers, data = format_header_data(_data)
        return data
