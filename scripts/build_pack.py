from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np, json, math
from build_dials import draw_dials
from pack_io import save_png
R=Path(__file__).resolve().parents[1]; P=R/'pack';P.mkdir(exist_ok=True)
S=4
# Original imagegen artwork; build script only sizes, masks and assembles pack assets.
assets={name: f'source/{name}_master.png' for name in ('title','carrier','cockpit')}
for k,v in assets.items():
 if k=='carrier':continue # clean animated launch plate is built once, below
 src=R/v
 im=Image.open(src).convert('RGBA').resize((1024,960),Image.Resampling.LANCZOS)
 if k=='cockpit':
  # Align the painted monitor/frame edges with fixed native instrument rows.
  out=Image.new('RGBA',(1024,960))
  # Start below the sky-colored margin baked into the cockpit master. The
  # first coaming segment still ends at the original instrument boundary.
  srcys=[131,142,177,214,240];dstys=[128,144,176,208,240]
  for a,b,c,d in zip(srcys,srcys[1:],dstys,dstys[1:]):out.paste(im.crop((0,a*4,1024,b*4)).resize((1024,(d-c)*4),Image.Resampling.LANCZOS),(0,c*4))
  im=out
  # Decorative dial scales are vector UI; flight values and attitude remain native.
  draw_dials(im)
 save_png(im,P/f'{k}.png')
fontpath=str(R/'source/fonts/DejaVuSansMono-Bold.ttf')
font=ImageFont.truetype(fontpath,25)
title_ui=Image.new('RGBA',(1024,960));d=ImageDraw.Draw(title_ui)
d.text((512,866),'PRESS START',font=ImageFont.truetype(fontpath,25),anchor='mm',fill=(218,232,241,255),stroke_width=1,stroke_fill=(9,23,41,255))
save_png(title_ui,P/'title_prompt.png')
# Dynamic instrument glyphs remain tied to original CHR data.
trans=Image.new('RGBA',(32,32));save_png(trans,P/'transparent.png')
lines=['# Top Gun HD v0.5.1 - banked horizon and cloud deck','<ver>109','<scale>4','<overscan>0,0,0,0','<img>transparent.png','<img>instruments.png']
def capture(n,s):return (R/f'captures/baseline/{n:05d}.{s}').read_bytes()
def pat(n,i):return capture(n,'chr')[i*16:(i+1)*16].hex().upper()
def tile_cond(name,n,x,y,i):lines.append(f'<condition>{name},tileAtPosition,{x},{y},{pat(n,i)},00000000,Y')
tile_cond('title',180,88,56,0x53)
tile_cond('carrier',900,112,80,0x6d)
# Unique stable cockpit coaming from the second nametable, as displayed at y=128.
tile_cond('cockpit',3240,80,132,0x51)
lines+=['<condition>prompt,frameRange,64,20','<condition>panel,positionCheckY,>=,128',
 '[title]<background>title.png,1,0,0,30',
 '[title&prompt]<background>title_prompt.png,1,0,0,31',
 '[carrier]<background>carrier.png,1,0,0,30',
 '[cockpit]<background>cockpit.png,1,0,0,10']
# Transparency removes only original static cockpit housing. Live data is kept.
remove={0,0xf,*range(0x50,0x62),0x69,0x6a,0x6b,0x70,0x7b,0x8b,0x92}
# Analog dials: keep markings and use muted neutral tones instead of orange.
analog=set(range(0x5c,0x60))|set(range(0x6c,0x70))|set(range(0x7c,0x80))|set(range(0x8c,0x90))
remove|=analog
# Actual glyph shapes; all text uses exact original tile matching, excluding artwork reuse.
chars={i+1:str(i) for i in range(10)}|{0x10+i:chr(65+i) for i in range(26)}|{0x0b:"'",0x0c:'.',0x0d:'?',0x0e:'!'}
chrdata=capture(3240,'chr')
def decode(b):return np.array([[((b[y]>>(7-x))&1)+2*((b[y+8]>>(7-x))&1) for x in range(8)] for y in range(8)])
def glyph(char):
 im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 dr.text((16,14),char,font=font,anchor='mm',fill=(147,242,151,255))
 return im
atlas=Image.new('RGBA',(512,512));records=[];slot=0
# Render all live cockpit data, including grid, gauges, tiny labels, underlays and marks.
live=set(range(1,0x50))|set(range(0x62,0x99))|{0xb1,0xb2,0xb3,0xb4,0xb5}
live|=analog
live-=remove
for i in sorted(live):
 if False:im=glyph(chars[i])
 else:
  a=decode(chrdata[i*16:i*16+16]);im=Image.new('RGBA',(8,8));px=im.load()
  for y in range(8):
   for x in range(8):
    v=a[y,x]
    # Avoid painting source background fields over the cockpit master.
    if i in analog: col=[(0,0,0,0),(150,181,193,255),(0,0,0,0),(203,225,228,255)][v]
    else:col=[(0,0,0,0),(117,233,126,255),(6,29,23,160),(167,248,166,255)][v]
    px[x,y]=col
  im=im.resize((32,32),Image.Resampling.NEAREST)
 x=slot%16*32;y=slot//16*32;atlas.alpha_composite(im,(x,y));records.append((i,x,y));slot+=1
sprite_records=[]
for i in range(0x101,0x10a):
 a=decode(chrdata[i*16:i*16+16]);im=Image.new('RGBA',(32,32));dr=ImageDraw.Draw(im)
 for yy in range(8):
  for xx in range(8):
   v=a[yy,xx]
   if v:dr.rectangle((xx*4,yy*4,xx*4+3,yy*4+3),fill={1:(138,255,183,255),2:(18,46,41,255),3:(5,24,22,255)}[int(v)])
 x=slot%16*32;y=slot//16*32;atlas.alpha_composite(im,(x,y));sprite_records.append((i,x,y));slot+=1
save_png(atlas,P/'instruments.png')
# Ignore palette only through default fallback, scoped to cockpit and lower screen.
# Palette matched rules first, default mappings for legitimate flashing palettes follow.
for i in sorted(remove):lines.append(f'[cockpit&panel]<tile>0,{pat(3240,i)},0F2A0A31,0,0,1,Y')
for i,x,y in records:lines.append(f'[cockpit&panel]<tile>1,{pat(3240,i)},0F2A0A31,{x},{y},1,Y')
for i,x,y in sprite_records:lines.append(f'[cockpit]<tile>1,{pat(3240,i)},FF2A100F,{x},{y},1,Y')
# Briefing/menu font shares the CHR alphabet; explicitly scoped by its palette.
for i,x,y in records:
 if i in chars:lines.append(f'<tile>1,{pat(3240,i)},0F2A0F0F,{x},{y},1,N')
(P/'hires.txt').write_text('\n'.join(lines)+'\n')
meta={'version': '0.2.0', 'emulator': 'MesenCE 2.2.1 (user supplied)', 'scale': 4, 'features': ['Approved title and native-timed animated launch', 'Impact-safe HD cockpit with native shake registration', 'Fine targeting reticle and radar display', 'Native-driven smooth missile digits and fuel segments', 'Updated landing instructions and pitch-aircraft indicator'], 'not_yet_redrawn': ['Enemy aircraft and projectiles', 'Clouds, ocean and terrain', 'Briefing map and weapon diagrams', 'Later missions, landing and refuelling'], 'assets': {'title': 'source/title_master.png', 'carrier': 'source/carrier_master.png', 'cockpit': 'source/cockpit_master.png'}, 'approved_intro_version': '0.1.1'}
(R/'source/build_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
import subprocess
subprocess.run(['python3',str(R/'scripts/build_launch.py')],check=True)
m=json.loads((R/'source/launch_mappings.json').read_text())
t=(P/'hires.txt').read_text();idx=t.index('<condition>');t=t[:idx]+'\n'.join(m['conditions'])+'\n'+t[idx:]
t=t.replace('[carrier]<background>carrier.png,1,0,0,30','[carrier]<background>carrier.png,1,0,0,30\n'+'\n'.join(m['backgrounds']))
(P/'hires.txt').write_text(t)
subprocess.run(['python3',str(R/'scripts/build_panels.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_flight_ui.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_menus.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_aircraft.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_combat_effects.py')],check=True)
subprocess.run(['python3',str(R/'scripts/build_environment.py')],check=True)
meta=json.loads((R/'source/build_manifest.json').read_text())
subprocess.run(['python3',str(R/'scripts/build_damage_hud.py')],check=True)
meta['version']='0.6.0'
meta['features'].append('Neutral windshield coaming and consistent attitude-display tick colors')
meta['features'].append('Correct inland-water fills within the original mission-one coastline')
meta['features'].append('Painted enemy aircraft across native banks, inverted views and distance sizes')
meta['features'].append('Native-timed missiles, ignition, explosions and smoke')
meta['not_yet_redrawn']=[item for item in meta['not_yet_redrawn'] if item!='Enemy aircraft and projectiles']
meta['assets'].update({'enemy_aircraft': 'source/enemy_aircraft_atlas.png', 'combat_effects': 'source/combat_effects_atlas.png'})
meta['combat_coverage']={'aircraft_layouts':116,'aircraft_patterns':145,'effect_layouts':19,'effect_patterns':27,'cloud_layouts':4,'cloud_patterns':10,'scope':'Mapped mission-one layouts and observed sprite palettes; later missions need coverage'}
meta['features'].append('Correct white cloud distance sizes, painted sky, ocean and runway surfaces')
meta['assets'].update({name:'source/environment_'+name+'_master.png' for name in ['sky','water','runway','cloud','clouddeck']})
meta['not_yet_redrawn']=[item for item in meta['not_yet_redrawn'] if item!='Clouds, ocean and terrain']
meta['not_yet_redrawn'].append('Terrain, later-mission scenery and refuelling')
meta['features'].append('Native-banked sky, ocean and feathered cloud deck without blue/white horizon dither')
meta['environment_coverage']='Mission-one native bank stages, vertical scroll and palette transitions; controller-driven cloud turns plus takeoff and landing replays'
(R/'source/build_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
meta['features'].extend(['Live hull-health bar and percentage from native damage state','Rear-threat instrument redraw with native warning timing and moving target','Readable incoming missile growth stages and complete impact burst','HD scenery preserved during the native red damage flash'])
meta['assets'].update({'incoming_missile':'source/incoming_missile_master.png','impact_burst':'source/impact_burst_master.png'})
subprocess.run(['python3',str(R/'scripts/build_landing.py')],check=True)
meta['version']='0.7.0'
meta['features'].extend(['Opaque carrier approach across 21 native distance stages','Painted side-on touchdown and animated water with native jet movement','Clean deck rollout without foreground mask blocks','Mission debrief with native score and lives','Cannon projectiles distinct from true missile artwork'])
meta['assets'].update({name:'source/landing_'+name+'_master.png' for name in ['approach','broadside','jet']})
meta['landing_coverage']='Supplied successful mission-one landing, touchdown, rollout and debrief; failure outcomes and later missions are not newly covered'
meta['not_yet_redrawn']=[x for x in meta['not_yet_redrawn'] if x!='Later missions, landing and refuelling']
subprocess.run(['python3',str(R/'scripts/build_landing_failure.py')],check=True)
meta['version']='0.7.1'
meta['features'].append('Painted carrier scenery throughout failed landing, with six native-timed fire and water-spray stages')
meta['assets']['landing_crash']='source/landing_crash_master.png'
meta['landing_coverage']='Supplied successful mission-one landing and failed water landing through debrief; other failure outcomes and later missions need additional coverage'
subprocess.run(['python3',str(R/'scripts/build_landing_transition.py')],check=True)
meta['version']='0.7.2'
meta['features'].append('No original-art flash when entering debrief or leaving it for the next briefing')
subprocess.run(['python3',str(R/'scripts/build_transition_flashes.py')],check=True)
meta['version']='0.7.3'
meta['features'].extend(['Styled danger-to-radar clearing and lethal HUD palette','Additional carrier-rollout edge and moving light phases without original-art flashes'])
subprocess.run(['python3',str(R/'scripts/build_mission2.py')],check=True)
meta['version']='0.8.0'
meta['features'].extend(['Mission 2 briefing and loadout using the approved console style','Mission 2 sea, sky and banked horizon palette coverage','Painted patrol boats and submarines at native distance sizes','Additional Mission 2 aircraft reuse approved combat art','Visible tanker, extending refuelling boom and native control instructions'])
meta['assets'].update({name:'source/mission2_'+name+'_master.png' for name in ['boat','submarine','tanker','boom']})
meta['mission2_coverage']='Supplied Mission 2 briefing, takeoff, naval combat and refuelling entry through the end of the recording; refuelling completion and later Mission 2 sections remain unrecorded'
meta['not_yet_redrawn']=['Unrecorded Mission 2 sections after the supplied refuelling clip','Later missions, terrain, remaining outcomes and ending']
subprocess.run(['python3',str(R/'scripts/build_mission2_fixes.py')],check=True)
meta['version']='0.8.1'
meta['features'].extend(['Clean Mission 2 takeoff-to-flight horizon','Mapped distant enemy and correct small boat artwork','Brighter submarine hull and wake','Amber danger target throughout HUD transitions','Styled vertical radar lines during refuelling entry'])
meta['assets']['submarine_bright']='source/mission2_submarine_bright_master.png'
subprocess.run(['python3',str(R/'scripts/build_refuel_entry.py')],check=True)
meta['version']='0.8.2'
meta['features'].append('One tanker entrance from the right, matching native refueling arrival')
subprocess.run(['python3',str(R/'scripts/build_mission2_completion.py')],check=True)
meta['version']='0.9.0'
meta['features'].extend(['Single tanker departure with no duplicate after the scroll reset',
 'Clean banked horizon during the Mission 2 boss route',
 'Painted carrier boss, damaged pose and destruction with native-driven amber health meter'])
meta['assets']['mission2_boss_damaged']='source/mission2_boss_damaged_master.png'
meta['mission2_coverage']='Supplied Mission 2 briefing, takeoff, naval combat, refueling entry and completion, carrier boss fight, successful landing and debrief'
meta['not_yet_redrawn']=['Unrecorded target sizes, later missions, terrain, remaining outcomes and ending']
subprocess.run(['python3',str(R/'scripts/build_mission2_approach.py')],check=True)
meta['version']='0.9.1'
meta['features']=[('Painted carrier approach, independent bridge/guns and native amber health meter'
 if item=='Painted carrier boss, damaged pose and destruction with native-driven amber health meter' else item) for item in meta['features']]
meta['features'].extend(['Twelve carrier distance sizes with opaque deck and native-timed bridge/gun sprites',
 'Three additional banked fighter poses reuse approved aviation artwork',
 'Correct numeral in the native 1ST TARGET message'])
meta['assets'].pop('mission2_boss_damaged',None)
meta['assets'].update({'mission2_boss_approach':'source/mission2_boss_approach_master.png',
 'mission2_boss_components':'source/mission2_boss_components_master.png'})
meta['mission2_coverage']='Supplied Mission 2 briefing, takeoff, naval combat, refueling entry/completion, carrier approach through close pass, boss combat, successful landing and debrief'
subprocess.run(['python3',str(R/'scripts/build_mission3.py')],check=True)
meta['version']='0.10.0'
meta['features'].extend(['Mission 3 briefing map, cockpit and native live instruments',
 'Banked and scrolling painted desert terrain with clean sky edge',
 'Native-sized radar dishes, armored ground targets and modular barricades',
 'Additional banked fighter poses and ground-palette projectile coverage',
 'Mission 3 refueling arrival, boom, guidance and departure reuse the approved artwork'])
meta['assets'].update({name:'source/mission3_'+name+'_master.png' for name in ['desert','radar','tank','barrier']})
meta['mission3_coverage']='Supplied 21,467-frame movie: preceding Mission 2 debrief, Mission 3 briefing, takeoff, desert combat, refueling completion, return to combat and game over'
meta['not_yet_redrawn']=['Mission 3 enemy base/boss and landing, unrecorded target sizes and outcomes, Mission 4 and ending']
subprocess.run(['python3',str(R/'scripts/build_mission3_tanks.py')],check=True)
meta['version']='0.10.1'
meta['features'].append('Both close tank orientations stay HD in Mission 3, with unchanged artwork')
subprocess.run(['python3',str(R/'scripts/build_mission3_completion.py')],check=True)
meta['version']='0.11.0'
meta['features'].extend(['Missing mirrored aircraft, close radar and large wall tiles remain HD',
 'Seven recorded desert-base approach sizes with independent gun sprites',
 'Native full, half and empty boss-health segments in a matching BASE display',
 'Desert and base artwork remain HD through the recorded damage and retry transition'])
meta['assets']['mission3_base']='source/mission3_base_master.png'
meta['mission3_coverage']+='; six further recordings cover missing enemy views, the base approach through distance stage 6, damage and retry'
meta['not_yet_redrawn']=['Unrecorded Mission 3 base sizes, defeat and landing; Mission 4, ending and other unrecorded outcomes']
subprocess.run(['python3',str(R/'scripts/build_mission3_radar_edges.py')],check=True)
meta['version']='0.11.1'
meta['features'].append('Complete radar silhouettes across native gaps in both recorded palette families')
(R/'source/build_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
(P/'README.txt').write_bytes((R/'README.txt').read_bytes())
# Install pack/ manually or through the emulator after reviewing the build.
print('Built',len(lines),'lines;',slot,'instrument tiles')
