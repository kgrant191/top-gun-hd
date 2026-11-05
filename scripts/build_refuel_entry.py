"""Show the tanker once during its native right-to-center entrance."""
from pathlib import Path
from PIL import Image
from pack_io import save_png

R = Path(__file__).resolve().parents[1]
P = R / 'pack'
lines = (P / 'hires.txt').read_text().splitlines()
assert '<condition>refuelArrival,memoryCheckConstant,009F,==,01' not in lines

# The original two-page plate is needed after the native scroll resets.
# During arrival, its left-page copy appears early and exits to the left.
# Preserve only the right-page copy for that phase; reuse the exact artwork.
plate = Image.open(P / 'mission2_tanker.png').convert('RGBA')
assert plate.size == (2048, 1536)
entry = Image.new('RGBA', plate.size)
entry.paste(plate.crop((1024, 0, 2048, 1536)), (1024, 0))
save_png(entry, P / 'mission2_tanker_entry.png')

i = next(i for i, line in enumerate(lines) if '<tile>' in line or '<background>' in line)
lines[i:i] = [
    '<condition>refuelArrival,memoryCheckConstant,009F,==,01',
    '[cockpit&cockpitBorder&missionTwo&mission2Flight&refuelRoute&refuelArrival]'
    '<background>mission2_tanker_entry.png,1,1,1,31',
]
lines[0] = '# Top Gun HD v0.8.2 - Single tanker entrance during refueling'
(P / 'hires.txt').write_text('\n'.join(lines) + '\n')
print('Refueling entrance: one incoming tanker; original plate retained after arrival')
