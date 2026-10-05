"""Explicit exec child only. Never imported by standard launcher."""
def main():
 import os,sys,json,logging
 from integration.geo_sample_probe import probe_geo_sample,_result
 from integration.geo_read_factory import create_geo_read_client
 logging.disable(logging.CRITICAL)
 uri=os.environ.pop('GEO_MONGODB_URI','')
 try:result=probe_geo_sample(uri,client_factory=create_geo_read_client)
 except BaseException:result=_result('unavailable',reason='source_unavailable')
 # Only trusted fixed probe result, no values or exceptions.
 sys.stdout.write(json.dumps(result,separators=(',',':')))
if __name__=='__main__':main()
