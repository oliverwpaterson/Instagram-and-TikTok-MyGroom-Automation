import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R="/home/claude/instagram-and-tiktok-mygroom-automation"; OUT=R+"/posts/2026-11-13_outage"
F=lambda n,s: ImageFont.truetype(f"{R}/tools/fonts/{n}.ttf", s)
SERIF=lambda s:F("newsreader-latin-400-normal",s); SANS=lambda s:F("karla-latin-500-normal",s); SANSB=lambda s:F("karla-latin-700-normal",s)
FOREST=(18,58,49); CREAM=(250,247,240); CORAL=(242,154,115); INK=(30,36,34); GREY=(110,118,114); SAGE=(157,195,171)
ICON=Image.open(f"{R}/tools/brand/icon.jpg").convert("RGB")
PHOTO=f"{R}/photos/library/horse-portrait/28719819-5eb9-4c6e-be43-9598c2f7c445.jpg"
def wrap(d,t,f,w):
    out,cur=[],""
    for x in t.split():
        s=(cur+" "+x).strip()
        if d.textlength(s,font=f)<=w: cur=s
        else: out.append(cur); cur=x
    out.append(cur); return out
def cover(W,H,fx,fy):
    im=Image.open(PHOTO).convert("RGB"); k=max(W/im.width,H/im.height)
    im=im.resize((int(im.width*k)+1,int(im.height*k)+1),Image.LANCZOS)
    x=int((im.width-W)*fx); y=int((im.height-H)*fy); return im.crop((x,y,x+W,y+H))
def card(d,x0,y0,w,scale=1.0):
    s=lambda v:int(v*scale); pad=s(48)
    # measure body
    body="Thanks for your email. Outlook's down, Teams is down, and I've taken that as a sign. I'm at the yard with my pony. I'll reply when Microsoft does."
    bl=wrap(d,body,SANS(s(36)),w-2*pad)
    h=pad+s(30)+s(26)+s(64)*2+s(24)+len(bl)*s(50)+s(36)+s(30)+pad
    d.rounded_rectangle([x0+6,y0+10,x0+w+6,y0+h+10],radius=s(34),fill=(0,0,0,70))
    d.rounded_rectangle([x0,y0,x0+w,y0+h],radius=s(34),fill=CREAM)
    y=y0+pad
    d.ellipse([x0+pad,y+s(6),x0+pad+s(18),y+s(24)],fill=CORAL)
    d.text((x0+pad+s(30),y),"AUTOMATIC REPLY",font=SANSB(s(28)),fill=GREY); y+=s(30)+s(26)
    for l in wrap(d,"Out of office: gone to see my pony",SERIF(s(60)),w-2*pad)[:2]:
        d.text((x0+pad,y),l,font=SERIF(s(60)),fill=INK); y+=s(64)
    y+=s(24)
    for l in bl: d.text((x0+pad,y),l,font=SANS(s(36)),fill=(60,66,64)); y+=s(50)
    y+=s(36); d.line([(x0+pad,y-s(14)),(x0+w-pad,y-s(14))],fill=(225,220,210),width=2)
    d.text((x0+pad,y),"Sent from the yard. Probably muddy.",font=SANS(s(28)),fill=GREY)
    return y0+h
def brand(im,d,x,y,sz=64):
    m=Image.new("L",(sz,sz),0); ImageDraw.Draw(m).rounded_rectangle([0,0,sz-1,sz-1],radius=sz//4,fill=255)
    im.paste(ICON.resize((sz,sz),Image.LANCZOS),(x,y),m); d.text((x+sz+16,y+sz//2-24),"MyGroom",font=SERIF(40),fill=CREAM)
def fade(im,start,end,alpha=235,topz=260):
    W,H=im.size; g=Image.new("L",(1,H))
    for y in range(H):
        t=0 if y<start else min(1,(y-start)/(end-start)); v=alpha*t
        if y<topz: v=max(v,150*(1-y/topz))
        g.putpixel((0,y),int(v))
    top=Image.new("L",(1,H))
    return Image.composite(Image.new("RGB",(W,H),FOREST),im,g.resize((W,H)))
# feed post 1080x1350
W,H=1080,1350
im=fade(cover(W,H,0.12,0.3),560,880); d=ImageDraw.Draw(im,"RGBA")
brand(im,d,64,60)
card(d,64,640,W-128)
d.text((64,H-84),"Care. Track. Remember.  ·  free on iPhone & web",font=SANS(30),fill=SAGE)
im.save(OUT+"/post.png",optimize=True)
# story 1080x1920
W,H=1080,1920
im=fade(cover(W,H,0.12,0.3),640,1000,topz=420); d=ImageDraw.Draw(im,"RGBA")
brand(im,d,84,250,72)
end=card(d,84,820,W-168,1.05)
bf=SANSB(38); lab="Free app: link in bio"; bw=d.textlength(lab,font=bf)+80
d.rounded_rectangle([84,end+80,84+bw,end+170],radius=45,fill=CORAL); d.text((124,end+101),lab,font=bf,fill=FOREST)
im.save(OUT+"/story.png",optimize=True)
print("ok")
