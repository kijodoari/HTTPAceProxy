# -*- coding: utf-8 -*-
'''
af1c1onados Plugin
http://ip:port/af1c1onados
'''
__author__ = 'HTTPAceProxy'

import requests
import logging
import traceback
import time
import zlib
from urllib3.packages.six.moves.urllib.parse import urlparse, quote, unquote
from urllib3.packages.six import ensure_str, ensure_binary, ensure_text
from PlaylistGenerator import PlaylistGenerator
from utils import schedule, query_get
import config.af1c1onados as config

class Af1c1onados(object):
    
    handlers = ('af1c1onados',)

    def __init__(self, AceConfig, AceProxy):
        self.AceConfig = AceConfig
        self.AceProxy = AceProxy
        self.picons = self.channels = self.playlist = self.etag = None
        self.playlisttime = time.time()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.logger = logging.getLogger('Af1c1onados')
        
        # Initial parse
        self.Playlistparser()
        
        # Schedule updates
        if config.updateevery:
            schedule(config.updateevery * 60, self.Playlistparser)

    def Playlistparser(self):
        try:
            self.logger.info('Fetching playlist from %s' % config.url)
            r = requests.get(config.url, headers=self.headers, proxies=config.proxies, timeout=30)
            r.raise_for_status()
            
            data = r.json()
            
            self.playlist = PlaylistGenerator(m3uchanneltemplate=config.m3uchanneltemplate)
            self.picons = {}
            self.channels = {}
            m = requests.auth.hashlib.md5()
            
            groups = data.get('groups', [])
            for group in groups:
                group_name = group.get('name', 'Others')
                stations = group.get('stations', [])
                
                for station in stations:
                    name = station.get('name')
                    url = station.get('url')
                    image = station.get('image', '')
                    
                    if not name or not url:
                        continue
                        
                    # Handle duplicate names if necessary
                    unique_name = name
                    counter = 2
                    while unique_name in self.channels:
                        unique_name = '%s (%d)' % (name, counter)
                        counter += 1
                    
                    self.channels[unique_name] = url
                    self.picons[unique_name] = image
                    
                    itemdict = {
                        'name': unique_name,
                        'tvg': unique_name,
                        'tvgid': '',
                        'group': group_name,
                        'logo': image,
                        'url': quote(ensure_str(unique_name), '')
                    }
                    
                    self.playlist.addItem(itemdict)
                    m.update(ensure_binary(unique_name))
            
            self.etag = '"' + m.hexdigest() + '"'
            self.playlisttime = time.time()
            self.logger.info('Playlist updated: %d channels in %d groups' % (len(self.channels), len(groups)))
            return True
            
        except Exception as e:
            self.logger.error('Error parsing playlist: %s' % repr(e))
            self.logger.error(traceback.format_exc())
            return False

    def handle(self, connection):
        # Refresh if needed
        if not self.playlist or (time.time() - self.playlisttime > 30 * 60):
            if not self.Playlistparser():
                connection.send_error(500, 'Playlist error')
                return

        # Handle individual channel requests
        if connection.path.startswith('/af1c1onados/channel/'):
            import os
            basename = os.path.basename(connection.path)
            chname = ensure_text(unquote(os.path.splitext(basename)[0]))
            ext = basename.split('.')[-1] if '.' in basename else 'm3u8'
            
            url = self.channels.get(chname)
            if not url:
                connection.send_error(404, 'Channel not found')
                return
                
            parsed = urlparse(url)
            connection.__dict__.update({
                'channelName': chname,
                'channelIcon': self.picons.get(chname),
                'path': {
                    'acestream': '/content_id/%s/%s.%s' % (parsed.netloc, chname, ext),
                    'infohash': '/infohash/%s/%s.%s' % (parsed.netloc, chname, ext),
                    'http': '/url/%s/%s.%s' % (quote(url, ''), chname, ext),
                    'https': '/url/%s/%s.%s' % (quote(url, ''), chname, ext),
                }[parsed.scheme]
            })
            connection.__dict__.update({'splittedpath': connection.path.split('/')})
            connection.__dict__.update({'reqtype': connection.splittedpath[1].lower()})
            return

        # Handle ETag
        elif self.etag == connection.headers.get('If-None-Match'):
            connection.send_response(304)
            connection.send_header('Connection', 'close')
            connection.end_headers()
            return

        # Serve M3U
        else:
            try:
                exported = self.playlist.exportm3u(
                    hostport=connection.headers['Host'],
                    path='/af1c1onados/channel',
                    header=config.m3uheadertemplate,
                    query=connection.query
                )
                
                response_headers = {
                    'Content-Type': 'audio/mpegurl; charset=utf-8',
                    'Connection': 'close',
                    'Access-Control-Allow-Origin': '*',
                    'Content-Length': len(exported)
                }
                
                if connection.request_version == 'HTTP/1.1':
                    response_headers['ETag'] = self.etag
                
                connection.send_response(200)
                for k, v in response_headers.items():
                    connection.send_header(k, v)
                connection.end_headers()
                connection.wfile.write(exported)
                
            except Exception as e:
                self.logger.error('Error serving playlist: %s' % repr(e))
                connection.send_error(500, 'Generation error')
