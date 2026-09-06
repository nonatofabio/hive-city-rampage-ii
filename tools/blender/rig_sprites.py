"""Skin the ORIGINAL art to continuous 2D meshes, animate and render in Blender.

No cutout layers: each sprite is one connected UV mesh with blended weights.
Blender --background --python tools/blender/rig_sprites.py -- --preview
Blender --background --python tools/blender/rig_sprites.py -- --render
"""
import argparse
import json
import math
from pathlib import Path
import sys
import time
import bpy
import bmesh
from mathutils import Vector,Matrix,Quaternion
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'src/pyg/assets/rendered'
PREVIEW=ROOT/'art/blender/preview'
SOURCE=ROOT/'art/blender/ashgate_sprite_rigs.blend'
parser=argparse.ArgumentParser()
parser.add_argument('--upper-body',action='store_true',help='Render aiming torso layers for authored lower-body walks')
parser.add_argument('--models',default='',help='Comma-separated models to render; source file still includes all rigs')
parser.add_argument('--aiming',action='store_true',help='Render finely aimed player weapons within each source view')
parser.add_argument('--directions',action='store_true',help='Build the four additional player yaw views')
parser.add_argument('--preview',action='store_true')
parser.add_argument('--render',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if args.directions:SOURCE=ROOT/'art/blender/ashgate_direction_rigs.blend'
if args.aiming:SOURCE=ROOT/'art/blender/ashgate_aim_rigs.blend'
if args.upper_body:
    if not args.aiming:parser.error('--upper-body requires --aiming')
    OUTPUT=OUTPUT/'upper'
    SOURCE=ROOT/'art/blender/ashgate_upper_rigs.blend'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False
scene.cycles.max_bounces=1;scene.cycles.device='CPU'
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_percentage=100
scene.render.fps=24
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world.color=(0,0,0)
V=Vector

SPECS={
'player':{'size':(88,100),'hips':[(.36,.57),(.52,.55)],'knees':[(.26,.76),(.55,.73)],'feet':[(.18,.94),(.64,.89)],'muzzle':(.985,.435)},
'grunt':{'size':(82,90),'hips':[(.37,.58),(.51,.59)],'knees':[(.29,.76),(.55,.78)],'feet':[(.19,.94),(.65,.95)],'muzzle':(.985,.415)},
'rifle':{'size':(82,94),'hips':[(.34,.58),(.50,.56)],'knees':[(.25,.78),(.55,.75)],'feet':[(.16,.95),(.65,.91)],'muzzle':(.98,.475)},
'boss':{'size':(200,238),'hips':[(.37,.68),(.63,.68)],'knees':[(.32,.83),(.69,.83)],'feet':[(.28,.94),(.76,.94)],'muzzle':(.52,.5)},
}

if args.directions:
    SPECS=json.loads((ROOT/'art/blender/directions.json').read_text())

if args.aiming:
    SPECS={'player':SPECS['player'],**json.loads((ROOT/'art/blender/directions.json').read_text())}
    barrels={'player':(.84,.410),'player_ne':(.80,.24),'player_n':(.84,.12),'player_se':(.79,.50),'player_s':(.5,.55)}
    ranges={'player':(-30,30),'player_ne':(-70,-15),'player_n':(-135,-60),'player_se':(15,70),'player_s':(60,135)}
    weapon_rigs=json.loads((ROOT/'art/blender/weapon_rig.json').read_text())
    for name,spec in SPECS.items():
        spec.update(weapon_rigs[name])
        spec['barrel']=barrels[name]
        lo,hi=ranges[name];spec['aim_angles']=list(range(lo,hi+1,5))
        dx=(spec['muzzle'][0]-spec['barrel'][0])*spec['size'][0]
        dy=(spec['muzzle'][1]-spec['barrel'][1])*spec['size'][1]
        spec['barrel_angle']=math.atan2(dy,dx)

def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)


def band(value,lo,hi,feather):
    return smooth((value-lo)/feather)*smooth((hi-value)/feather)


def xyz(spec,p):
    w,h=spec['size'];return V(((p[0]-.5)*w/100,(1-p[1])*h/100,0))


def segment_distance(point,a,b):
    delta=b-a;t=max(0,min(1,(point-a).dot(delta)/delta.length_squared))
    return (point-(a+t*delta)).length


def polygon_distance(point,polygon):
    inside=False;distance=10.
    for i,p in enumerate(polygon):
        a=V(p);b=V(polygon[(i+1)%len(polygon)])
        distance=min(distance,segment_distance(point,a,b))
        if (a.y>point.y)!=(b.y>point.y) and point.x<(b.x-a.x)*(point.y-a.y)/(b.y-a.y)+a.x:
            inside=not inside
    return 0. if inside else distance


def weight_map(spec,nx,ny):
    boss=spec['name']=='boss'
    weights={}
    gun=0 if boss else smooth((nx-.38)/.20)*band(ny,.29,.62,.06)
    if 'weapon' in spec and 'rigid_weapon' not in spec:
        # A capsule follows each view's drawn gun, including foreshortened views.
        a=V(spec['weapon']);b=V(spec['muzzle']);point=V((nx,ny))
        delta=b-a;t=max(0,min(1,(point-a).dot(delta)/delta.length_squared))
        distance=(point-(a+t*delta)).length
        gun=1-smooth((distance-spec['gun_radius'])/.045)
    arm=0.
    if 'rigid_weapon' in spec:
        point=V((nx,ny))
        distance=polygon_distance(point,spec['rigid_weapon'])
        gun=1-smooth(distance/.045)
        arm=(1-smooth((segment_distance(point,V(spec['forearm']),V(spec['weapon']))-.055)/.085))*(1-gun)
    right=smooth((nx-.43)/.12)
    if 'rigid_weapon' in spec:
        # Each armor panel belongs to exactly one bone. Only the hip connector
        # shares weights with the torso; knee and ankle transitions are hinges.
        point=V((nx,ny))
        distances=[min(segment_distance(point,V(hip),V(knee)),
                       segment_distance(point,V(knee),V(foot)))
                   for hip,knee,foot in zip(spec['hips'],spec['knees'],spec['feet'])]
        i=min(range(2),key=distances.__getitem__)
        label=('L','R')[i]
        hip_y=spec['hips'][i][1]
        leg=smooth((ny-hip_y)/.035)*(1-gun-arm)
        section='thigh' if ny<spec['knees'][i][1]-.035 else 'shin' if ny<spec['feet'][i][1]-.045 else 'foot'
        weights[section+'.'+label]=leg
    else:
        leg=smooth((ny-(.63 if boss else .50))/.15)*(1-gun-arm)
        for i,label in enumerate(('L','R')):
            knee=spec['knees'][i][1];foot=spec['feet'][i][1]
            shin=smooth((ny-knee+.075)/.15)
            boot=smooth((ny-foot+.075)/.10)
            side=leg*(right if i else 1-right)
            weights['thigh.'+label]=side*(1-shin)
            weights['shin.'+label]=side*shin*(1-boot)
            weights['foot.'+label]=side*shin*boot
    weights['weapon']=gun if 'weapon' in spec else gun*smooth((nx-.52)/.16) if not boss else 0
    weights['forearm.R']=arm if 'rigid_weapon' in spec else gun-weights['weapon'] if not boss else 0
    rest=1-leg-gun-arm
    if boss:
        arms=(smooth((.31-nx)/.1)+smooth((nx-.72)/.1))*band(ny,.30,.86,.12)*rest
        weights['arm.L']=arms*(1-right);weights['arm.R']=arms*right;rest-=arms
    head=smooth((.30-ny)/.12)*rest
    weights['head']=head
    weights['spine']=(rest-head)*(1-smooth((ny-.46)/.15))
    weights['hips']=max(0,rest-head-weights['spine'])
    return {k:v for k,v in weights.items() if v>.00001}


def build(name,spec):
    spec=dict(spec,name=name)
    coll=bpy.data.collections.new(name+' sprite rig');scene.collection.children.link(coll)
    arm=bpy.data.armatures.new(name+' skeleton');rig=bpy.data.objects.new(name+' ARMATURE',arm);coll.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bones=[('root',(.5,1.0),(.5,.85),None),('hips',(.45,.62),(.45,.51),'root'),('spine',(.45,.52),(.42,.30),'hips'),('head',(.42,.29),(.42,.12),'spine')]
    for i,label in enumerate(('L','R')):
        bones.extend([('thigh.'+label,spec['hips'][i],spec['knees'][i],'hips'),('shin.'+label,spec['knees'][i],spec['feet'][i],'thigh.'+label),('foot.'+label,spec['feet'][i],(spec['feet'][i][0]+.07,spec['feet'][i][1]),'shin.'+label)])
    if name!='boss':bones.extend([('forearm.R',spec.get('forearm',(.40,.38)),spec.get('weapon',(.57,.44)),'spine'),('weapon',spec.get('weapon',(.54,.44)),spec['muzzle'],'forearm.R')])
    else:bones.extend([('arm.L',(.26,.39),(.21,.76),'spine'),('arm.R',(.78,.39),(.83,.76),'spine')])
    for bn,head,tail,parent in bones:
        b=arm.edit_bones.new(bn);b.head=xyz(spec,head);b.tail=xyz(spec,tail)
        if parent:b.parent=arm.edit_bones[parent]
        if bn=='weapon':b.inherit_scale='NONE'
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front=True;rig.display_type='WIRE'
    for b in rig.pose.bones:b.rotation_mode='QUATERNION'
    w,h=spec['size'];cols=math.ceil(w/2);rows=math.ceil(h/2)
    verts=[];faces=[];uvcoords=[]
    for y in range(rows+1):
        for x in range(cols+1):
            nx,ny=x/cols,y/rows
            verts.append(xyz(spec,(nx,ny)));uvcoords.append((nx,1-ny))
    for y in range(rows):
        for x in range(cols):
            a=y*(cols+1)+x;b=a+1;c=a+cols+1;d=c+1
            faces.extend([(a,c,b),(b,c,d)])
    mesh=bpy.data.meshes.new(name+' continuous UV mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name+' ORIGINAL SPRITE',mesh);coll.objects.link(obj)
    uv=mesh.uv_layers.new(name='Original artwork')
    for poly in mesh.polygons:
        for loop in poly.loop_indices:uv.data[loop].uv=uvcoords[mesh.loops[loop].vertex_index]
    mat=bpy.data.materials.new(name+' original RGBA');mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear()
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'art/blender/textures'/f'{name}.png'));tex.image.pack();tex.interpolation='Linear'
    emit=nodes.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=1
    clear=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');out=nodes.new('ShaderNodeOutputMaterial')
    links=mat.node_tree.links;links.new(tex.outputs['Color'],emit.inputs['Color']);links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(clear.outputs[0],mix.inputs[1]);links.new(emit.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
    mesh.materials.append(mat)
    groups={b.name:obj.vertex_groups.new(name=b.name) for b in arm.bones}
    for i,(nx,vy) in enumerate(uvcoords):
        weights=weight_map(spec,nx,1-vy);total=sum(weights.values())
        for bone,value in weights.items():groups[bone].add([i],value/total,'REPLACE')
    if 'rigid_weapon' in spec:
        weapon_group=groups['weapon'].index
        obj['rigid_weapon_vertices']=[v.index for v in mesh.vertices if any(g.group==weapon_group and g.weight>.99999 for g in v.groups)]
        for label in ('L','R'):
            for section in ('thigh','shin','foot'):
                group=groups[section+'.'+label].index
                obj['rigid_'+section+'_'+label]=[v.index for v in mesh.vertices if any(g.group==group and g.weight>.99999 for g in v.groups)]
    if args.upper_body:
        # Remove lower-body faces offline, retaining the complete weapon even
        # when it hangs below the belt. The authored legs draw behind this layer.
        bm=bmesh.new();bm.from_mesh(mesh)
        hem=spec['torso_hem']
        weapon=spec.get('upper_weapon',spec['rigid_weapon'])
        remove=[]
        for face in bm.faces:
            center=face.calc_center_median()
            nx=center.x*100/w+.5;ny=1-center.y*100/h
            limit=hem[-1][1]
            for (ax,ay),(bx,by) in zip(hem,hem[1:]):
                if ax<=nx<=bx:
                    limit=ay+(by-ay)*(nx-ax)/(bx-ax);break
            if ny>limit and polygon_distance(V((nx,ny)),weapon)>0:remove.append(face)
        bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(mesh);bm.free()
    obj.parent=rig
    mod=obj.modifiers.new('Continuous blended skeleton skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
    spec.update(rig=rig,mesh=obj,collection=coll,cell=(w+48,h+48))
    return spec


def set_bone(model,name,head=None,tail=None,offset=None,angle=0):
    rig=model['rig'];rest=rig.data.bones[name]
    if head is not None:
        head,tail=V(head),V(tail);delta=tail-head;original=rest.tail_local-rest.head_local
        rotation=original.rotation_difference(delta).to_matrix()
        matrix=(rotation @ rest.matrix_local.to_3x3()).to_4x4()
        scale=delta.length/original.length
        for i in range(3):matrix[i][1]*=scale
        matrix.translation=head
    else:
        pivot=rest.head_local
        matrix=Matrix.Translation(pivot+V(offset or (0,0,0))) @ Matrix.Rotation(angle,4,'Z') @ Matrix.Translation(-pivot) @ rest.matrix_local
    rig.pose.bones[name].matrix=matrix
    bpy.context.view_layer.update()


def pose(model,action,frame,count,elevation=0):
    rig=model['rig'];boss=model['name']=='boss'
    marine=model['name'].startswith('player')
    for pb in rig.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
    phase=frame/count*math.tau
    moving=action in ('walk','walk_fire')
    kick=[1,.45,.1,0][frame%4] if action=='fire' else .8 if action=='walk_fire' else 0
    wind=math.sin(frame/(count-1)*math.pi) if action=='attack' else 0
    bob=((.022 if marine else .009)*math.cos(phase*2) if moving else .003*math.sin(phase))-(.035*wind if boss else 0)
    if args.upper_body and moving:bob=-bob  # Settle on contact; rise on passing.
    set_bone(model,'hips',offset=(0,bob*.25,0))
    set_bone(model,'spine',offset=(-kick*.006,bob,0),angle=(.006*math.sin(phase) if moving else 0))
    set_bone(model,'head',offset=(-kick*.006,bob*.7,0))
    for i,label in enumerate(('L','R')):
        ph=phase+i*math.pi
        swing=(math.sin(ph)*(.030 if boss else .038 if marine else .025)) if moving else 0
        lift=max(0,math.cos(ph))*(.030 if boss else .034 if marine else .025) if moving else 0
        hip=xyz(model,model['hips'][i])+V((0,bob*.25,0))
        dx,dy=model.get('aim',(1,0))
        knee=xyz(model,model['knees'][i])+V((swing*dx*.5,lift*(.48 if marine else .35)+swing*dy*.25,0))
        foot=xyz(model,model['feet'][i])+V((swing*dx,lift+swing*dy*.5,0))
        if marine and 'rigid_weapon' in model:
            rest_hip=xyz(model,model['hips'][i])
            rest_knee=xyz(model,model['knees'][i])
            rest_foot=xyz(model,model['feet'][i])
            # Forward kinematics: rotate fixed-length segments at actual joints.
            # Frontal views rotate around X, side views around Z.
            axis=V((dy,0,dx)).normalized()
            hip_rotation=Quaternion(axis,.26*math.sin(ph) if moving else 0.)
            knee_rotation=Quaternion(axis,-.75*max(0,math.sin(ph)) if moving else 0.)
            knee=hip+hip_rotation @ (rest_knee-rest_hip)
            foot=knee+(hip_rotation @ knee_rotation) @ (rest_foot-rest_knee)
        set_bone(model,'thigh.'+label,hip,knee)
        set_bone(model,'shin.'+label,knee,foot)
        rest=rig.data.bones['foot.'+label]
        set_bone(model,'foot.'+label,foot,foot+(rest.tail_local-rest.head_local))
    if boss:
        for label,side in [('L',-1),('R',1)]:
            set_bone(model,'arm.'+label,offset=(side*.01*wind,.045*wind+bob,0),angle=side*wind*.025)
    elif 'aim_angles' in model:
        theta=model['barrel_angle']-elevation
        dx,dy=math.cos(theta),-math.sin(theta)
        elbow=xyz(model,model['forearm'])+V((0,bob,0))
        wrist_rest=xyz(model,model['weapon'])
        elbow_rest=xyz(model,model['forearm'])
        wrist=elbow+Matrix.Rotation(elevation*.20,3,'Z') @ (wrist_rest-elbow_rest)
        offset=wrist-wrist_rest+V((-dx*kick*.023,-dy*kick*.023,0))
        set_bone(model,'forearm.R',elbow,wrist_rest+offset)
        set_bone(model,'weapon',offset=offset,angle=elevation)
    elif 'aim' in model:
        dx,dy=model['aim']
        set_bone(model,'forearm.R',offset=(-dx*kick*.012,bob-dy*kick*.012,0))
        set_bone(model,'weapon',offset=(-dx*kick*.023,bob-dy*kick*.023,0))
    else:
        set_bone(model,'forearm.R',offset=(-kick*.012,bob+kick*.003,0),angle=elevation*.35+kick*.008)
        set_bone(model,'weapon',offset=(-kick*.023,bob+kick*.005,0),angle=elevation+kick*.018)
    bpy.context.view_layer.update()


models=[build(name,spec) for name,spec in SPECS.items()]
for model in models:
    rig=model['rig'];rig.animation_data_create();model['clips']={}
    clips={'idle':4,'walk':12,'attack':8} if model['name']=='boss' else {'idle':4,'walk':12,'fire':4,'walk_fire':12}
    variants={name:(name,count,0.) for name,count in clips.items()}
    if args.aiming:
        variants={name+'_aim_'+str(angle):(name,count,model['barrel_angle']-math.radians(angle)) for name,count in clips.items() for angle in model['aim_angles']}
    if model['name']!='boss' and not (args.directions or args.aiming):
        for name,count in clips.items():
            for suffix,angle in [('up',math.radians(6)),('down',-math.radians(6))]:
                variants[name+'_'+suffix]=(name,count,angle)
    for name,(base,count,elevation) in variants.items():
        action=bpy.data.actions.new(model['name']+'/'+name);action.use_fake_user=True;rig.animation_data.action=action
        for frame in range(count+int(base in ('idle','walk','walk_fire'))):
            scene.frame_set(frame+1);pose(model,base,frame%count,count,elevation)
            for pb in rig.pose.bones:
                for path in ('location','rotation_quaternion','scale'):pb.keyframe_insert(path,frame=frame+1)
        model['clips'][name]={'action':action.name,'count':count}

bpy.ops.object.camera_add(location=(0,.5,10));camera=bpy.context.object;scene.camera=camera;camera.name='Sprite orthographic camera';camera.data.type='ORTHO';camera.rotation_euler=(0,0,0)


def activate(model):
    for m in models:
        m['collection'].hide_render=m is not model;m['collection'].hide_viewport=m is not model
    w,h=model['size'];cw,ch=model['cell']
    scene.render.resolution_x=cw;scene.render.resolution_y=ch
    camera.data.ortho_scale=ch/100
    camera.location=(0,h/200,10)
    bpy.context.view_layer.update()


def screen_point(p):
    v=world_to_camera_view(scene,camera,p)
    return [round(v.x*scene.render.resolution_x,4),round((1-v.y)*scene.render.resolution_y,4)]

activate(models[0]);models[0]['rig'].animation_data.action=bpy.data.actions[models[0]['clips'][next(n for n in models[0]['clips'] if n.startswith('walk'))]['action']];scene.frame_start=1;scene.frame_end=13;scene.frame_set(1)
SOURCE.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
if not (args.preview or args.render):sys.exit(0)
output=PREVIEW if args.preview else OUTPUT;output.mkdir(parents=True,exist_ok=True)
started=time.time()
for model in models:
    if args.models and model['name'] not in args.models.split(','):continue
    if args.preview and model is not models[0]:continue
    activate(model);rig=model['rig']
    result={'cell':model['cell'],'anchor':screen_point(xyz(model,model.get('anchor',(.4,.96) if model['name']!='boss' else (.5,.97)))),'clips':{},'size':model['size'],'aim_angles':model.get('aim_angles'),'source':'Blender continuous mesh / blended armature weights'}
    for name,clip in model['clips'].items():
        rig.animation_data.action=bpy.data.actions[clip['action']]
        row=[]
        for i in range(clip['count']):
            scene.frame_set(i+1)
            filename=f"{model['name']}_{name}_{i:02}.png"
            scene.render.filepath=str(output/filename)
            if model['name']!='boss':
                local=rig.data.bones['weapon'].matrix_local.inverted() @ xyz(model,model['muzzle'])
                muzzle=screen_point(rig.pose.bones['weapon'].matrix @ local)
            else:muzzle=screen_point(xyz(model,model['muzzle']))
            entry={'file':filename,'muzzle':muzzle}
            if args.upper_body:
                pelvis=(rig.data.bones['thigh.L'].head_local+rig.data.bones['thigh.R'].head_local)*.5
                local=rig.data.bones['hips'].matrix_local.inverted() @ pelvis
                entry['waist']=screen_point(rig.pose.bones['hips'].matrix @ local)
            if args.aiming:
                local=rig.data.bones['weapon'].matrix_local.inverted() @ xyz(model,model['barrel'])
                entry['barrel']=screen_point(rig.pose.bones['weapon'].matrix @ local)
                local=rig.data.bones['weapon'].matrix_local.inverted() @ xyz(model,model['ejection'])
                entry['ejection']=screen_point(rig.pose.bones['weapon'].matrix @ local)
            row.append(entry)
            bpy.ops.render.render(write_still=True)
        result['clips'][name]={'count':clip['count'],'frames':row}
        print('PROGRESS',model['name'],name,round(time.time()-started,1),flush=True)
    (output/(model['name']+'_frames.json')).write_text(json.dumps(result,indent=2)+'\n')
print('COMPLETE',round(time.time()-started,1),flush=True)
