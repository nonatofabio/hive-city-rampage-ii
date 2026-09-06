"""Complete original-art poses rendered from Blender's weighted sprite rigs.

No runtime limb extraction, rotations, or mesh deformation. Blender does the
skeletal animation offline. Player walking combines an aiming torso with
authored lower-body poses selected independently from movement direction.
"""
from functools import lru_cache
import json
import math
from pathlib import Path
import pygame as pg

V=pg.Vector2
DIRECTORY=Path(__file__).with_name('assets')/'rendered'
SIZES={'player':(88,100),'grunt':(82,90),'rifle':(82,94),'runner':(70,78),'brute':(98,112),'boss':(200,238)}
MODELS={'player':'player','grunt':'grunt','rifle':'rifle','runner':'grunt','brute':'rifle','boss':'boss'}


@lru_cache(maxsize=1)
def manifest():
    models=json.loads((DIRECTORY/'sprites.json').read_text())['models']
    # Moving player combat sockets come from the exact torso layers being drawn.
    for name,data in upper_manifest().items():models[name]['clips'].update(data['clips'])
    return models


def pose_key(kind,stride,moving,angle,recoil,time=0.,windup=0.,view=None):
    model=MODELS[kind]
    if kind=='player':
        view=direction_angle(angle) if view is None else view
        model={-90:'player_n',-45:'player_ne',0:'player',45:'player_se',90:'player_s'}[view]
    data=manifest()[model]
    if kind=='boss' and windup>0:
        clip='attack'
        index=min(data['clips'][clip]['count']-1,int((1-windup/1.25)*data['clips'][clip]['count']))
    else:
        clip=('walk_fire' if recoil>.05 else 'walk') if moving else 'fire' if recoil>0 else 'idle'
        if kind=='boss' and clip=='fire':clip='idle'
        if kind=='player' and data.get('aim_angles'):
            sample=min(data['aim_angles'],key=lambda a:abs(a-angle))
            clip+='_aim_'+str(sample)
        if kind not in ('boss','player'):clip += '_up' if angle < -20 else '_down' if angle > 20 else ''
        count=data['clips'][clip]['count']
        if moving:index=int(stride*count)%count
        elif recoil>0 and kind!='boss':index=min(count-1,max(0,int((1-recoil/.105)*count)))
        else:index=int(time*2)%count
    return model,clip,max(0,index)


def coordinates(kind,key,facing):
    model,clip,index=key;data=manifest()[model]
    sx=sy=1.
    if kind!='player':
        sx=SIZES[kind][0]/SIZES[model][0];sy=SIZES[kind][1]/SIZES[model][1]
    if model in ('player_n','player_s'):facing=1
    size=(round(data['cell'][0]*sx),round(data['cell'][1]*sy))
    # Use the exact integer resize factors used to draw the full image.
    scale=V(size[0]/data['cell'][0],size[1]/data['cell'][1])
    anchor=V(data['anchor']);muzzle=V(data['clips'][clip]['muzzles'][index])
    anchor=V(anchor.x*scale.x,anchor.y*scale.y)
    if kind=='player':anchor.y+=GROUND_SHIFT[model]
    muzzle=V(muzzle.x*scale.x,muzzle.y*scale.y)
    if facing<0:anchor.x=size[0]-anchor.x;muzzle.x=size[0]-muzzle.x
    return size,anchor,muzzle


@lru_cache(maxsize=96)
def sheet(model,clip):
    filename=manifest()[model]['clips'][clip]['sheet']
    return pg.image.load(str(DIRECTORY/filename)).convert_alpha()


@lru_cache(maxsize=2048)
def frame(kind,key,facing):
    model,clip,index=key;data=manifest()[model];w,h=data['cell']
    image=sheet(model,clip).subsurface((index*w,0,w,h))
    size,anchor,muzzle=coordinates(kind,key,facing)
    if image.get_size()!=size:image=pg.transform.scale(image,size)
    if facing<0 and model not in ('player_n','player_s'):image=pg.transform.flip(image,True,False)
    return image,anchor,muzzle


@lru_cache(maxsize=96)
def upper_sheet(model,clip):
    filename=manifest()[model]['clips'][clip]['sheet']
    return pg.image.load(str(DIRECTORY/'upper'/filename)).convert_alpha()


@lru_cache(maxsize=5)
def walk_sheet(view):
    return pg.image.load(str(DIRECTORY/'walk'/f'{view}.png')).convert_alpha()


def signed_direction(view,facing):
    return view if facing>=0 else (180-view+180)%360-180


def gait_pose(body_view,facing,move_view,move_facing,phase):
    """Constrain pelvis yaw and select forward/backward timing from one phase."""
    body=signed_direction(body_view,facing)
    travel=signed_direction(move_view,move_facing)
    delta=(travel-body+180)%360-180
    backward=abs(delta)>90
    if backward:delta=(delta+360)%360-180
    # For retreat, orient feet toward the body and play the gait in reverse.
    pelvis=body+max(-45,min(45,delta))
    radians=math.radians(pelvis)
    leg_facing=1 if math.cos(radians)>=-1e-6 else -1
    leg_view=direction_angle(math.degrees(math.atan2(math.sin(radians),abs(math.cos(radians)))))
    step=int(phase*4)%4
    return leg_view,leg_facing,(-step)%4 if backward else step


@lru_cache(maxsize=1)
def upper_manifest():
    return json.loads((DIRECTORY/'upper/sprites.json').read_text())['models']


def waist_socket(key,facing):
    model,clip,index=key
    waist=V(upper_manifest()[model]['clips'][clip]['waists'][index])
    if facing<0 and model not in ('player_n','player_s'):
        waist.x=manifest()[model]['cell'][0]-waist.x
    return waist


BELT_OVERLAP={'player':8,'player_ne':6,'player_n':4,'player_se':8,'player_s':7}
# Ground the new contact poses after seating the belt inside the torso.
GROUND_SHIFT={'player':-4,'player_ne':-5,'player_n':1,'player_se':-3,'player_s':1}


@lru_cache(maxsize=40)
def lower_body(leg_view,leg_facing,step):
    # Symmetric front/rear armor uses reflected opposite-foot poses, avoiding
    # generator inconsistencies that repeat the same supporting leg.
    vertical=abs(leg_view)==90
    lower=walk_sheet(leg_view).subsurface(((step%2 if vertical else step)*80,0,80,64))
    if (vertical and step>=2) or (not vertical and leg_facing<0):lower=pg.transform.flip(lower,True,False)
    return lower


def lower_origin(key,facing):
    waist=waist_socket(key,facing)
    return round(waist.x)-40,round(waist.y)-12-BELT_OVERLAP[key[0]]


@lru_cache(maxsize=1024)
def walking_frame(key,facing,leg_view,leg_facing,step):
    model,clip,index=key;data=manifest()[model];w,h=data['cell']
    size,anchor,muzzle=coordinates('player',key,facing)
    upper=upper_sheet(model,clip).subsurface((index*w,0,w,h))
    if facing<0 and model not in ('player_n','player_s'):upper=pg.transform.flip(upper,True,False)
    lower=lower_body(leg_view,leg_facing,step)
    image=pg.Surface(size,pg.SRCALPHA)
    # Register the belt to the animated pelvis, using the same frame as the torso.
    image.blit(lower,lower_origin(key,facing))
    image.blit(upper,(0,0))
    return image,anchor,muzzle


def animated_sprite(kind,stride,moving,facing,angle,recoil,time=0.,windup=0.,view=None,move_angle=None,move_facing=None):
    key=pose_key(kind,stride,moving,angle,recoil,time,windup,view)
    if kind=='player':
        body_view={'player':0,'player_ne':-45,'player_n':-90,'player_se':45,'player_s':90}[key[0]]
        if moving:
            leg_view,leg_facing,step=gait_pose(body_view,facing,body_view if move_angle is None else move_angle,facing if move_facing is None else move_facing,key[2]/manifest()[key[0]]['clips'][key[1]]['count'])
        else:
            # Settle onto the nearest contact pose without changing art sets.
            leg_view,leg_facing,step=body_view,facing,(round(stride*2)*2)%4
        return walking_frame(key,facing,leg_view,leg_facing,step)
    return frame(kind,key,facing)


def muzzle_offset(kind,stride,moving,facing,angle,recoil,time=0.,view=None):
    # JSON geometry only; headless simulation does not need a video device.
    _,anchor,muzzle=coordinates(kind,pose_key(kind,stride,moving,angle,recoil,time,view=view),facing)
    return muzzle-anchor


def ejection_offset(kind,stride,moving,facing,angle,recoil,time=0.,view=None):
    key=pose_key(kind,stride,moving,angle,recoil,time,view=view)
    model,clip,index=key;data=manifest()[model]
    port=V(data['clips'][clip]['ejections'][index])
    size,anchor,_=coordinates(kind,key,facing)
    port=V(port.x*size[0]/data['cell'][0],port.y*size[1]/data['cell'][1])
    if facing<0 and model not in ('player_n','player_s'):port.x=size[0]-port.x
    return port-anchor


def barrel_axis(kind,key,facing):
    model,clip,index=key
    data=manifest()[model]
    barrel=V(data['clips'][clip]['barrels'][index])
    tip=V(data['clips'][clip]['muzzles'][index])
    axis=tip-barrel
    if facing<0 and model not in ('player_n','player_s'):axis.x=-axis.x
    return axis.normalize() if axis.length_squared() else V(facing,0)


def solve_weapon_aim(stride,moving,facing,preferred,recoil,time,target):
    """Choose the rendered barrel closest to the true muzzle-to-target line.

    Search pose geometry directly: iterative angle rounding can oscillate when
    the cursor is close and the muzzle itself moves as the weapon turns.
    """
    models={-90:'player_n',-45:'player_ne',0:'player',45:'player_se',90:'player_s'}
    def best(view):
        candidates=[]
        for angle in manifest()[models[view]]['aim_angles']:
            key=pose_key('player',stride,moving,angle,recoil,time,view=view)
            _,anchor,muzzle=coordinates('player',key,facing)
            delta=target-(muzzle-anchor)
            if delta.length_squared()<16:continue
            error=abs((barrel_axis('player',key,facing).angle_to(delta)+180)%360-180)
            candidates.append((error,view,angle))
        return min(candidates) if candidates else (180,view,view)
    result=best(preferred)
    if result[0]>3:
        # A nearby target can require an adjacent body view to keep the barrel on it.
        for view in models:
            if abs(view-preferred)==45:
                candidate=best(view)
                if candidate[0]+.25<result[0]:result=candidate
    return result[1],result[2]


def direction_angle(angle,previous=None):
    """Five source views; a 4-degree margin prevents boundary chatter in play."""
    views=(-90,-45,0,45,90)
    if previous in views and abs(angle-previous)<=26.5:
        return previous
    return min(views,key=lambda view:abs(angle-view))


def aim_pose(delta,previous_facing=1,previous_angle=None):
    projected=V(delta.x-delta.y,(delta.x+delta.y)*.5)
    facing=previous_facing if abs(projected.x)<3 else 1 if projected.x>=0 else -1
    if projected.length_squared()<9 and previous_angle is not None:
        return previous_facing,previous_angle
    angle=math.degrees(math.atan2(projected.y,abs(projected.x)))
    return facing,angle if previous_angle is None else direction_angle(angle,previous_angle)
