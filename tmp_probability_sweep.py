import importlib.util
import pathlib
import sys
import csv
import numpy as np

path = pathlib.Path(r'c:/QuantumComputing/dewscifrar copy.py')
spec = importlib.util.spec_from_file_location('dewscifrar_copy', str(path))
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

velocities = np.linspace(0.55, 0.75, 9).tolist()
coherences = np.linspace(0.8, 1.0, 9).tolist()
results = []
for v in velocities:
    for c in coherences:
        agent = mod.ExternalAgent('observador', 0, 70.0, v, c)
        physical_influence = mod.measure_physical_influence_with_qiskit(agent, len(mod.HISTORY))
        effective_t = round(mod.relativistic_time(agent, mod.CURRENT_TIME)) + agent.entry_time
        effective_k = round(mod.relativistic_time(agent, mod.FUTURE_JUMP)) + physical_influence
        restored = mod.restoration_index(effective_t, effective_k, len(mod.HISTORY))
        prob = mod.restoration_probability(restored, agent, len(mod.HISTORY), target_state=7, shots=1024, repeats=2)
        results.append((v, c, physical_influence, restored, prob))

csv_path = pathlib.Path(r'c:/QuantumComputing/critical_region_refined.csv')
with csv_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['velocity', 'coherence', 'physical_influence', 'restored_index', 'probability'])
    for row in results:
        writer.writerow([f'{row[0]:.4f}', f'{row[1]:.4f}', row[2], row[3], f'{row[4]:.6f}'])

max_row = max(results, key=lambda r: r[4])
print('csv_path', csv_path)
print('max_row', max_row)
best_by_v = {}
for v, c, _, _, p in results:
    if v not in best_by_v or p > best_by_v[v][2]:
        best_by_v[v] = (c, p)
print('best_by_v')
for v in sorted(best_by_v):
    print(f'{v:.3f}: coherence={best_by_v[v][0]:.3f}, p={best_by_v[v][2]:.6f}')
