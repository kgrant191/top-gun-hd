"""Keep landing transitions covered while the native mode advances before PPU data."""
from pathlib import Path

R = Path(__file__).resolve().parents[1]
path = R/'pack/hires.txt'
lines = path.read_text().splitlines()
assert not any(l.startswith('<condition>landingNextBriefing,') for l in lines)

# The mode changes to debrief one frame before the outgoing carrier/cockpit
# nametable is cleared. Keep the native blank transition covered until the
# actual debrief glyph signature becomes visible.
insert = next(i for i,l in enumerate(lines) if l.startswith('<condition>'))
lines[insert:insert] = [
    '<condition>landingNextBriefing,memoryCheckConstant,0018,==,05',
    '<condition>landingBriefingInit,memoryCheckConstant,0019,==,00',
    '<condition>landingTransferIdle,memoryCheckConstant,001B,==,00',
]
insert = next(i for i,l in enumerate(lines) if '<background>' in l)
lines[insert:insert] = ['[landingDebrief&!debriefVisible]<background>landing_black.png,1,0,0,39']

# Likewise, mode 5 starts before the outgoing results screen has been cleared.
# Reuse its existing artwork and exact glyph rules while that screen remains
# rendered. Cached tileAtPosition data survives disabled PPU rendering, so
# stop the extension when the native transfer begins and keep it limited to
# the briefing initializer. This preserves the original blank loading frames.
extended = []
for line in lines:
    extended.append(line)
    if line.startswith('[landingDebrief&debriefVisible]'):
        extended.append(line.replace('[landingDebrief&', '[landingNextBriefing&landingBriefingInit&landingTransferIdle&',1))
lines = extended
lines[0] = '# Top Gun HD v0.7.2 - landing/debrief transition coverage'
path.write_text('\n'.join(lines)+'\n')
print('Landing transitions: covered pre-debrief blank and outgoing results frame')
