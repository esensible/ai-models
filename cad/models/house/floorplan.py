"""Measured draft floor plan. Run from repo root using cad/run.sh.

Units mm; front is y=0, rear is +y. CAD geometry is a 100 mm plan
slice, not an assertion about ceiling height. See README.md for assumptions.
"""
import json
from pathlib import Path
import build123d as b
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc, PathPatch
from matplotlib.path import Path as PlotPath
import trimesh

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'cad/out/house'
OUT.mkdir(parents=True, exist_ok=True)
data = json.loads(Path(__file__).with_name('measurements.json').read_text())
m = {v['id']: v['value'] for v in data['measurements']}
def val(key): return m[key]
T = 200  # unmeasured walls: provisional
D = data['assumptions']['default_doorway_width']['value']
H0 = 4200
H1 = H0 + val('entry_hall_width_at_front_door')
STEP = val('entry_hall_front_door_to_right_step')
HN = H1 - val('entry_hall_narrow_section_width')
HW = HN + val('entry_hall_next_wider_section_width')
END = STEP + val('entry_hall_second_section_length')
# Anchor the kitchen at the laundry wall, rather than guessing the exterior width.
RIGHT = (val('ensuite_side_to_side_span') + val('laundry_side_to_side_span') + 2*T
         + val('kitchen_zone_and_passage_cross_house_span') + T
         + val('toilet_side_to_side_span'))
KLEFT = RIGHT - val('toilet_side_to_side_span') - T - val('kitchen_zone_and_passage_cross_house_span')
KR = KLEFT + val('kitchen_zone_and_passage_cross_house_span')
KBACK = END + T + val('kitchen_recess_width')
BLEFT = RIGHT - val('right_bathroom_side_to_side_span')
BTOP = KBACK + T + val('right_bathroom_front_to_back_span')
REAR = BTOP + T + 3000
LIVING_LEFT = 2147
EW = val('ensuite_side_to_side_span')
LW = val('laundry_side_to_side_span')
EY = END + T + val('ensuite_front_to_back_span')
LY = END + T + val('laundry_front_to_back_width')
rooms = []
openings = []
doors = []
windows = []
def room(name, x, y, w, h, measured=False, label=None):
    rooms.append((name,x,y,w,h,measured,label))
def gap(x,y,w,h): openings.append((x,y,w,h))
def door(x,y,axis='v',width=D):
    # Hinges and swing directions are provisional, shown to identify openings.
    if axis == 'v': gap(x-5,y,T+10,width)
    else: gap(x,y-5,width,T+10)
    doors.append((x,y,axis,width))
def window(x,y,length,axis='h'):
    if axis=='h': gap(x,y-5,length,T+10)
    else: gap(x-5,y,T+10,length)
    windows.append((x,y,length,axis))

# Front rooms and measured hall, followed by the short assumed neck.
room('Front-left bedroom',0,0,H0-T,STEP-T,label='Reference room; outline provisional')
room('Bedroom / lounge',H1+T,0,RIGHT-H1-T,STEP-T,label='Reference room; outline provisional')
room('Entry',H0,0,H1-H0,STEP,True,label='Width 1,720')
room('Middle-left bedroom',0,STEP+T,HN-T,END-STEP-T,label='Reference room; outline provisional')
room('Middle-right bedroom',HW+T,STEP+T,RIGHT-HW-T,END-STEP-T,label='Reference room; outline provisional')
room('Hall',HN,STEP+T,HW-HN,END-STEP-T,True,label='Width 1,450')
room('Ensuite',0,END+T,EW,val('ensuite_front_to_back_span'),True)
room('Laundry',EW+T,END+T,LW,val('laundry_front_to_back_width'),True)
room('Kitchen + passage',KLEFT,END+T,KR-KLEFT,KBACK-END-T,True,label='Across zone 4,815 | recess 1,830*')
room('Toilet',RIGHT-val('toilet_side_to_side_span'),END+T,val('toilet_side_to_side_span'),val('toilet_front_to_back_span'),True)
room('Bathroom',BLEFT,KBACK+T,val('right_bathroom_side_to_side_span'),val('right_bathroom_front_to_back_span'),True)
room('Rear bedroom',BLEFT,BTOP+T,RIGHT-BLEFT,3000,label='Reference depth ~3,000')
room('Living / dining',LIVING_LEFT,KBACK+T,BLEFT-LIVING_LEFT-T,REAR-KBACK-T,label='Reference room; outline provisional')
TY = END+T+val('toilet_front_to_back_span')
# Openings and reference window locations.
door(H0+450,-T,'h')
door(H0-T,1500); door(H1,2350)
door(HN-T,6100); door(HW,6100)
door(600,END,'h'); door(EW,END+T+450,width=660)
door(EW+T+450,LY,'h',val('laundry_doorway_width'))
door(BLEFT-T,KBACK+T+220); door(BLEFT-T,BTOP+T+220)
for x in (900,H1+1900): window(x,-T,1500)
for y in (1200,5600): window(-T,y,1400,'v'); window(RIGHT,y,1400,'v')
window(RIGHT,KBACK+T+650,900,'v'); window(RIGHT,BTOP+T+1000,900,'v')
window(LIVING_LEFT+700,REAR,1600); window(BLEFT+550,REAR,1000)
door(LIVING_LEFT+2700,REAR,'h')
# Build a single closed envelope and subtract room/circulation interiors.
# Shared partitions are the material remaining between adjacent spaces, so
# every T-junction is filled before intentional door/window openings are cut.
def rect(x,y,w,h): return b.Pos(x+w/2,y+h/2)*b.Rectangle(w,h)
envelope = b.Polygon((-T,-T),(RIGHT+T,-T),(RIGHT+T,REAR+T),
                     (LIVING_LEFT-T,REAR+T),(LIVING_LEFT-T,LY+T),
                     (-T,LY+T),align=None)
footprint = envelope
for name,x,y,w,h,measured,label in rooms:
    footprint = footprint - rect(x,y,w,h)
# Continuous hall, kitchen/living opening and toilet/bathroom connection.
connectors = [
    (HN,STEP,H1-HN,T),
    (HN,END,HW-HN,T),
    (KLEFT, KBACK, BLEFT-T-KLEFT, T),
    (KR+T, TY, RIGHT-KR-T, KBACK+T-TY),
]
for r in connectors: footprint = footprint - rect(*r)
# The measured thickness is local; segment extent and position remain provisional.
footprint = footprint + rect(EW+T+LW,LY,650,val('kitchen_to_living_wall_thickness'))
# Laundry door must cut through the complete shared wall, even where room
# depth differs by a few mm; never leave a thin sliver across an opening.
openings.append((EW+T+450,LY-5,val('laundry_doorway_width'),KBACK+T-LY+10))
for r in openings: footprint = footprint - rect(*r)
footprint = footprint.clean()
part = b.extrude(footprint,amount=100)
print('Volume mm3:',part.volume)
print('Bounding box:',part.bounding_box())
assert part.is_valid, 'Invalid CAD topology'
b.export_step(part,str(OUT/'house_plan_slice.step'))
b.export_stl(part,str(OUT/'house_plan_slice.stl'))
mesh=trimesh.load(OUT/'house_plan_slice.stl')
print('Watertight:',mesh.is_watertight)
assert mesh.is_watertight, 'Invalid plan mesh'

# Measure clear spans from intersections with the final CAD walls, independently
# of text labels. A 0.02 mm probe is used away from doors/windows.
def clear_span(cx,cy,axis):
    probe = rect(-1000,cy-.01,RIGHT+2000,.02) if axis=='x' else rect(cx-.01,-1000,.02,REAR+2000)
    hits = footprint & probe
    ranges=[]
    for f in hits.faces():
        bb=f.bounding_box()
        ranges.append((bb.min.X,bb.max.X) if axis=='x' else (bb.min.Y,bb.max.Y))
    c=cx if axis=='x' else cy
    left=max(hi for lo,hi in ranges if hi<c)
    right=min(lo for lo,hi in ranges if lo>c)
    return right-left
checks=[]
def check(key,cx,cy,axis):
    actual=clear_span(cx,cy,axis); expected=val(key)
    checks.append({'measurement':key,'expected_mm':expected,'cad_clear_mm':round(actual,3)})
    assert abs(actual-expected)<.05, (key,actual,expected)
check('entry_hall_width_at_front_door',(H0+H1)/2,600,'x')
check('entry_hall_narrow_section_width',(HN+H1)/2,STEP+100,'x')
check('entry_hall_next_wider_section_width',(HN+HW)/2,5500,'x')
check('laundry_side_to_side_span',EW+T+LW/2,END+T+1600,'x')
check('laundry_front_to_back_width',EW+T+LW-200,END+T+900,'y')
check('ensuite_side_to_side_span',EW/2,END+T+1600,'x')
check('ensuite_front_to_back_span',1500,END+T+900,'y')
check('right_bathroom_side_to_side_span',BLEFT+1200,KBACK+T+1800,'x')
check('right_bathroom_front_to_back_span',BLEFT+600,KBACK+T+1200,'y')
check('toilet_side_to_side_span',RIGHT-500,END+T+500,'x')
check('kitchen_zone_and_passage_cross_house_span',(KLEFT+KR)/2,END+T+1000,'x')
(OUT/'geometry_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print('Verified',len(checks),'clear dimensions from CAD wall intersections')

# Draw the actual CAD footprint, with annotations on a separate layer.
fig = plt.figure(figsize=(8,11),facecolor='#faf9f6')
# Fixed 1:100 at the SVG's native 8 x 11 inch page size.
XMIN,XMAX=-650,RIGHT+3400
YMIN,YMAX=-2500,REAR+650
ax=fig.add_axes([.06,.18,(XMAX-XMIN)/100/(8*25.4),(YMAX-YMIN)/100/(11*25.4)])
ax.set_aspect('equal'); ax.axis('off')
ink='#24343e'; teal='#187a77'; muted='#78818a'
for name,x,y,w,h,measured,label in rooms:
    ax.add_patch(Rectangle((x,y),w,h,facecolor='#edf5f2' if measured else '#f0ede7',edgecolor='none'))
    if name=='Toilet':
        txt='Toilet\n1,039 ×\n1,800'; size=7
    elif name in ('Entry','Hall'): txt=f'{name}\n{label.replace("Width ", "")}'; size=7
    elif measured and not label: txt=f'{name}\n{w:,} × {h:,}'; size=8
    else: txt=f'{name}\n{label.replace("Width ", "")}'; size=7.5
    ax.text(x+w/2+(100 if name in ('Entry','Hall') else 0),y+h/2+(700 if name in ('Entry','Hall') else 0),txt,ha='center',va='center',fontsize=size,color=ink,linespacing=1.6)
for face in footprint.faces():
    verts=[]; codes=[]
    for i,wire in enumerate([face.outer_wire(),*face.inner_wires()]):
        edges=list(wire.edges())
        segments=[[(e.start_point().X,e.start_point().Y),(e.end_point().X,e.end_point().Y)] for e in edges]
        pts=segments.pop(0)
        while segments:
            end=pts[-1]
            found=False
            for j,(p0,p1) in enumerate(segments):
                if abs(p0[0]-end[0])+abs(p0[1]-end[1])<.001:
                    pts.append(p1); segments.pop(j); found=True; break
                if abs(p1[0]-end[0])+abs(p1[1]-end[1])<.001:
                    pts.append(p0); segments.pop(j); found=True; break
            assert found, 'Disconnected drawing wire'
        pts=pts[:-1]
        area=sum(pts[j][0]*pts[(j+1)%len(pts)][1]-pts[(j+1)%len(pts)][0]*pts[j][1] for j in range(len(pts)))
        if (area>0)!=(i==0): pts.reverse()
        verts.extend(pts+[pts[0]]); codes.extend([PlotPath.MOVETO]+[PlotPath.LINETO]*(len(pts)-1)+[PlotPath.CLOSEPOLY])
    ax.add_patch(PathPatch(PlotPath(verts,codes),facecolor=ink,edgecolor=ink,lw=.4))
for x,y,axis,w in doors:
    if axis=='v':
        ax.plot([x,x+w],[y,y],color=muted,lw=.7)
        ax.add_patch(Arc((x,y),2*w,2*w,theta1=0,theta2=90,color=muted,lw=.6))
    else:
        ax.plot([x,x],[y,y+w],color=muted,lw=.7)
        ax.add_patch(Arc((x,y),2*w,2*w,theta1=0,theta2=90,color=muted,lw=.6))
for x,y,l,a in windows:
    for off in (65,135):
        if a=='h': ax.plot([x,x+l],[y+off,y+off],color=teal,lw=.8)
        else: ax.plot([x+off,x+off],[y,y+l],color=teal,lw=.8)
def dim(x1,y1,x2,y2,text):
    ax.annotate('',(x1,y1),(x2,y2),arrowprops=dict(arrowstyle='|-|',color=teal,lw=.8))
    vertical=x1==x2
    ax.text((x1+x2)/2+(130 if vertical else 0),(y1+y2)/2+(0 if vertical else 110),text,rotation=90 if vertical else 0,ha='left' if vertical else 'center',va='center' if vertical else 'bottom',fontsize=8,color=teal,bbox=dict(facecolor='#faf9f6',edgecolor='none',pad=1))
dim(H0+180,0,H0+180,STEP,'4,260')
dim(HN+180,STEP,HN+180,END,'3,960*')
ax.annotate('815 neck*',xy=((HN+H1)/2,STEP+100),xytext=(H1+1200,STEP+650),fontsize=8,color=teal,arrowprops=dict(arrowstyle='-',color=teal,lw=.7))
ax.annotate('350 wall*',xy=(EW+T+LW+325,LY+175),xytext=(KLEFT+1500,LY+850),fontsize=8,color=teal,arrowprops=dict(arrowstyle='-',color=teal,lw=.7))
# Ancillary spaces shown as reference outlines only; detached shed as a labelled inset.
ax.add_patch(Rectangle((-T,-2200),RIGHT+2*T,2000,fill=False,edgecolor=muted,ls='--',lw=.8))
ax.text(RIGHT/2,-1450,'Front verandah · reference only',ha='center',fontsize=9,color=muted)
ax.add_patch(Rectangle((RIGHT+T,0),2800,5800,fill=False,edgecolor=muted,ls='--',lw=.8))
ax.text(RIGHT+1600,2900,'Carport\n~2,800 × 5,800',ha='center',fontsize=9,color=muted)
ax.annotate('FRONT',xy=((H0+H1)/2,-200),xytext=((H0+H1)/2,-750),ha='center',fontsize=8,color=ink,arrowprops=dict(arrowstyle='->',color=ink))
ax.set_xlim(-650,RIGHT+3400); ax.set_ylim(-2500,REAR+650)
fig.text(.075,.957,'house',fontsize=30,color=ink,weight='bold')
fig.text(.075,.931,'FLOOR PLAN  /  MEASURED DRAFT 02',fontsize=11,color=teal)
fig.text(.79,.87,'DRAWING KEY',fontsize=10,color=ink,weight='bold')
fig.text(.79,.84,'Scale 1:100 at native size\nScale bar remains valid on screen\n\nGreen rooms\nMeasured dimensions\n\nWarm grey rooms\nReference / inferred\n\nAll dimensions in mm\nFront at bottom\nNo north bearing assumed',fontsize=9,color=ink,linespacing=1.6,va='top')
fig.text(.79,.51,'REFERENCE ONLY',fontsize=10,color=ink,weight='bold')
fig.text(.79,.48,'Detached rear shed\n~5,800 × 3,800\nPosition not measured',fontsize=9,color=muted,linespacing=1.6,va='top')
# Geometric scale bar, in the same coordinate system as the CAD walls.
for i in range(4):
    ax.add_patch(Rectangle((i*1000,-2100),1000,100,facecolor=ink if i%2==0 else 'white',edgecolor=ink,lw=.6))
for i in range(5): ax.text(i*1000,-2300,str(i),ha='center',fontsize=7,color=ink)
ax.text(4400,-2300,'metres',fontsize=7,color=ink)
fig.text(.075,.115,'* Layout interpretations to confirm',fontsize=11,color=ink,weight='bold')
fig.text(.075,.092,'Hall: 3,960 includes an assumed 200-long neck. Kitchen recess: 1,830 interpreted front-to-back.\n350-thick wall segment is provisional. Other walls assumed 200 thick; openings positioned from reference.\nDoor widths assumed 820, laundry 660. Bedrooms, living room, windows and outside footprint remain provisional.',fontsize=9,color=ink,linespacing=1.5,va='top')
fig.text(.075,.025,'Measurement reference for ongoing modelling · not a surveyed or construction drawing',fontsize=9,color=muted)
# Keep text proportions appropriate to the smaller physical sheet.
from matplotlib.text import Text
for artist in fig.findobj(Text): artist.set_fontsize(artist.get_fontsize()*.72)
fig.canvas.draw()
origin=ax.transData.transform((0,0))
xunit=ax.transData.transform((1000,0))
yunit=ax.transData.transform((0,1000))
x_paper_mm=(xunit[0]-origin[0])/fig.dpi*25.4
y_paper_mm=(yunit[1]-origin[1])/fig.dpi*25.4
assert abs(x_paper_mm-10)<1e-6 and abs(y_paper_mm-10)<1e-6
print('Scale verified: 1,000 mm maps to 10 mm on paper, in both axes')
fig.savefig(OUT/'house_floorplan.svg',facecolor=fig.get_facecolor())
fig.savefig(OUT/'house_floorplan.png',dpi=180,facecolor=fig.get_facecolor())
print('Saved drawings to',OUT)
