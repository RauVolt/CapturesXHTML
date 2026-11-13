"""Generate the project's geometric capture icon from native drawing primitives."""
from pathlib import Path
from PIL import Image, ImageDraw

assets = Path(__file__).resolve().parents[1] / 'assets'
assets.mkdir(exist_ok=True)
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
<rect x="8" y="8" width="240" height="240" rx="56" fill="#2563eb"/>
<path d="M96 60H68a8 8 0 0 0-8 8v28m100-36h28a8 8 0 0 1 8 8v28M60 160v28a8 8 0 0 0 8 8h28m64 0h28a8 8 0 0 0 8-8v-28"
fill="none" stroke="white" stroke-width="14" stroke-linecap="round"/>
<rect x="96" y="96" width="64" height="64" rx="18" fill="#a5f3fc"/>
</svg>'''
(assets / 'capture.svg').write_text(svg, encoding='utf-8')
scale = 4
im = Image.new('RGBA', (256 * scale, 256 * scale))
d = ImageDraw.Draw(im)
def rect(box, radius, fill):
    d.rounded_rectangle(tuple(x * scale for x in box), radius=radius * scale, fill=fill)
rect((8, 8, 248, 248), 56, '#2563eb')
for points in (((96,60),(60,60),(60,96)), ((160,60),(196,60),(196,96)),
               ((60,160),(60,196),(96,196)), ((160,196),(196,196),(196,160))):
    d.line([(x*scale,y*scale) for x,y in points], fill='white', width=14*scale, joint='curve')
    for x,y in (points[0],points[-1]):
        d.ellipse(((x-7)*scale,(y-7)*scale,(x+7)*scale,(y+7)*scale),fill='white')
rect((96,96,160,160),18,'#a5f3fc')
im = im.resize((256,256), Image.Resampling.LANCZOS)
im.save(assets / 'capture.png')
im.save(assets / 'capture.ico', sizes=[(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(128,128),(256,256)])
