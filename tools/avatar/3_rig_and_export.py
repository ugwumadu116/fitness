import bpy, bmesh, mathutils, math
from mathutils import Vector
S='/private/tmp/claude-501/-Users-mac-dev-workspace-personal-SHIPFAST/5ad65bf0-d8dc-4ea5-a3dc-5eb2fe9392d2/scratchpad'
OUT='/Users/mac/dev/workspace/personal/SHIPFAST/fitness/models/joel.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=S+'/h3d/joel-shape.glb')
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
# bake transforms so vertex coords are world coords (Blender Z-up, faces -Y)
for o in list(bpy.context.scene.objects):
    if o!=mesh and o.type!='MESH': pass
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); bpy.context.view_layer.objects.active=mesh
mesh.parent=None if mesh.parent is None else mesh.parent
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# lighter mesh for the web
dec=mesh.modifiers.new('dec','DECIMATE'); dec.ratio=0.12
bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.shade_smooth()
bb=[Vector(c) for c in mesh.bound_box]
xmin=min(v.x for v in bb); xmax=max(v.x for v in bb); zmin=min(v.z for v in bb); zmax=max(v.z for v in bb)
print('BBOX',xmin,xmax,zmin,zmax, len(mesh.data.polygons))

# image <-> mesh mapping (front photo, 1632x2582 px; silhouette x 136..1504, y 177..2523)
IW,IH=1632,2582; PX0,PX1,PY0,PY1=136,1504,177,2523
sx=(xmax-xmin)/(PX1-PX0); sz=(zmax-zmin)/(PY1-PY0)
def px2mesh(px,py): return (xmin+(px-PX0)*sx, zmax-(py-PY0)*sz)
def mesh2px(x,z): return (PX0+(x-xmin)/sx, PY0+(zmax-z)/sz)

# UVs: front-facing faces sample the front half, back-facing faces the mirrored back half
me=mesh.data
uv=me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
for p in me.polygons:
    back = p.normal.y > 0.05
    for li in p.loop_indices:
        v=me.vertices[me.loops[li].vertex_index].co
        px,py=mesh2px(v.x,v.z)
        u=px/IW
        if back: u=(IW-1-px)/IW
        uv.data[li].uv=((u*0.5)+(0.5 if back else 0), 1-py/IH)
mat=bpy.data.materials.new('joel'); mat.use_nodes=True
bsdf=mat.node_tree.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value=0.75
tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(S+'/atlas.jpg')
mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
me.materials.clear(); me.materials.append(mat)

# joints from the photo (px), depth = centre of the body slice there
import numpy as np
co=np.array([v.co[:] for v in me.vertices])
def depth(x,z,r=0.05,mode='mid'):
    m=(np.abs(co[:,0]-x)<r)&(np.abs(co[:,2]-z)<r)
    if m.sum()<3: return 0.0
    ys=co[m,1]
    return float(ys.min()) if mode=='front' else float((ys.min()+ys.max())/2)
J={}
def j(name,px,py,mode='mid'):
    x,z=px2mesh(px,py); J[name]=Vector((x,depth(x,z,mode=mode),z))
cx=820
j('Hips',cx,1420); j('Spine',cx,1260); j('Spine1',cx,1080); j('Spine2',cx,880); j('Neck',cx,600); j('Head',cx,520)
J['HeadTop_End']=Vector((J['Head'].x,J['Head'].y,zmax))
# character left = image right = +X
for side,sgn in (('Left',1),('Right',-1)):
    m=lambda px: cx+sgn*(px-cx)
    j(side+'Shoulder',m(890),615); j(side+'Arm',m(1095),665); j(side+'ForeArm',m(1310),1110); j(side+'Hand',m(1446),1412)
    j(side+'HandEnd',m(1478),1555)
    j(side+'UpLeg',m(950),1440); j(side+'Leg',m(949),1942); j(side+'Foot',m(965),2380)
    j(side+'ToeBase',m(985),2480,'front'); 
    t=J[side+'ToeBase']; J[side+'ToeBase']=Vector((t.x,t.y+0.03,zmin+0.025)); J[side+'Toe_End']=Vector((t.x,t.y-0.07,zmin+0.02))
    f=J[side+'Foot']; J[side+'Foot']=Vector((f.x,f.y,max(f.z,zmin+0.07)))
for k,v in J.items(): print('J',k,[round(c,3) for c in v])

arm=bpy.data.armatures.new('Armature'); rig=bpy.data.objects.new('Armature',arm); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode='EDIT')
eb=arm.edit_bones
def bone(name,head,tail,parent=None):
    b=eb.new('mixamorig:'+name); b.head=J[head] if isinstance(head,str) else head; b.tail=J[tail] if isinstance(tail,str) else tail
    if parent: b.parent=eb['mixamorig:'+parent]; b.use_connect=False
    return b
bone('Hips','Hips','Spine'); bone('Spine','Spine','Spine1','Hips'); bone('Spine1','Spine1','Spine2','Spine'); bone('Spine2','Spine2','Neck','Spine1')
bone('Neck','Neck','Head','Spine2'); bone('Head','Head','HeadTop_End','Neck')
bone('HeadTop_End','HeadTop_End',J['HeadTop_End']+Vector((0,0,0.05)),'Head')
for s in ('Left','Right'):
    bone(s+'Shoulder',s+'Shoulder',s+'Arm','Spine2'); bone(s+'Arm',s+'Arm',s+'ForeArm',s+'Shoulder')
    bone(s+'ForeArm',s+'ForeArm',s+'Hand',s+'Arm'); bone(s+'Hand',s+'Hand',s+'HandEnd',s+'ForeArm')
    bone(s+'UpLeg',s+'UpLeg',s+'Leg','Hips'); bone(s+'Leg',s+'Leg',s+'Foot',s+'UpLeg')
    bone(s+'Foot',s+'Foot',s+'ToeBase',s+'Leg'); bone(s+'ToeBase',s+'ToeBase',s+'Toe_End',s+'Foot')
    bone(s+'Toe_End',s+'Toe_End',J[s+'Toe_End']+Vector((0,-0.03,0)),s+'ToeBase')
bpy.ops.object.mode_set(mode='OBJECT')
# skin with automatic (heat) weights
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty=[vg.name for vg in mesh.vertex_groups]
w=np.zeros(len(me.vertices))
for v in me.vertices:
    w[v.index]=sum(g.weight for g in v.groups)
print('UNWEIGHTED', int((w<1e-4).sum()), 'of', len(w))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_skins=True, export_animations=False, export_image_format='JPEG', export_jpeg_quality=85, export_apply=False)
print('EXPORTED')
