from gradio_client import Client, handle_file
import os, shutil, sys, time
tok=open(os.path.expanduser('~/.cache/huggingface/token')).read().strip()
S='/private/tmp/claude-501/-Users-mac-dev-workspace-personal-SHIPFAST/5ad65bf0-d8dc-4ea5-a3dc-5eb2fe9392d2/scratchpad'
n=sys.argv[1]; api=sys.argv[2] if len(sys.argv)>2 else '/shape_generation'
c=Client('tencent/Hunyuan3D-2.1', token=tok, verbose=False, httpx_kwargs={'timeout': 900})
r=c.predict(handle_file(f'{S}/gen/{n}.png'), handle_file(f'{S}/gen/{n}.png'), handle_file(f'{S}/gen/{n}b.png'), None, None, 30, 5.0, 1234, 320, True, 8000, False, api_name=api)
f=r[0]['value'] if isinstance(r[0],dict) else r[0]
shutil.copy(f, f'{S}/gen/{n}-mesh.glb'); print('saved', n, f)
