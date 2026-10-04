from gradio_client import Client, handle_file
import os, shutil, json, sys, time
tok=open(os.path.expanduser('~/.cache/huggingface/token')).read().strip()
S='/private/tmp/claude-501/-Users-mac-dev-workspace-personal-SHIPFAST/5ad65bf0-d8dc-4ea5-a3dc-5eb2fe9392d2/scratchpad'
api=sys.argv[1]
c=Client('tencent/Hunyuan3D-2.1', token=tok, verbose=False, httpx_kwargs={'timeout': 900})
t=time.time()
job=c.submit(handle_file(S+'/joel-front.jpg'), None,None,None,None, 30, 5.0, 1234, 320, True, 8000, False, api_name=api)
while not job.done():
    st=job.status(); print(int(time.time()-t), st.code, getattr(st,'rank',None), getattr(st,'queue_size',None), flush=True); time.sleep(15)
r=job.result()
print('RESULT', r if not isinstance(r,(list,tuple)) else [str(x)[:200] for x in r], flush=True)
tag=api.strip('/')
for i,f in enumerate(r[:2] if isinstance(r,(list,tuple)) else [r]):
    if isinstance(f,str) and os.path.exists(f): shutil.copy(f, S+f'/h3d/{tag}{i}'+os.path.splitext(f)[1]); print('saved', tag, i, f)
