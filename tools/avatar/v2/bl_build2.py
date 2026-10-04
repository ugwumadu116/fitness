import bpy, json, os, numpy as np
from mathutils import Vector
S='/private/tmp/claude-501/-Users-mac-dev-workspace-personal-SHIPFAST/5ad65bf0-d8dc-4ea5-a3dc-5eb2fe9392d2/scratchpad/gen'
N=os.environ['N']; OUT=os.environ['OUT']
meta=json.load(open(f'{S}/{N}-atlas.json')); J2=json.load(open(f'{S}/joints2d.json'))[N]['J']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'{S}/{N}-mesh.glb')
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); bpy.context.view_layer.objects.active=mesh
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
d=mesh.modifiers.new('d','DECIMATE'); d.ratio=float(os.environ.get('RATIO','0.12')); bpy.ops.object.modifier_apply(modifier='d')
bpy.ops.object.shade_smooth()
me=mesh.data; co=np.array([v.co[:] for v in me.vertices])
zmin,zmax=co[:,2].min(),co[:,2].max(); xc=(co[:,0].min()+co[:,0].max())/2
# uniform scale by height; x aligned on the torso centre of each photo
def mapping(M, back=False):
    s=(zmax-zmin)/(M['y1']-M['y0'])
    if not back: return lambda x,z: (M['cx']+(x-xc)/s, M['y0']+(zmax-z)/s)
    return lambda x,z: (M['cx']-(x-xc)/s, M['y0']+(zmax-z)/s)       # seen from behind, +X is on the left
F=mapping(meta['front']); Bk=mapping(meta['back'],True)
W,H=meta['front']['W'],meta['front']['H']
uv=me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name='UVMap')
for p in me.polygons:
    back=p.normal.y>0.0
    for li in p.loop_indices:
        v=me.vertices[me.loops[li].vertex_index].co
        px,py=(Bk if back else F)(v.x,v.z)
        uv.data[li].uv=((px/W)*0.5+(0.5 if back else 0.0), 1-py/H)
mat=bpy.data.materials.new('body'); mat.use_nodes=True
bsdf=mat.node_tree.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value=0.7
tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(f'{S}/{N}-atlas.jpg')
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']); me.materials.clear(); me.materials.append(mat)
# joints: photo px -> mesh x,z; depth from the mesh slice
sF=(zmax-zmin)/(meta['front']['y1']-meta['front']['y0'])
def px2mesh(px,py): return (xc+(px-meta['front']['cx'])*sF, zmax-(py-meta['front']['y0'])*sF)
def depth(x,z,mode='mid',r=0.05):
    m=(np.abs(co[:,0]-x)<r)&(np.abs(co[:,2]-z)<r)
    if m.sum()<3: m=(np.abs(co[:,0]-x)<r*2)&(np.abs(co[:,2]-z)<r*2)
    if m.sum()<3: return 0.0
    ys=co[m,1]; return float(ys.min()) if mode=='front' else float((ys.min()+ys.max())/2)
J={}
for k,(px,py) in J2.items():
    x,z=px2mesh(px,py); J[k]=Vector((x,depth(x,z),z))
J['HeadTop_End']=Vector((J['Head'].x,J['Head'].y,zmax))
for s in ('Left','Right'):
    f=J[s+'Foot']; J[s+'Foot']=Vector((f.x,f.y,max(f.z,zmin+0.07)))
    t=J[s+'ToeBase']; ty=depth(t.x,zmin+0.03,'front',0.04)
    J[s+'ToeBase']=Vector((t.x,(f.y+ty)/2,zmin+0.03)); J[s+'Toe_End']=Vector((t.x,ty,zmin+0.02))
arm=bpy.data.armatures.new('Armature'); rig=bpy.data.objects.new('Armature',arm); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode='EDIT'); eb=arm.edit_bones
def bone(n,h,t,p=None):
    b=eb.new('mixamorig:'+n); b.head=J[h] if isinstance(h,str) else h; b.tail=J[t] if isinstance(t,str) else t
    if p: b.parent=eb['mixamorig:'+p]
bone('Hips','Hips','Spine'); bone('Spine','Spine','Spine1','Hips'); bone('Spine1','Spine1','Spine2','Spine'); bone('Spine2','Spine2','Neck','Spine1')
bone('Neck','Neck','Head','Spine2'); bone('Head','Head','HeadTop_End','Neck'); bone('HeadTop_End','HeadTop_End',J['HeadTop_End']+Vector((0,0,0.05)),'Head')
for s in ('Left','Right'):
    bone(s+'Shoulder',s+'Shoulder',s+'Arm','Spine2'); bone(s+'Arm',s+'Arm',s+'ForeArm',s+'Shoulder'); bone(s+'ForeArm',s+'ForeArm',s+'Hand',s+'Arm')
    bone(s+'Hand',s+'Hand',s+'HandEnd',s+'ForeArm'); bone(s+'UpLeg',s+'UpLeg',s+'Leg','Hips'); bone(s+'Leg',s+'Leg',s+'Foot',s+'UpLeg')
    bone(s+'Foot',s+'Foot',s+'ToeBase',s+'Leg'); bone(s+'ToeBase',s+'ToeBase',s+'Toe_End',s+'Foot'); bone(s+'Toe_End',s+'Toe_End',J[s+'Toe_End']+Vector((0,-0.03,0)),s+'ToeBase')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
w=np.array([sum(g.weight for g in v.groups) for v in me.vertices]); print('UNWEIGHTED',int((w<1e-4).sum()),'of',len(w))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_skins=True, export_animations=False, export_image_format='JPEG', export_jpeg_quality=85)
print('EXPORTED',OUT)
