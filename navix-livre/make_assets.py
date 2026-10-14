"""Gera ícones locais do Navix Livre, sem imagens de terceiros.
Usado somente na compilação; o aplicativo instalado não depende do Pillow.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

OUT=Path(__file__).resolve().parent/"assets"
OUT.mkdir(exist_ok=True)

def curve(p0,p1,p2,steps=60):
    return [(
        int((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0]),
        int((1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1])
    ) for t in (i/steps for i in range(steps+1))]

def feather(draw,scale=1,origin=(0,0),color=(250,253,255,255)):
    ox,oy=origin
    def point(x,y):return(int(ox+x*scale),int(oy+y*scale))
    # Pena estilizada: duas folhas curvas e uma haste de escrita.
    upper=curve(point(49,158),point(64,25),point(212,37))
    edge=curve(point(212,37),point(188,135),point(49,158))
    draw.polygon(upper+edge,fill=color)
    mid=curve(point(50,158),point(131,79),point(207,41))
    draw.line(mid,fill=(65,172,245,255),width=max(2,int(4*scale)),joint="curve")
    for x,y in [(86,118),(107,99),(130,79),(153,62),(171,51)]:
        anchor=point(x,y)
        tip=point(x+55,(y+17 if y>90 else y+23))
        draw.line([anchor,tip],fill=(135,213,255,230),width=max(1,int(2*scale)))
    draw.line(curve(point(50,158),point(33,196),point(25,225)),
              fill=(249,253,255,255),width=max(2,int(5*scale)),joint="curve")

S=256
im=Image.new("RGBA",(S,S),(0,0,0,0))
d=ImageDraw.Draw(im)
for y in range(9,247):
    for x in range(9,247):
        if 8 <= x <= 247 and 8 <= y <= 247:
            # Fundo luminoso sem gradiente opaco nas bordas.
            pass
d.rounded_rectangle((8,8,247,247),radius=51,fill=(17,94,193,255))
for j in range(7):
    d.arc((13+j,13+j,242-j,242-j),start=195,end=355,
          fill=(32,128+j*8,225,105),width=3)
shadow=Image.new("RGBA",im.size,(0,0,0,0))
sd=ImageDraw.Draw(shadow)
feather(sd,origin=(6,7),color=(0,21,44,100))
shadow=shadow.filter(ImageFilter.GaussianBlur(6))
im=Image.alpha_composite(im,shadow)
feather(ImageDraw.Draw(im))
im.save(OUT/"navix.ico",format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])

def wizard(w,h,name):
    canvas=Image.new("RGB",(w,h))
    pixels=canvas.load()
    for y in range(h):
        for x in range(w):
            t=y/max(1,h-1)
            pixels[x,y]=(int(6+15*t),int(26+12*t),int(62+42*t))
    dr=ImageDraw.Draw(canvas)
    factor=min(w/256,h/320)
    px=(w-225*factor)/2
    feather(dr,scale=factor*1.05,origin=(px,h*0.16),color=(243,252,255))
    try:
        font=ImageFont.truetype("arialbd.ttf",max(14,int(w*0.11)))
    except OSError:
        font=ImageFont.load_default()
    dr.text((w//2,int(h*.81)),"NAVIX",font=font,fill=(235,246,255),anchor="mm")
    dr.text((w//2,int(h*.90)),"LIVRE",font=font,fill=(122,197,253),anchor="mm")
    canvas.save(OUT/name,format="BMP")

wizard(164,314,"wizard.bmp")
wizard(55,58,"wizard_small.bmp")
print("Assets gerados:",*[p.name for p in OUT.iterdir()])
