import bpy, math, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
rig=bpy.data.objects['GOSHMAN_Rig']
if rig.animation_data:rig.animation_data.action=None
jaw=rig.pose.bones['jaw']
scene=bpy.context.scene
def mesh_world(o):
 deps=bpy.context.evaluated_depsgraph_get()
 e=o.evaluated_get(deps)
 mesh=e.to_mesh()
 try:
  verts=[e.matrix_world@v.co for v in mesh.vertices]
  faces=[tuple(p.vertices) for p in mesh.polygons]
  return verts,BVHTree.FromPolygons([tuple(v) for v in verts],faces)
 finally:e.to_mesh_clear()
def min_dist(a,b):
 va,ta=mesh_world(a);vb,tb=mesh_world(b)
 dist=1e20
 for v in va:
  hit=tb.find_nearest(v)
  if hit[0] is not None:dist=min(dist,hit[3])
 for v in vb:
  hit=ta.find_nearest(v)
  if hit[0] is not None:dist=min(dist,hit[3])
 return round(float(dist),6),bool(ta.overlap(tb))
def tooth_vs_jaw(angle):
 o=bpy.data.objects['Mandible_integrated']
 return {f'{i:02d}':dict(zip(('gap','intersect'),min_dist(o,bpy.data.objects[f'Lower_tooth_{i:02d}']))) for i in range(9)}
samples=[]
for step in range(109):
 angle=54.431*step/108
 jaw.rotation_euler=(math.radians(angle),0,0)
 bpy.context.view_layer.update()
 entry={'angle':round(angle,4),'sides':{}}
 for side in ('L','R'):
  parts={n:bpy.data.objects[f'Jaw_hinge_{n}_{side}'] for n in ('pin','bushing','moving_cap','bearing','retainer','socket')}
  pairs=(('pin','bushing'),('pin','moving_cap'),('bushing','bearing'),('bushing','retainer'),('bushing','socket'),('bushing','moving_cap'),('retainer','moving_cap'))
  entry['sides'][side]={a+'__'+b:dict(zip(('gap','intersect'),min_dist(parts[a],parts[b]))) for a,b in pairs}
  entry['sides'][side]['jaw__socket']=dict(zip(('gap','intersect'),min_dist(bpy.data.objects['Mandible_integrated'],parts['socket'])))
 if step in (0,1,2,3,6,12,24,54,108):
  entry['lower_teeth_vs_jaw']=tooth_vs_jaw(angle)
 samples.append(entry)
 print('JOINT_QA_SAMPLE',step,round(angle,3),flush=True)
out=Path(__file__).parent/'qa_project'/'output'/'bearing_clearance_v22.json'
out.write_text(json.dumps(samples,indent=2),encoding='utf8')
print('JOINT_QA_COMPLETE',str(out),flush=True)
