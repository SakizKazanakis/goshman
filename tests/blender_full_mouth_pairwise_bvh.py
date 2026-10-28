import bpy,json,math
from mathutils.bvhtree import BVHTree
from mathutils import Vector
rig=bpy.data.objects['GOSHMAN_Rig']
if rig.animation_data:rig.animation_data.action=None
jaw=rig.pose.bones['jaw']
def geom(o,deps):
 e=o.evaluated_get(deps);me=e.to_mesh()
 try:return BVHTree.FromPolygons([tuple(e.matrix_world@v.co) for v in me.vertices],[tuple(p.vertices) for p in me.polygons])
 finally:e.to_mesh_clear()
perpose=[]
for angle in (0,1,3,5,10,20,35,54.431):
 jaw.rotation_euler=(math.radians(angle),0,0)
 bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
 names=['Upper_gum','Lower_gum','Tongue','Mandible_integrated','Upper_snout','Cheek_L','Cheek_R','Jaw_hinge_moving_cap_L','Jaw_hinge_moving_cap_R','Jaw_hinge_socket_L','Jaw_hinge_socket_R']
 names += [f'Upper_tooth_{i:02d}' for i in range(9)]
 names += [f'Lower_tooth_{i:02d}' for i in range(9)]
 tree={n:geom(bpy.data.objects[n],dep) for n in names}
 pairs=[]
 for i,a in enumerate(names):
  for b in names[i+1:]:
   # Intentionally seated tooth-to-gum is tested, so this is an exploratory
   # matrix: contacts are not automatically interpreted as defects.
   if tree[a].overlap(tree[b]): pairs.append([a,b])
 perpose.append({'angle':angle,'colliding_pairs':pairs})
 print('ALL_COMPONENT_BVH',angle,len(pairs),pairs[:15],flush=True)
for n in ['Upper_gum','Lower_gum']:
 o=bpy.data.objects[n]
 print('GUM_STAT',n,len(o.data.vertices),len(o.data.polygons),o.get('socket_count'),flush=True)
print('FULL_AUDIT',json.dumps(perpose),flush=True)
