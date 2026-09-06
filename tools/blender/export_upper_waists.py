"""Export the animated pelvis attachment without rerendering torso textures."""
import json
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/blender/ashgate_upper_rigs.blend'))
path=ROOT/'src/pyg/assets/rendered/upper/sprites.json'
data=json.loads(path.read_text());scene=bpy.context.scene;camera=scene.camera
for name,model in data['models'].items():
    rig=bpy.data.objects[name+' ARMATURE']
    for collection in rig.users_collection:collection.hide_viewport=False
    w,h=model['size'];cw,ch=model['cell']
    scene.render.resolution_x=cw;scene.render.resolution_y=ch
    camera.data.ortho_scale=ch/100;camera.location=(0,h/200,10)
    rest=rig.data.bones['hips']
    pelvis=(rig.data.bones['thigh.L'].head_local+rig.data.bones['thigh.R'].head_local)*.5
    local=rest.matrix_local.inverted() @ pelvis
    for clip,frames in model['clips'].items():
        rig.animation_data.action=bpy.data.actions[name+'/'+clip]
        sockets=[]
        for i in range(frames['count']):
            scene.frame_set(i+1);bpy.context.view_layer.update()
            point=world_to_camera_view(scene,camera,rig.pose.bones['hips'].matrix @ local)
            sockets.append([round(point.x*cw,4),round((1-point.y)*ch,4)])
        frames['waists']=sockets
path.write_text(json.dumps(data,indent=2)+'\n')
print('Exported animated waist sockets for all torso poses.')
