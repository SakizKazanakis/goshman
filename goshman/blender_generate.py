"""GOSHMAN Blender runtime. Execute ONLY in Blender: blender -b --python ... -- --project X.

Produces editable mesh objects, mechanical armature, test poses, material node graphs,
FBX/GLB and sprite frames. This module intentionally does not import external AI code.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

try:
    import bpy
    from mathutils import Vector
except ImportError as exc:
    raise SystemExit("This program must be run by Blender Python") from exc

RIG = None
M = {}
PARTS = []


def mat(name, rgb, metallic=0.0, roughness=.62):
    c = tuple(int(rgb[i:i+2], 16)/255 for i in (1, 3, 5))
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*c, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*c, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    M[name] = material
    return material


def record(obj, material, bone=None):
    obj.name = obj.name.replace(".", "_") if obj.name.startswith(("Sphere", "Cube", "Cylinder", "Cone", "Torus")) else obj.name
    obj.data.materials.clear()
    obj.data.materials.append(M[material])
    if bone:
        world = obj.matrix_world.copy()
        obj.parent = RIG
        obj.parent_type = "BONE"
        obj.parent_bone = bone
        obj.matrix_world = world
    PARTS.append(obj)
    return obj


def ellipsoid(name, xyz, size, material, bone=None, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    return record(obj, material, bone)


def box(name, xyz, size, material, bone=None, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Rounded edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        if hasattr(mod, 'affect'):
            mod.affect = 'EDGES'
        mod2 = obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return record(obj, material, bone)


def cylinder(name, xyz, radius, depth, material, bone=None, vertices=24, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=xyz)
    obj = bpy.context.object
    obj.name = name
    if rotation:
        obj.rotation_euler = rotation
    return record(obj, material, bone)


def capsule_between(name, a, b, radius, material, bone=None, r2=None):
    v1, v2 = Vector(a), Vector(b)
    mid = (v1+v2)*.5
    direction = v2-v1
    bpy.ops.mesh.primitive_cone_add(vertices=18, radius1=radius, radius2=r2 if r2 is not None else radius,
                                    depth=direction.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return record(obj, material, bone)


def star(name, xyz, outer, material, bone=None):
    # Five-point front-facing 3D mesh; flat plate extruded in positive y direction.
    cx, cy, cz = xyz
    outline = []
    for i in range(10):
        angle = math.pi/2 + i*math.pi/5
        r = outer if i % 2 == 0 else outer*.43
        outline.append((cx + r*math.cos(angle), cz + r*math.sin(angle)))
    coords = [(x, cy+side*.065, z) for side in (-1, 1) for x,z in outline]
    faces = []
    for i in range(1, 9):
        faces.append((0, i+1, i))
        faces.append((10, 10+i, 10+i+1))
    for i in range(10):
        j = (i+1) % 10
        faces.append((i, j, 10+j, 10+i))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(coords, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return record(obj, material, bone)


def make_rig():
    global RIG
    arm = bpy.data.armatures.new("GOSHMAN_armature")
    RIG = bpy.data.objects.new("GOSHMAN_Rig", arm)
    bpy.context.collection.objects.link(RIG)
    bpy.context.view_layer.objects.active = RIG
    RIG.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bones = [
        ("root", (0, 0, 0.05), (0,0,1.95), None),
        ("pelvis", (0,0,1.95), (0,0,2.55), "root"),
        ("torso", (0,0,2.55), (0,0,4.2), "pelvis"),
        ("neck", (0,0,4.2), (0,0,4.48), "torso"),
        ("head", (0,0,4.48), (0,0,5.42), "neck"),
        ("jaw", (0,-.38,4.75), (0,-.7,4.52), "head"),
        ("eye.L", (-.36,-.57,5.21), (-.36,-.81,5.21), "head"),
        ("eye.R", (.36,-.57,5.21), (.36,-.81,5.21), "head"),
    ]
    for side, sign in (("L", -1), ("R", 1)):
        bones += [
            ("upper_arm."+side, (sign*.78,0,4.0), (sign*1.17,0,3.40), "torso"),
            ("forearm."+side, (sign*1.17,0,3.40), (sign*1.33,-.03,2.85), "upper_arm."+side),
            ("hand."+side, (sign*1.33,-.03,2.85), (sign*1.37,-.13,2.56), "forearm."+side),
            ("thigh."+side, (sign*.43,0,2.12), (sign*.51,0,1.32), "pelvis"),
            ("shin."+side, (sign*.51,0,1.32), (sign*.54,-.02,.58), "thigh."+side),
            ("foot."+side, (sign*.54,-.02,.58), (sign*.54,-.39,.24), "shin."+side),
        ]
        for finger in range(4):
            f = "finger%d.%s" % (finger, side)
            hx = sign*(1.19 + .10*finger)
            bones.append((f, (hx,-.22,2.57), (hx,-.35,2.32), "hand."+side))
    start = (0,.54,2.06)
    for i in range(7):
        next_point = (0,.54+(i+1)*.30,2.06-(i+1)*.15)
        bones.append(("tail_%02d" % (i+1), start, next_point,
                      "pelvis" if i == 0 else "tail_%02d" % i))
        start = next_point
    for name, head, tail, parent in bones:
        b = arm.edit_bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    RIG.select_set(False)
    for pose_bone in RIG.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    return RIG


def build(spec):
    make_rig()
    scale = float(spec.get("head_scale", 1.0))
    snout = float(spec.get("snout_length", 1.0))
    eye = float(spec.get("eye_scale", 1.0))
    detail = int(spec.get("armor_detail", 2))
    p = spec.get("palette", {})
    mat("Scales", p.get("scales", "#59892b"), roughness=.52)
    mat("Belly", p.get("belly", "#dab967"), roughness=.68)
    mat("Leather", p.get("leather", "#794026"), roughness=.73)
    mat("Metal", p.get("metal", "#869293"), metallic=.9, roughness=.27)
    mat("Gold", p.get("gold", "#e9b324"), metallic=.75, roughness=.26)
    mat("Mouth", p.get("mouth", "#63212a"), roughness=.8)
    mat("Black", "#111419", roughness=.28)
    mat("White", "#eeeedb", roughness=.35)
    mat("Iris", "#a8aa44", roughness=.3)
    mat("Sole", "#29201b", roughness=.88)
    # Torso, vest, mechanically separated neck and hip.
    ellipsoid("Torso_core", (0,0,3.29), (.79,.51,1.04), "Scales", "torso")
    for i in range(6):
        z = 2.70 + i*.23
        box("Belly_plate_%02d"%i, (0,-.505,z), (1.03,.135,.215), "Belly", "torso", .045)
    box("Vest_left", (-.57,-.49,3.36), (.29,.19,1.62), "Leather", "torso")
    box("Vest_right", (.57,-.49,3.36), (.29,.19,1.62), "Leather", "torso")
    box("Vest_back", (0,.47,3.34), (1.28,.15,1.60), "Leather", "torso")
    for side, x in (("L",-.68),("R",.68)):
        for j in range(9):
            ellipsoid("Vest_stud_%s_%02d"%(side,j), (x,-.605,2.65+j*.18), (.037,.035,.037),"Metal","torso",10,6)
    ellipsoid("Pelvis_core",(0,0,2.17),(.64,.44,.40),"Scales","pelvis")
    box("Leather_belt",(0,-.42,2.28),(1.40,.17,.19),"Leather","pelvis")
    star("Belt_sheriff_star",(0,-.535,2.32),.24,"Gold","pelvis")
    cylinder("Neck_shaft",(0,0,4.28),.26,.40,"Metal","neck")
    for i in range(3):
        cylinder("Neck_rib_%d"%i,(0,0,4.15+i*.13),.33,.07,"Metal","neck")
    # Crocodile skull: prominent cheek bones, tapered muzzle and lower jaw.
    ellipsoid("Head_cranium", (0,0,5.03),(.68*scale,.57*scale,.69*scale),"Scales","head")
    ellipsoid("Upper_snout", (0,-.57*snout,4.88),(.70*scale,.51*snout,.27*scale),"Scales","head")
    for side, sign in (("L",-1),("R",1)):
        ellipsoid("Cheek_"+side,(sign*.53*scale,-.22,4.78),(.28,.29,.24),"Scales","head")
        ellipsoid("Nostril_"+side,(sign*.30*scale,-1.01*snout,5.01),(.095,.05,.07),"Black","head",16,8)
        # All eyes are discrete mechanical elements and parented to their own controls.
        ellipsoid("Eyeball_"+side,(sign*.35*scale,-.53,5.26),(.245*eye,.16,.258*eye),"White","eye."+side)
        ellipsoid("Iris_"+side,(sign*.35*scale,-.685,5.26),(.129*eye,.059,.135*eye),"Iris","eye."+side)
        ellipsoid("Pupil_"+side,(sign*.35*scale,-.736,5.26),(.068*eye,.032,.077*eye),"Black","eye."+side)
        ellipsoid("Eyebrow_"+side,(sign*.35*scale,-.54,5.59),(.29,.11,.095),"Leather","head")
    ellipsoid("Lower_jaw",(0,-.56*snout,4.45),(.66*scale,.56*snout,.20),"Belly","jaw")
    ellipsoid("Tongue",(0,-.76*snout,4.61),(.27,.35*snout,.055),"Mouth","jaw")
    for i in range(9):
        # Rows of separated teeth with opposing attachment points.
        x = -.50 + i*.125
        cylinder("Upper_tooth_%02d"%i,(x,-.95*snout,4.675),.047,.19,"White","head",12)
        cylinder("Lower_tooth_%02d"%i,(x,-.89*snout,4.63),.042,.14,"White","jaw",12)
    # Hat and star: independent hat elements follow the head.
    cylinder("Hat_brim",(0,0,5.78),1.07,.09,"Leather","head",48)
    cylinder("Hat_crown",(0,0,6.00),.61,.39,"Leather","head",48)
    cylinder("Hat_band",(0,0,5.88),.63,.10,"Sole","head",48)
    star("Hat_sheriff_star",(0,-.655,6.02),.22,"Gold","head")
    # Legs, thigh-chaps, knee mechanisms, boots and soles.
    for side, sign in (("L",-1),("R",1)):
        x = sign*.46
        ellipsoid("Thigh_"+side,(x,0,1.76),(.38,.40,.53),"Leather","thigh."+side)
        ellipsoid("Knee_hinge_"+side,(x,0,1.29),(.26,.28,.22),"Metal","shin."+side)
        ellipsoid("Shin_"+side,(x,0,.91),(.29,.30,.45),"Scales","shin."+side)
        box("Boot_shaft_"+side,(x,-.08,.52),(.60,.62,.70),"Leather","foot."+side)
        ellipsoid("Boot_toe_"+side,(x,-.37,.24),(.35,.53,.24),"Leather","foot."+side)
        box("Boot_sole_"+side,(x,-.40,.09),(.72,.98,.12),"Sole","foot."+side,.04)
        cylinder("Boot_strap_rivet_"+side,(x,-.39,.57),.095,.08,"Metal","foot."+side,16, (math.pi/2,0,0))
        # Shoulders arms metallic hinge supports and articulate wrist/fingers.
        x_sh = sign*.88
        ellipsoid("Shoulder_socket_"+side,(x_sh,0,3.96),(.25,.27,.25),"Metal","upper_arm."+side)
        capsule_between("Upper_arm_shell_"+side,(x_sh,0,3.84),(sign*1.14,0,3.43),.25,"Scales","upper_arm."+side,.24)
        ellipsoid("Elbow_hinge_"+side,(sign*1.18,0,3.4),(.20,.20,.19),"Metal","forearm."+side)
        capsule_between("Forearm_shell_"+side,(sign*1.2,0,3.38),(sign*1.33,-.03,2.88),.21,"Scales","forearm."+side,.18)
        ellipsoid("Palm_"+side,(sign*1.35,-.06,2.7),(.23,.17,.24),"Metal","hand."+side)
        for finger in range(4):
            fx = sign*(1.19 + finger*.105)
            b = "finger%d.%s"%(finger,side)
            capsule_between("Finger_base_%s_%d"%(side,finger),(fx,-.15,2.6),(fx,-.23,2.38),.045,"Metal",b,.034)
            capsule_between("Claw_%s_%d"%(side,finger),(fx,-.23,2.38),(fx,-.32,2.22),.037,"Metal",b,0.0)
    # Tail chain: seven overlapping but independent rigid segments with dorsal spikes.
    starts = [(0,.54+i*.30,2.06-i*.15) for i in range(8)]
    for i in range(7):
        a, b = starts[i], starts[i+1]
        radius = .36*(1-i/8)
        bone = "tail_%02d" % (i+1)
        capsule_between("Tail_segment_%02d"%i,a,b,radius,"Scales",bone,radius*.88)
        # ventral scutes and dorsal spike geometry are separate rigid pieces
        mid = tuple((a[j]+b[j])/2 for j in range(3))
        ellipsoid("Tail_belly_%02d"%i,(mid[0],mid[1],mid[2]-.19),(radius*.8,.16,.075),"Belly",bone,16,8)
        ellipsoid("Tail_spike_%02d"%i,(mid[0],mid[1],mid[2]+radius*.80),(.095,.10,.13),"Belly",bone,12,8)
        if detail >= 2:
            for j in range(4):
                ellipsoid("Tail_scute_%d_%d"%(i,j),(-radius*.55+j*radius*.36,mid[1],mid[2]+radius*.45),
                          (.075,.13,.05),"Scales",bone,12,8)
    if detail >= 1:
        for i in range(4):
            for s in (-1,1):
                ellipsoid("Temple_scute_%d_%s"%(i,s),(s*.59,-.04+i*.20,5.05),(.105,.11,.06),"Scales","head",12,8)
    return len(PARTS)


def reset_pose():
    for bone in RIG.pose.bones:
        bone.rotation_euler = (0,0,0)
        bone.location = (0,0,0)


def animate():
    # Animation actions are genuine transform F-curves on an armature, not static images.
    tracks = {
        "idle": {1:{"head":(0,0,0)},12:{"head":(.035,0,.025)},24:{"head":(0,0,0)}},
        "jaw_open": {1:{"jaw":(0,0,0)},12:{"jaw":(-.68,0,0)},24:{"jaw":(0,0,0)}},
        "jumpscare": {1:{"jaw":(0,0,0)},5:{"head":(-.30,0,0),"jaw":(-.9,0,0),"upper_arm.L":(0,0,-.45),"upper_arm.R":(0,0,.45)},10:{"head":(-.10,0,0),"jaw":(-.95,0,0)},16:{"head":(0,0,0),"jaw":(0,0,0)}},
        "look_left": {1:{"head":(0,0,0)},10:{"head":(0,0,.35)},18:{"head":(0,0,0)}},
        "angry": {1:{"head":(0,0,0)},8:{"head":(-.14,0,0),"jaw":(-.25,0,0)},16:{"head":(0,0,0),"jaw":(0,0,0)}},
        "wave": {1:{"upper_arm.R":(0,0,0)},9:{"upper_arm.R":(0,0,.9),"forearm.R":(-.3,0,0)},18:{"forearm.R":(.15,0,0)},26:{"upper_arm.R":(0,0,0),"forearm.R":(0,0,0)}},
        "tail_sway": {1:{"tail_01":(0,0,-.17)},12:{"tail_01":(0,0,.19)},24:{"tail_01":(0,0,-.17)}},
        "walk": {1:{"thigh.L":(.25,0,0),"thigh.R":(-.25,0,0)},7:{"thigh.L":(-.25,0,0),"thigh.R":(.25,0,0)},13:{"thigh.L":(.25,0,0),"thigh.R":(-.25,0,0)}},
        "attack": {1:{"head":(0,0,0)},6:{"head":(-.2,0,0),"jaw":(-.8,0,0)},14:{"head":(0,0,0),"jaw":(0,0,0)}},
        "a_pose":{1:{"upper_arm.L":(0,0,-.30),"upper_arm.R":(0,0,.30)}},
        "t_pose":{1:{"upper_arm.L":(0,0,-.95),"upper_arm.R":(0,0,.95)}},
    }
    for name, keys in tracks.items():
        reset_pose()
        # First key entire armature to prevent inherited animation transforms.
        armature_action = bpy.data.actions.new("GOSHMAN_"+name)
        slot = armature_action.slots.new(id_type="OBJECT", name=RIG.name)
        RIG.animation_data_create()
        RIG.animation_data.action = armature_action
        RIG.animation_data.action_slot = slot
        for frame, rotations in keys.items():
            for bone_name, euler in rotations.items():
                pb = RIG.pose.bones[bone_name]
                pb.rotation_euler = euler
                pb.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone_name)
        armature_action.use_fake_user = True
    reset_pose()
    return list(tracks)


def setup_scene(size):
    world = bpy.context.scene.world
    world.color = (.16,.16,.16)
    world.use_nodes = True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.22,.25,.29,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .65
    for name, xyz, power, shape in (("Key",(4,-6,9),1100,5),("Fill",(-6,-3,6),800,5)):
        light = bpy.data.lights.new(name,"AREA")
        light.energy=power
        light.shape='DISK'; light.size=shape
        obj=bpy.data.objects.new(name,light); bpy.context.collection.objects.link(obj); obj.location=xyz
    camera_data = bpy.data.cameras.new("FrontCam")
    camera = bpy.data.objects.new("FrontCam",camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location=(0,-12,5)
    direction=Vector((0,-.1,3.1))-camera.location
    camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO';camera_data.ortho_scale=7.8
    sc=bpy.context.scene; sc.camera=camera
    sc.render.engine='CYCLES'
    sc.cycles.samples=16
    sc.render.film_transparent=True
    sc.render.resolution_x=size;sc.render.resolution_y=size;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.render.fps=24
    return camera


def do_exports(project_folder, do_render, do_export, size, clips):
    out=project_folder/'output';out.mkdir(exist_ok=True)
    blend=out/'crocodile_cowboy.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if do_export:
        try:
            bpy.ops.export_scene.gltf(filepath=str(out/'crocodile_cowboy.glb'),export_format='GLB',export_animations=True, export_animation_mode='ACTIONS')
        except Exception as e:
            print('EXPORT_GLTF_FAILED:',str(e),file=sys.stderr)
        try:
            bpy.ops.export_scene.fbx(filepath=str(out/'crocodile_cowboy.fbx'),
                                      add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True)
        except Exception as e:
            print('EXPORT_FBX_FAILED:',str(e),file=sys.stderr)
    if do_render:
        for clip in ("idle","jaw_open","jumpscare","walk","wave"):
            if bpy.data.actions.get("GOSHMAN_"+clip) is None:
                continue
            RIG.animation_data.action=bpy.data.actions["GOSHMAN_"+clip]
            RIG.animation_data.action_slot=RIG.animation_data.action.slots[0]
            directory=out/'sprites'/clip
            directory.mkdir(parents=True,exist_ok=True)
            nframes={"idle":24,"jaw_open":24,"jumpscare":16,"walk":13,"wave":26}[clip]
            for index in range(1,nframes+1):
                bpy.context.scene.frame_set(index)
                bpy.context.scene.render.filepath=str(directory/(f"{clip}_{index:04d}.png"))
                bpy.ops.render.render(write_still=True)

    # Always produce an actual Blender camera render for visual QA, independent of full sprite sequences.
    sc = bpy.context.scene
    idle = bpy.data.actions.get("GOSHMAN_idle")
    if idle is not None:
        RIG.animation_data.action = idle
        RIG.animation_data.action_slot = idle.slots[0]
    sc.frame_set(1)
    previous_size = (sc.render.resolution_x, sc.render.resolution_y)
    previous_samples = sc.cycles.samples
    sc.render.resolution_x = min(size, 384)
    sc.render.resolution_y = min(size, 384)
    sc.cycles.samples = 8
    sc.render.filepath = str(out / "preview_front.png")
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        sc.render.resolution_x, sc.render.resolution_y = previous_size
        sc.cycles.samples = previous_samples

    counts={"mesh_objects":len([x for x in bpy.data.objects if x.type=='MESH']),
            "bones":len(RIG.data.bones),"actions":len(clips),"saved_blend":str(blend),
            "glb_exists":(out/'crocodile_cowboy.glb').exists(),
            "fbx_exists":(out/'crocodile_cowboy.fbx').exists()}
    (out/'build_report.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
    print('GOSHMAN_REPORT='+json.dumps(counts))


def main():
    arg=sys.argv.index('--') if '--' in sys.argv else len(sys.argv)
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True)
    parser.add_argument('--size',type=int,default=512)
    parser.add_argument('--render',choices=('0','1'),default='0')
    parser.add_argument('--export',choices=('0','1'),default='1')
    args=parser.parse_args(sys.argv[arg+1:])
    folder=Path(args.project).resolve(strict=True)
    raw=json.loads((folder/'project.json').read_text('utf-8'))
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    count=build(raw['spec']); clips=animate();setup_scene(args.size)
    do_exports(folder,args.render=='1',args.export=='1',args.size,clips)
    print('Built geometry objects:', count)

if __name__ == '__main__':
    main()
