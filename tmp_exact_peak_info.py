import importlib.util
import pathlib
import sys

path = pathlib.Path(r'c:/QuantumComputing/dewscifrar copy.py')
spec = importlib.util.spec_from_file_location('dewscifrar_copy', str(path))
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

v = 0.675
c = 1.0
agent = mod.ExternalAgent('observador', 0, 70.0, v, c)
physical_influence = mod.measure_physical_influence_with_qiskit(agent, len(mod.HISTORY))
gamma = mod.lorentz_factor(v)
effective_t = round(mod.relativistic_time(agent, mod.CURRENT_TIME)) + agent.entry_time
effective_k = round(mod.relativistic_time(agent, mod.FUTURE_JUMP)) + physical_influence
restored = mod.restoration_index(effective_t, effective_k, len(mod.HISTORY))
print('v', v)
print('coherence', c)
print('gamma', gamma)
print('physical_influence', physical_influence)
print('effective_t', effective_t)
print('effective_k', effective_k)
print('restored', restored)
print('restored event', mod.HISTORY[restored])
print('signature', mod.text_signature(mod.HISTORY[restored]))
print('state 7 probability', mod.restoration_probability(restored, agent, len(mod.HISTORY), 7, shots=1024, repeats=2))
