# -*- coding: utf-8 -*-
'''
af1c1onados Playlist Plugin configuration file
'''
import os

# Proxy settings
proxies = {}

# URL for the JSON playlist
url = 'https://af1c1onados.vercel.app/14.AcEStREAM.iDs.w3u'

# Download playlist every N minutes
updateevery = 60

# TV Guide URL
tvgurl = 'https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv_sincolor0.xml.gz'

# Shift the TV Guide time
tvgshift = 0

# Playlist Headers
m3uheadertemplate = u'#EXTM3U url-tvg="{}" tvg-shift={} deinterlace=1 m3uautoload=1 cache=1000\n'.format(tvgurl, tvgshift)

# Channel template
m3uchanneltemplate = u'#EXTINF:-1 group-title="{group}" tvg-name="{tvg}" tvg-id="{tvgid}" tvg-logo="{logo}",{name}\n#EXTGRP:{group}\n{url}\n'
