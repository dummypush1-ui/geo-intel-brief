"""Allowlisted HTML boundary for internal report output."""
from html.parser import HTMLParser
from html import escape
import re
from integration.news_view import safe_url
from integration.report_styles import safe_style
class SafeReport(HTMLParser):
 tags={'html','body','table','tr','td','th','thead','tbody','section','div','span','h1','h2','h3','h4','p','ul','ol','li','a','b','strong','i','em','br'}
 def __init__(self):super().__init__(convert_charrefs=True);self.output=[];self.blocked=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','iframe','object'):self.blocked+=1;return
  if self.blocked or tag not in self.tags:return
  kept=[]
  for k,v in attrs:
   if k=='style':
    style=safe_style(v)
    if style:kept.append('style="'+escape(style,quote=True)+'"')
   if tag in ('table','td','th') and k in ('width','cellpadding','cellspacing') and re.fullmatch(r'\d{1,4}%?',v or ''):kept.append(k+'="'+v+'"')
   if tag in ('table','td','th') and k=='align' and v in ('left','center','right'):kept.append('align="'+v+'"')
   if tag=='a' and k=='href':
    url=safe_url(v)
    if url:kept.append('href="'+escape(url,quote=True)+'"')
  self.output.append('<'+tag+(' '+' '.join(kept) if kept else '')+'>')
 def handle_endtag(self,tag):
  if tag in ('script','style','iframe','object'):self.blocked=max(0,self.blocked-1);return
  if not self.blocked and tag in self.tags and tag!='br':self.output.append('</'+tag+'>')
 def handle_data(self,data):
  if not self.blocked:self.output.append(escape(data))
def sanitize_html(value):
 p=SafeReport();p.feed(value);p.close();return ''.join(p.output)
