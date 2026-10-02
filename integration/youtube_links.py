"""Exact outbound YouTube watch/channel-live link grammars. No lookup or availability claim.

This is not a general query exception. Only HTTPS www.youtube.com/watch with
one literal v= identifier, or exact /channel/UC+22/live, is recognized. No fragments, ports, encoded input,
credentials, alternate hosts, list/time/tracking parameters or embeds.
"""
import re
WATCH=re.compile(r'https://www\.youtube\.com/watch\?v=([A-Za-z0-9_-]{11})\Z')
VIDEO=re.compile(r'[A-Za-z0-9_-]{11}\Z')
def youtube_watch(value):
 if not isinstance(value,str):return None
 m=WATCH.fullmatch(value)
 return 'https://www.youtube.com/watch?v='+m.group(1) if m else None

def supplied_video_watch(video_id):
 if not isinstance(video_id,str) or not VIDEO.fullmatch(video_id):return None
 return 'https://www.youtube.com/watch?v='+video_id

CHANNEL=re.compile(r'UC[A-Za-z0-9_-]{22}\Z')
def supplied_channel_watch(channel_id):
 if not isinstance(channel_id,str) or not CHANNEL.fullmatch(channel_id):return None
 return 'https://www.youtube.com/channel/'+channel_id+'/live'

CHANNEL_LIVE=re.compile(r'https://www\.youtube\.com/channel/(UC[A-Za-z0-9_-]{22})/live\Z')
def youtube_channel_live(value):
 if not isinstance(value,str):return None
 m=CHANNEL_LIVE.fullmatch(value)
 return supplied_channel_watch(m.group(1)) if m else None
