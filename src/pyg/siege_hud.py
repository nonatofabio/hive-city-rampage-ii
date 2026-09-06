"""Compact, background-free vitals and a translucent tactical auspex."""
import math
import pygame as pg
from siege_effects import weapon_texture

# Original Latin-styled devotional snippets; not quotations from a game script.
SAYINGS=('LUX IN TENEBRIS','FERRUM ET FIDES','VIGILA. RESISTE.','OFFICIUM ANTE OMNIA','EX TENEBRIS, SPES')


def servo_saying(time):
    phase=time%6.5
    opacity=max(0,min(1,phase/.18,(3.1-phase)/.5))
    opacity*=.84+.16*math.sin(time*9)
    return SAYINGS[int(time//6.5)%len(SAYINGS)],round(opacity*255)


def outlined(surface,font,text,pos,color,alpha=255):
    label=font.render(text,True,color);shadow=font.render(text,True,(10,12,16))
    if alpha<255:label.set_alpha(alpha);shadow.set_alpha(alpha)
    surface.blit(shadow,(pos[0]+1,pos[1]+1));surface.blit(label,pos)


def auspex(game,font):
    panel=pg.Surface((132,88),pg.SRCALPHA)
    panel.fill((15,23,30,78))
    pg.draw.rect(panel,(158,139,100,100),panel.get_rect(),1)
    panel.blit(font.render('AUSPEX',True,(194,164,107)),(8,5))
    def point(pos):return round(8+pos.x/2400*115),round(25+pos.y/700*52)
    for cover in game.cover:
        if cover.hp>0:pg.draw.circle(panel,(117,112,91,165),point(cover.pos),1)
    for relay in game.relays:
        pg.draw.circle(panel,(235,151,56,235) if relay.hp>0 else (84,126,111,165),point(relay.pos),2)
    for enemy in game.enemies:
        if enemy.hp>0:pg.draw.circle(panel,(229,74,47,240),point(enemy.pos),3 if enemy.kind=='boss' else 2)
    pg.draw.circle(panel,(120,224,249,255),point(game.player.pos),3)
    if game.boss_defeated:pg.draw.circle(panel,(100,232,175,230),point(pg.Vector2(2280,510)),3,1)
    return panel


def status_hud(surface,game,font,small):
    skull=weapon_texture('servo_skull')
    surface.blit(skull,(14,12+round(math.sin(game.time*2.5))))
    outlined(surface,small,f'{game.score:08d}',(64,15),(225,208,164))
    for y,value,maximum,color,label in ((37,game.player.hp,100,(206,63,45),'HP'),(52,game.shield,60,(66,166,204),'SH')):
        outlined(surface,small,label,(64,y-3),(211,210,198))
        # Only thin bar tracks have a dark backing; there is no enclosing panel.
        pg.draw.rect(surface,(30,31,34),(84,y,112,5))
        pg.draw.rect(surface,color,(84,y,round(112*max(0,min(1,value/maximum))),5))
        outlined(surface,small,str(max(0,int(value))),(203,y-3),(226,220,204))
    saying,alpha=servo_saying(game.time)
    if alpha:outlined(surface,small,saying,(64,69),(208,176,112),alpha)
    surface.blit(auspex(game,small),(surface.get_width()-144,12))
