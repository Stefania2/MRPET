import csv
from pathlib import Path
import math

path = Path('critical_region_refined.csv')
rows = []
with path.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append((float(r['velocity']), float(r['coherence']), float(r['probability'])))

# Build normal equation for quadratic model: P = a0 + a1*v + a2*c + a4*v*c + a3*v^2 + a5*c^2
# x vector = [1, v, c, v*c, v^2, c^2]
X = []
y = []
for v, c, p in rows:
    X.append([1.0, v, c, v*c, v*v, c*c])
    y.append(p)

# Compute ATA and ATy
n = 6
ATA = [[0.0] * n for _ in range(n)]
ATy = [0.0] * n
for xi, yi in zip(X, y):
    for i in range(n):
        ATy[i] += xi[i] * yi
        for j in range(n):
            ATA[i][j] += xi[i] * xi[j]

# Solve ATA * coeffs = ATy with Gaussian elimination
A = [row[:] for row in ATA]
b = ATy[:]
for i in range(n):
    # pivot
    pivot = i
    for j in range(i, n):
        if abs(A[j][i]) > abs(A[pivot][i]):
            pivot = j
    if abs(A[pivot][i]) < 1e-12:
        raise RuntimeError('Singular matrix')
    A[i], A[pivot] = A[pivot], A[i]
    b[i], b[pivot] = b[pivot], b[i]
    piv = A[i][i]
    A[i] = [x / piv for x in A[i]]
    b[i] /= piv
    for j in range(i+1, n):
        factor = A[j][i]
        if factor != 0.0:
            A[j] = [aj - factor * ai for aj, ai in zip(A[j], A[i])]
            b[j] -= factor * b[i]
coeffs = [0.0] * n
for i in range(n-1, -1, -1):
    coeffs[i] = b[i] - sum(A[i][j] * coeffs[j] for j in range(i+1, n))

a0, a1, a2, a4, a3, a5 = coeffs
ss_res = 0.0
for xi, yi in zip(X, y):
    pred = sum(ci * xij for ci, xij in zip(coeffs, xi))
    ss_res += (yi - pred) ** 2
ss_tot = sum((yi - sum(y) / len(y)) ** 2 for yi in y)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

A_mat = [[2*a3, a4], [a4, 2*a5]]
b_vec = [-a1, -a2]
# Solve 2x2 linear system
det = A_mat[0][0] * A_mat[1][1] - A_mat[0][1] * A_mat[1][0]
peak = None
if abs(det) > 1e-12:
    v0 = (b_vec[0] * A_mat[1][1] - b_vec[1] * A_mat[0][1]) / det
    c0 = (A_mat[0][0] * b_vec[1] - A_mat[1][0] * b_vec[0]) / det
    P0 = a0 + a1*v0 + a2*c0 + a4*v0*c0 + a3*v0*v0 + a5*c0*c0
    peak = (v0, c0, P0)

print('coeffs', coeffs)
print('r2', r2)
print('peak', peak)
if peak is not None:
    v0, c0, p0 = peak
    for dv in (-0.01, 0.0, 0.01):
        for dc in (-0.01, 0.0, 0.01):
            vv = v0 + dv
            cc = c0 + dc
            val = a0 + a1*vv + a2*cc + a4*vv*cc + a3*vv*vv + a5*cc*cc
            print(f'P({vv:.3f},{cc:.3f}) = {val:.6f}')
