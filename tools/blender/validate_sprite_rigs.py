"""Run in Blender against the saved source to check real skinning and topology."""
import json
import math
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2]
aiming='--aiming' in sys.argv
directional='--directions' in sys.argv
source='ashgate_aim_rigs.blend' if aiming else 'ashgate_direction_rigs.blend' if directional else 'ashgate_sprite_rigs.blend'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/blender'/source))
report={}
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    mods=[m for m in obj.modifiers if m.type=='ARMATURE']
    assert len(mods)==1 and mods[0].object.type=='ARMATURE',obj.name
    graph=[[] for _ in obj.data.vertices]
    for edge in obj.data.edges:
        a,b=edge.vertices;graph[a].append(b);graph[b].append(a)
    seen={0};pending=[0]
    while pending:
        for nxt in graph[pending.pop()]:
            if nxt not in seen:seen.add(nxt);pending.append(nxt)
    assert len(seen)==len(graph),'Detached cutout geometry: '+obj.name
    totals=[sum(g.weight for g in v.groups) for v in obj.data.vertices]
    assert min(totals)>.999 and max(totals)<1.001,'Unnormalized skin weights'
    blended=sum(sum(g.weight>.01 for g in v.groups)>1 for v in obj.data.vertices)
    assert blended>100,'No meaningful joint blending'
    report[obj.name]={'vertices':len(graph),'connected_components':1,'bones':len(mods[0].object.data.bones),'blended_vertices':blended}
    if aiming:
        ids=list(obj['rigid_weapon_vertices'])
        assert len(ids)>20,'No rigid weapon region'
        samples=ids[::max(1,len(ids)//12)]
        rig=mods[0].object
        for collection in obj.users_collection:collection.hide_viewport=False
        actions=[a for a in bpy.data.actions if a.name.startswith(rig.name.split(' ')[0]+'/walk_aim_')]
        max_error=0.;leg_error=0.;knee_angles=[]
        leg_samples=[]
        for label in ('L','R'):
            for section in ('thigh','shin','foot'):
                panel=list(obj['rigid_'+section+'_'+label])
                # The SE gun occludes almost the entire right thigh.
                minimum=2 if obj.name.startswith('player_se ') and section=='thigh' and label=='R' else 9
                assert len(panel)>=minimum,('Missing rigid leg panel',obj.name,section,label)
                leg_samples.append(panel[::max(1,len(panel)//12)])
        for action in (actions[0],actions[-1]):
            rig.animation_data.action=action
            for frame in (1,4,7,10,12):
                bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
                evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
                for a,b in zip(samples,samples[1:]):
                    rest=(obj.data.vertices[a].co-obj.data.vertices[b].co).length
                    current=(mesh.vertices[a].co-mesh.vertices[b].co).length
                    if rest>1e-6:max_error=max(max_error,abs(current/rest-1))
                for panel in leg_samples:
                    for a,b in zip(panel,panel[1:]):
                        rest=(obj.data.vertices[a].co-obj.data.vertices[b].co).length
                        current=(mesh.vertices[a].co-mesh.vertices[b].co).length
                        if rest>1e-6:leg_error=max(leg_error,abs(current/rest-1))
                evaluated.to_mesh_clear()
                thigh=rig.pose.bones['thigh.L'];shin=rig.pose.bones['shin.L']
                knee_angles.append(math.degrees((thigh.tail-thigh.head).angle(shin.tail-shin.head)))
        assert leg_error<.0002,('Leg armor deformed',obj.name,leg_error)
        report[obj.name]['max_leg_panel_scale_error']=leg_error
        assert max_error<.0002,('Gun shape deformed',obj.name,max_error)
        assert max(knee_angles)-min(knee_angles)>8,('Insufficient knee flex',obj.name,knee_angles)
        report[obj.name]['rigid_weapon_vertices']=len(ids)
        report[obj.name]['max_weapon_scale_error']=max_error
        report[obj.name]['knee_flex_range_degrees']=[min(knee_angles),max(knee_angles)]
assert len(report)==(5 if aiming else 4)
report['actions']=[a.name for a in bpy.data.actions]
names=('player','player_n','player_ne','player_se','player_s') if aiming else ('player_n','player_ne','player_se','player_s') if directional else ('player','grunt','rifle')
for name in names:
    if aiming:
        assert any(a.startswith(name+'/walk_aim_') for a in report['actions'])
        assert any(a.startswith(name+'/fire_aim_') for a in report['actions'])
    else:assert name+'/walk' in report['actions'] and name+'/fire' in report['actions']
(ROOT/'art/blender'/('aim_validation.json' if aiming else 'direction_validation.json' if directional else 'rig_validation.json')).write_text(json.dumps(report,indent=2)+'\n')
print('VALIDATED: connected sprite meshes, normalized blended skin weights, saved animation actions')
