# -*- coding: utf-8 -*-
'''
All-In-One (AIO) Playlist Plugin configuration file
'''
import os

# Proxy settings (standard architecture)
proxies = {}

# TV Guide URL (optional, can be empty)
tvgurl = ''

# Shift the TV Guide time
tvgshift = 0

# Playlist Headers
m3uheadertemplate = u'#EXTM3U url-tvg="{}" tvg-shift={} deinterlace=1 m3uautoload=1 cache=1000\n'.format(tvgurl, tvgshift)

# Channel template
m3uchanneltemplate = u'#EXTINF:-1 group-title="{group}" tvg-name="{tvg}" tvg-id="{tvgid}" tvg-logo="{logo}",{name}\n#EXTGRP:{group}\n{url}\n'