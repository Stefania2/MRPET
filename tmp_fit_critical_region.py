import csv
from pathlib import Path
import numpy as np

path = Path('critical_region_refined.csv')
rows = []
with path.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append((float(r['velocity']), float(r['coherence']), float(r['probability'])))

X = np.array([[1.0, v, c, v*c, v**2, c**2] for v, c, _ in rows])
y = np.array([p for _, _, p in rows])
coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
a0, a1, a2, a4, a3, a5 = coeffs
ss_res = np.sum((y - X @ coeffs) ** 2)
ss_tot = np.sum((y - y.mean()) ** 2)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

# Solve gradient = 0 for a quadratic surface: dP/dv = a1 + a4 c + 2 a3 v = 0; dP/dc = a2 + a4 v + 2 a5 c = 0
A = np.array([[2 * a3, a4], [a4, 2 * a5]])
b = np.array([-a1, -a2])
peak = None
try:
    peak = np.linalg.solve(A, b)
except np.linalg.LinAlgError:
    peak = None

print('coeffs', coeffs)
print('r2', r2)
print('peak', peak)
if peak is not None:
    v0, c0 = peak
    P0 = a0 + a1 * v0 + a2 * c0 + a4 * v0 * c0 + a3 * v0**2 + a5 * c0**2
    print('peak_estimate', v0, c0, P0)
    # Evaluate near actual domain boundaries
    for dv in [0.0, -0.01, 0.01]:
        for dc in [0.0, -0.01, 0.01]:
            vv = v0 + dv; cc = c0 + dc
            print(f'P({vv:.3f},{cc:.3f}) = {a0 + a1*vv + a2*cc + a4*vv*cc + a3*vv**2 + a5*cc**2:.6f}')
