import bpy,math,json
from mathutils.bvhtree import BVHTree
rig=bpy.data.objects['GOSHMAN_Rig']
if rig.animation_data:rig.animation_data.action=None
jaw=rig.pose.bones['jaw']
def get(o):
 deps=bpy.context.evaluated_depsgraph_get();q=o.evaluated_get(deps);m=q.to_mesh()
 try:
  vs=[q.matrix_world@v.co for v in m.vertices]
  return vs,BVHTree.FromPolygons([tuple(v) for v in vs],[tuple(p.vertices) for p in m.polygons])
 finally:q.to_mesh_clear()
def check(a,b):
 av,ab=get(a);bv,bb=get(b)
 ds=[]
 for v in av:
  p=bb.find_nearest(v)
  if p[0] is not None:ds.append(p[3])
 for v in bv:
  p=ab.find_nearest(v)
  if p[0] is not None:ds.append(p[3])
 return {'gap':round(min(ds),6),'hit':bool(ab.overlap(bb))}
for deg in (0,1,5,10,20,35,54.431):
 jaw.rotation_euler=(math.radians(deg),0,0);bpy.context.view_layer.update()
 for side in ('L','R'):
  vals={}
  for a,b in [('Mandible_integrated','Jaw_hinge_bushing_'+side),('Mandible_integrated','Jaw_hinge_moving_cap_'+side),('Jaw_hinge_pin_'+side,'Jaw_hinge_retainer_'+side),('Jaw_hinge_bearing_'+side,'Jaw_hinge_pin_'+side)]:
   vals[a+'--'+b]=check(bpy.data.objects[a],bpy.data.objects[b])
  print('LOAD_PATH',deg,side,json.dumps(vals),flush=True)
