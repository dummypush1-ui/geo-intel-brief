"""Owner-operated disposable guard fixture. No network, Atlas or credentials.
Only launched inside separately configured3GiB diagnostic cgroup. It allocates
bounded synthetic resident pages, never claims this measures real Mongo usage.
"""
import sys,resource,subprocess,time,os
MiB=1024*1024
resource.setrlimit(resource.RLIMIT_AS,(512*MiB,512*MiB))
mode=sys.argv[1:]
if mode not in (['--below'],['--overflow']):raise SystemExit(2)
children=[]
try:
    if mode==['--below']:
        sizes=[(256,200)]*8+[(256,180)]
        parent=bytearray(350*MiB)
        count=350+8*200+180
    else:
        sizes=[(256,240)]*14
        parent=bytearray(80*MiB)
        count=80+14*240
    for cap,size in sizes:
        code=('import resource,time;resource.setrlimit(resource.RLIMIT_AS,('+str(cap*MiB)+','+str(cap*MiB)+'));x=bytearray('+str(size*MiB)+');print("ready",flush=True);time.sleep(20)')
        p=subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env={})
        children.append(p)
        if p.stdout.readline()!=b'ready\n':raise SystemExit(3)
    if mode==['--overflow']:
        # A functioning OOM-group guard must have killed every member first.
        raise SystemExit(4)
    print('synthetic_resident_mib='+str(count),flush=True)
finally:
    for p in children:
        if p.poll()is None:p.kill()
        p.wait()
