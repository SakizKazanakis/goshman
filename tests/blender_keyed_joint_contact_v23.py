import bpy,json,math
from mathutils.bvhtree import BVHTree
rig=bpy.data.objects['GOSHMAN_Rig']
if rig.animation_data:rig.animation_data.action=None
jaw=rig.pose.bones['jaw']
def tree(name):
 obj=bpy.data.objects[name];deps=bpy.context.evaluated_depsgraph_get()
 e=obj.evaluated_get(deps);mesh=e.to_mesh()
 try:return BVHTree.FromPolygons([tuple(e.matrix_world@v.co) for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons])
 finally:e.to_mesh_clear()
results=[]
for deg in (0,1,5,15,30,54.431):
 jaw.rotation_euler=(math.radians(deg),0,0)
 bpy.context.view_layer.update()
 row={'angle_deg':deg,'sides':{}}
 for side in ('L','R'):
  bus=tree('Jaw_hinge_bushing_'+side)
  shell=tree('Mandible_integrated')
  pin=tree('Jaw_hinge_pin_'+side)
  keys=[]
  for suffix in ('A','B'):
   k=tree('Jaw_hinge_key_'+side+'_'+suffix)
   keys.append({'name':suffix,'hits_bushing':len(k.overlap(bus)),'hits_mandible':len(k.overlap(shell)),'hits_pin':len(k.overlap(pin))})
  row['sides'][side]={'keys':keys,'bushing_shell':len(bus.overlap(shell)),'pin_bushing':len(pin.overlap(bus))}
 results.append(row)
 print('KEYED_JOINT_QA',json.dumps(row),flush=True)
