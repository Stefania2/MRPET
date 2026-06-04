import csv
from pathlib import Path

path = Path('critical_region_refined.csv')
rows = []
with path.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append((float(r['velocity']), float(r['coherence']), float(r['probability'])))
# Find global max
max_row = max(rows, key=lambda x: x[2])
v0, c0, A = max_row
print('peak', max_row)
# Select nearby points within 0.05 in v and c
near = [r for r in rows if abs(r[0]-v0) <= 0.05 and abs(r[1]-c0) <= 0.05 and r != max_row]
print('near points', len(near))
for r in sorted(near, key=lambda x:(abs(x[0]-v0)+abs(x[1]-c0))):
    print(r)
# Fit P = A - B*(v-v0)^2 - C*(c-c0)^2 using least squares on nearby points
points = near
SBB = SBC = SCC = SBD = SCD = 0.0
for v, c, p in points:
    dv = (v - v0) ** 2
    dc = (c - c0) ** 2
    dP = A - p
    SBB += dv * dv
    SBC += dv * dc
    SCC += dc * dc
    SBD += dv * dP
    SCD += dc * dP
# Solve 2x2 linear system [SBB SBC; SBC SCC] [B; C] = [SBD; SCD]
det = SBB * SCC - SBC * SBC
if abs(det) < 1e-12:
    raise RuntimeError('Singular fit matrix')
B = (SBD * SCC - SBC * SCD) / det
C = (SBB * SCD - SBC * SBD) / det
print('fit A', A, 'B', B, 'C', C)
print('model: P(v,c) = {:.6f} - {:.6f}*(v-{:.3f})^2 - {:.6f}*(c-{:.3f})^2'.format(A, B, v0, C, c0))
for v, c, p in points[:10]:
    pred = A - B * (v - v0) ** 2 - C * (c - c0) ** 2
    print('point', v, c, p, 'pred', pred, 'err', p-pred)
