import importlib.util, pathlib, sys
path = pathlib.Path(r'c:/QuantumComputing/dewscifrar copy.py')
spec = importlib.util.spec_from_file_location('dewscifrar_copy', str(path))
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

v = 0.675
c = 1.0
agent = mod.ExternalAgent('observador', 0, 70.0, v, c)
physical_influence = mod.measure_physical_influence_with_qiskit(agent, len(mod.HISTORY))
print('physical_influence', physical_influence)
restored = 2
print('restored', restored, 'restored event', mod.HISTORY[restored], 'signature', mod.text_signature(mod.HISTORY[restored]))
print('probability', mod.restoration_probability(restored, agent, len(mod.HISTORY), 7, shots=8192, repeats=3))
