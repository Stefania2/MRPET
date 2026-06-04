import importlib.util, pathlib, sys
path = pathlib.Path(r'c:/QuantumComputing/dewscifrar copy.py')
spec = importlib.util.spec_from_file_location('dewscifrar_copy', str(path))
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

v = 0.675
c = 1.0
agent = mod.ExternalAgent('observador', 0, 70.0, v, c)
print('gamma', mod.lorentz_factor(v))
print('normalized_energy_angle', mod.normalized_energy_angle(agent))
print('observer_phase', mod.observer_phase(agent))
print('coupling[0][1]', mod.event_coupling_matrix(agent, mod.HISTORY)[0][1])
print('restoration_gate_angles', mod.restoration_gate_angles(agent, mod.text_signature(mod.HISTORY[2]), 6))
