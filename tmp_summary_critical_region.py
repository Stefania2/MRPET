import csv
from pathlib import Path

path = Path('critical_region_refined.csv')
rows = []
with path.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append((float(r['velocity']), float(r['coherence']), int(r['physical_influence']), int(r['restored_index']), float(r['probability'])))
rows.sort(key=lambda x: x[4], reverse=True)
print('count', len(rows))
print('top 10')
for r in rows[:10]:
    print(r)
print('by coherence')
cs = sorted(set(r[1] for r in rows))
for c in cs:
    best = max((r for r in rows if r[1] == c), key=lambda x: x[4])
    print(f'coherence {c:.3f}: best v={best[0]:.3f}, p={best[4]:.6f}, restored={best[3]}, phys_inf={best[2]}')
