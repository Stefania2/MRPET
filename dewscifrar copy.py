"""
Simulacion de restauracion de estados en un espacio temporal discreto.

Este modelo combina:
  * un espacio de eventos discretos H,
  * observadores relativistas con masa, velocidad y coherencia,
  * un Hamiltoniano de transicion entre eventos,
  * evolucion cuántica gobernada por fases fisicas.

Cada evento historico se representa como un vector de amplitud en el
espacio de Hilbert discreto. El observador modifica el sistema a traves de:
  * dilatacion temporal relativista: t' = gamma * t,
  * amplitudes de transicion A(i->j) entre eventos,
  * un Hamiltoniano que depende de energia, gravedad y coherencia.

Se evita la narrativa de "viaje en el tiempo" y se enfatiza una aproximacion
como simulacion computacional de restauracion de estados.

Instalacion si hace falta:
    python -m pip install qiskit qiskit-aer

Ejecucion:
    python dewscifrar.py
"""

from __future__ import annotations

import math
import sys
import os
import argparse
from dataclasses import dataclass
from html import escape
from pathlib import Path
import csv
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import QFTGate


HISTORY = [
    "la semilla fue sembrada",
    "la raiz busco agua",
    "el tallo encontro luz",
    "la flor se abrio",
    "el fruto guardo memoria",
    "la semilla cayo otra vez",
    "la tierra recordo el ciclo",
    "el comienzo regreso",
]
CURRENT_TIME = 11
FUTURE_JUMP = 5
REGISTER_BITS = 6
GRAPH_PATH = Path(__file__).with_name("simulacion_tiempo.svg")
BOLTZMANN_CONSTANT = 1.380649e-23
LIGHT_SPEED = 299_792_458
GRAVITATIONAL_CONSTANT = 6.67430e-11
REDUCED_PLANCK_CONSTANT = 1.054571817e-34
PLANCK_LENGTH = 1.616255e-35
PLANCK_ENERGY = 1.9561e9

DEFAULT_RESULT_CSV = Path(__file__).with_name("restauracion_resultados.csv")
DEFAULT_SWEEP_CSV = Path(__file__).with_name("velocity_state_table.csv")
CSV_FIELD_NAMES = [
    "time",
    "jump",
    "effective_time",
    "effective_jump",
    "cycle_size",
    "agent_name",
    "agent_entry_time",
    "agent_mass_kg",
    "agent_velocity_fraction_c",
    "agent_coherence",
    "physical_influence",
    "kinetic_energy_j",
    "gravitational_radius_m",
    "restored_index",
    "restored_event",
    "measured_restored_index",
    "measured_restored_event",
    "past_index",
    "present_index",
    "future_index",
    "memory_units",
    "horizon_area_m2",
    "horizon_entropy_j_per_k",
    "top_branch_state",
    "top_branch_probability",
    "branch_list",
]


@dataclass(frozen=True)
class ExternalAgent:
    name: str
    entry_time: int
    mass_kg: float
    velocity_fraction_c: float
    coherence: float


@dataclass(frozen=True)
class TimelineRegister:
    past: int
    present: int
    future: int


@dataclass(frozen=True)
class CycleResult:
    t: int
    k: int
    effective_t: int
    effective_k: int
    n: int
    agent: ExternalAgent
    physical_influence: int
    kinetic_energy: float
    gravitational_radius: float
    past_index: int
    present_index: int
    future_index: int
    restored_index: int
    measured_restored_index: int
    branches: list[dict[str, float]]
    memory_units: int
    horizon_area: float
    horizon_entropy: float


def load_qiskit():
    try:
        from qiskit import QuantumCircuit, transpile
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Qiskit no esta instalado. Ejecuta:\n"
            "  python -m pip install qiskit qiskit-aer"
        ) from exc

    try:
        from qiskit_aer import AerSimulator

        backend = AerSimulator()
    except ModuleNotFoundError:
        try:
            from qiskit.providers.basic_provider import BasicSimulator

            backend = BasicSimulator()
        except ModuleNotFoundError:
            try:
                from qiskit import BasicAer

                backend = BasicAer.get_backend("qasm_simulator")
            except Exception as exc:  # pragma: no cover - depende de la version instalada.
                raise RuntimeError(
                    "Qiskit esta instalado, pero no encontre un simulador local. "
                    "Instala qiskit-aer con:\n"
                    "  python -m pip install qiskit-aer"
                ) from exc

    return QuantumCircuit, transpile, backend


def cycle_index(time: int, cycle_size: int) -> int:
    return time % cycle_size


def past_index(time: int, cycle_size: int) -> int:
    return cycle_index(time - 1, cycle_size)


def present_index(time: int, cycle_size: int) -> int:
    return cycle_index(time, cycle_size)


def future_index(time: int, jump: int, cycle_size: int) -> int:
    return cycle_index(time + jump, cycle_size)


def restoration_index(time: int, jump: int, cycle_size: int) -> int:
    return cycle_index(time + jump, cycle_size)


def planck_area() -> float:
    return GRAVITATIONAL_CONSTANT * REDUCED_PLANCK_CONSTANT / LIGHT_SPEED**3


def horizon_area_from_restoration(restored_index: int) -> float:
    memory_units = restored_index + 1
    return 4 * memory_units * planck_area()


def horizon_entropy(area: float) -> float:
    numerator = BOLTZMANN_CONSTANT * LIGHT_SPEED**3 * area
    denominator = 4 * GRAVITATIONAL_CONSTANT * REDUCED_PLANCK_CONSTANT
    return numerator / denominator


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def lorentz_factor(beta: float) -> float:
    beta = clamp(abs(beta), 0.0, 0.999999)
    return 1 / math.sqrt(1 - beta**2)


def relativistic_time(agent: ExternalAgent, proper_time: int) -> float:
    return lorentz_factor(agent.velocity_fraction_c) * proper_time


def normalized_energy_angle(agent: ExternalAgent) -> float:
    energy = kinetic_energy(agent)
    normalized = math.atan(energy / (PLANCK_ENERGY * 1e4))
    return clamp(normalized * 2.0, 0.0, math.pi)


def observer_phase(agent: ExternalAgent) -> float:
    base_phase = ((text_signature(agent.name) % 16) + 1) / 16.0 * math.pi
    return base_phase * clamp(agent.coherence, 0.0, 1.0)


def event_coupling_matrix(agent: ExternalAgent, history: list[str]) -> list[list[float]]:
    n = len(history)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    gravity_scale = clamp(math.log1p(gravitational_radius(agent) / PLANCK_LENGTH), 0.0, 4.0)
    coherence = clamp(agent.coherence, 0.0, 1.0)
    mass_scale = clamp(agent.mass_kg / 1000.0, 0.0, 10.0)
    velocity_scale = clamp(agent.velocity_fraction_c, 0.0, 1.0)

    for i, event_i in enumerate(history):
        sig_i = text_signature(event_i)
        for j, event_j in enumerate(history):
            if i == j:
                continue
            sig_j = text_signature(event_j)
            overlap = 1.0 / (1.0 + abs(sig_i - sig_j))
            phase = ((sig_i + sig_j) % 8) / 8.0 * math.pi
            base_strength = 0.2 + 0.6 * coherence
            coupling = (
                overlap
                * base_strength
                * (1.0 + 0.05 * mass_scale)
                * (1.0 + 0.2 * velocity_scale)
                * (1.0 + 0.15 * gravity_scale)
            )
            matrix[i][j] = clamp(coupling, 0.0, 1.0) * math.pi
    return matrix


def kinetic_energy(agent: ExternalAgent) -> float:
    gamma = lorentz_factor(agent.velocity_fraction_c)
    return (gamma - 1) * agent.mass_kg * LIGHT_SPEED**2


def gravitational_radius(agent: ExternalAgent) -> float:
    return 2 * GRAVITATIONAL_CONSTANT * agent.mass_kg / LIGHT_SPEED**2


def perturbation_angles(agent: ExternalAgent, bit_count: int) -> list[float]:
    energy_ratio = max(0.0, kinetic_energy(agent)) / PLANCK_ENERGY
    gravity_ratio = max(0.0, gravitational_radius(agent)) / PLANCK_LENGTH
    coherence = clamp(agent.coherence, 0.0, 1.0)
    entry_phase = (abs(agent.entry_time) + 1) / 10
    energy_phase = math.log1p(energy_ratio)
    gravity_phase = math.log1p(gravity_ratio)
    decoherence_phase = (1 - coherence) * math.pi

    angles = []
    for index in range(bit_count):
        phase = (
            energy_phase / (index + 1)
            + gravity_phase * (index + 1) / bit_count
            + entry_phase
            + decoherence_phase
        )
        angles.append((phase % (2 * math.pi)) * coherence)
    return angles


def restoration_gate_angles(agent: ExternalAgent, event_signature: int, bit_count: int) -> list[float]:
    energy_factor = math.log1p(kinetic_energy(agent) / PLANCK_ENERGY)
    gravity_factor = math.log1p(gravitational_radius(agent) / PLANCK_LENGTH)
    coherence = clamp(agent.coherence, 0.0, 1.0)
    signature_base = ((event_signature % 64) + 1) / 64.0
    entry_offset = ((agent.entry_time % 8) + 8) % 8 / 8.0

    return [
        (
            2 * math.pi * signature_base * (index + 1) / bit_count
            + energy_factor * 0.5
            + gravity_factor * 0.3 * (index + 1) / bit_count
            + (1 - coherence) * math.pi
            + entry_offset * math.pi
        ) % (2 * math.pi)
        for index in range(bit_count)
    ]


def build_physical_perturbation_circuit(QuantumCircuit, agent: ExternalAgent, bit_count: int):
    circuit = QuantumCircuit(bit_count, bit_count)

    energy_angle = normalized_energy_angle(agent)
    observer_angle = observer_phase(agent)

    for index in range(bit_count):
        circuit.ry(energy_angle / (index + 1), index)
        circuit.rz(observer_angle * (index + 1) / bit_count, index)

    for i in range(bit_count - 1):
        coupling = energy_angle * (0.3 + 0.7 * clamp(agent.coherence, 0.0, 1.0)) / (i + 2)
        circuit.cp(coupling, i, i + 1)

    circuit.barrier(label="agente_fisico")
    circuit.measure(range(bit_count), range(bit_count))
    return circuit


def measure_physical_influence_with_qiskit(agent: ExternalAgent, cycle_size: int) -> int:
    QuantumCircuit, transpile, backend = load_qiskit()
    bit_count = max(1, math.ceil(math.log2(cycle_size)))
    circuit = build_physical_perturbation_circuit(QuantumCircuit, agent, bit_count)
    compiled = transpile(circuit, backend)
    result = backend.run(compiled, shots=2048).result()
    measured_bits = max(result.get_counts(), key=result.get_counts().get)

    # Qiskit entrega el bit clasico 0 al extremo derecho de la cadena medida.
    measured_bits = measured_bits.replace(" ", "")[::-1]
    return int(measured_bits, 2) % cycle_size


def build_restoration_circuit(QuantumCircuit, restored_event_signature: int, agent: ExternalAgent, bit_count: int):
    circuit = QuantumCircuit(bit_count, bit_count)
    raw_bits = format(restored_event_signature, f"0{REGISTER_BITS}b")
    signature_bits = raw_bits[-bit_count:]
    coupling_matrix = event_coupling_matrix(agent, HISTORY)
    energy_angle = normalized_energy_angle(agent)
    observer_angle = observer_phase(agent)

    for index, bit in enumerate(signature_bits):
        if bit == "1":
            circuit.x(index)

    for index in range(bit_count):
        circuit.ry(energy_angle / (index + 1), index)
        circuit.rz(observer_angle * (index + 1) / bit_count, index)

    for i in range(bit_count):
        for j in range(i + 1, bit_count):
            phase = coupling_matrix[i][j]
            circuit.cp(phase, i, j)

    qft_gate = QFTGate(num_qubits=bit_count)
    circuit.append(qft_gate, range(bit_count))

    circuit.barrier(label="indice_restaurado")
    circuit.measure(range(bit_count), range(bit_count))
    return circuit

#*#

# ==========================================
# DECODIFICADOR TEMPORAL
# ==========================================

TEMPORAL_CODES = {
    0: "estado estable",
    1: "eco del pasado",
    2: "recuerdo restaurado",
    3: "bifurcacion temporal",
    4: "linea alternativa",
    5: "salto cronologico",
    6: "paradoja estable",
    7: "convergencia de ciclos",
    8: "memoria persistente",
    9: "evento repetido",
    10: "interferencia temporal",
    11: "reconstruccion historica",
    12: "rama secundaria",
    13: "horizonte temporal",
    14: "sincronizacion cuantica",
    15: "restauracion completa"
}

def decode_temporal_state(value: int) -> str:
    return TEMPORAL_CODES.get(
        value % 16,
        "estado desconocido"
    )

def measure_restoration_distribution(
    restored_index: int,
    agent: ExternalAgent,
    cycle_size: int,
    shots: int = 1024,
    verbose: bool = True,
):
    QuantumCircuit, transpile, backend = load_qiskit()

    bit_count = max(1, math.ceil(math.log2(cycle_size)))

    event_signature = text_signature(HISTORY[restored_index])
    circuit = build_restoration_circuit(QuantumCircuit, event_signature, agent, bit_count)

    compiled = transpile(circuit, backend)
    result = backend.run(compiled, shots=shots).result()
    counts = result.get_counts()

    probabilities: dict[int, float] = {}
    total = sum(counts.values())
    for bits, freq in counts.items():
        state_bits = bits.replace(" ", "")[::-1]
        probabilities[int(state_bits, 2)] = freq / total

    if verbose:
        print("\nDistribucion de estados:")
        print(counts)
        measured_bits = max(counts, key=counts.get).replace(" ", "")[::-1]
        print(f"Bits dominantes: {measured_bits}")
        branches = create_branches(counts)
        print("\nRamas temporales detectadas:")
        for branch in branches:
            print(f"Estado {branch['state']} -> {branch['probability']:.2%}")
    else:
        branches = create_branches(counts)

    return probabilities, branches


def measure_restoration_with_qiskit(restored_index: int, agent: ExternalAgent, cycle_size: int):
    probabilities, branches = measure_restoration_distribution(restored_index, agent, cycle_size)
    measured_restored = max(probabilities, key=probabilities.get)
    return measured_restored, branches


def restoration_probability(
    restored_index: int,
    agent: ExternalAgent,
    cycle_size: int,
    target_state: int,
    shots: int = 1024,
    repeats: int = 1,
) -> float:
    probabilities_sum = 0.0
    for _ in range(max(1, repeats)):
        probabilities, _ = measure_restoration_distribution(
            restored_index,
            agent,
            cycle_size,
            shots=shots,
            verbose=False,
        )
        probabilities_sum += probabilities.get(target_state, 0.0)
    return probabilities_sum / max(1, repeats)


def fit_probability_power_law(
    samples: list[tuple[float, float, float]],
    epsilon: float = 1e-6,
) -> dict[str, float]:
    values = np.array([
        [1.0, math.log(v + epsilon), math.log(c + epsilon)]
        for v, c, _ in samples
    ])
    targets = np.log(np.array([p + epsilon for _, _, p in samples]))
    coeffs, *_ = np.linalg.lstsq(values, targets, rcond=None)
    log_a, b, c = coeffs
    predictions = np.exp(values @ coeffs)
    ss_res = np.sum((np.exp(targets) - predictions) ** 2)
    ss_tot = np.sum((np.exp(targets) - np.mean(np.exp(targets))) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "A": math.exp(log_a),
        "B": b,
        "C": c,
        "r2": r2,
    }


def make_probability_surface(
    velocities: list[float],
    coherences: list[float],
    target_state: int,
    shots: int = 1024,
    repeats: int = 1,
) -> list[tuple[float, float, float]]:
    results = []
    cycle_size = len(HISTORY)
    for v in velocities:
        for c in coherences:
            agent = ExternalAgent(
                name="observador",
                entry_time=0,
                mass_kg=70.0,
                velocity_fraction_c=v,
                coherence=c,
            )
            physical_influence = measure_physical_influence_with_qiskit(agent, cycle_size)
            effective_time = round(relativistic_time(agent, CURRENT_TIME)) + agent.entry_time
            effective_jump = round(relativistic_time(agent, FUTURE_JUMP)) + physical_influence
            restored = restoration_index(effective_time, effective_jump, cycle_size)
            prob = restoration_probability(
                restored,
                agent,
                cycle_size,
                target_state,
                shots=shots,
                repeats=repeats,
            )
            results.append((v, c, prob))
    return results


def print_probability_model(model: dict[str, float], target_state: int) -> None:
    print("\nEcuacion empírica ajustada:")
    print(
        f"P(estado {target_state}) = {model['A']:.4g} * v^{model['B']:.4g} * coherencia^{model['C']:.4g}"
    )
    print(f"R^2 aproximado = {model['r2']:.4f}")


def save_probability_surface_csv(samples: list[tuple[float, float, float]], csv_path: Path) -> Path:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["velocity_fraction_c", "coherence", "probability"])
        for v, c, p in samples:
            writer.writerow([f"{v:.6f}", f"{c:.6f}", f"{p:.6f}"])
    return csv_path

def save_measurement(bits, value, interpretation):

    with open(
        "timeline.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            bits,
            value,
            interpretation
        ])

def agent_signature(agent_name: str) -> int:
    return sum(agent_name.encode("utf-8"))


def text_signature(text: str) -> int:
    return sum(text.encode("utf-8")) % (2**REGISTER_BITS)


def create_external_agent() -> ExternalAgent:
    # Si la entrada no es interactiva (por ejemplo ejecuciones automatizadas),
    # usa los valores por defecto para no bloquear la ejecucion.
    if os.environ.get("SKIP_PROMPT") or not (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()):
        return ExternalAgent(
            name="observador",
            entry_time=0,
            mass_kg=70.0,
            velocity_fraction_c=0.01,
            coherence=0.75,
        )

    print("Ingreso de agente externo")
    name = read_text("Nombre del agente", "observador")
    entry_time = read_int("Tiempo de entrada", 0)
    mass_kg = read_float("Masa del agente en kg", 70.0)
    velocity_fraction_c = read_float("Velocidad como fraccion de c", 0.01)
    coherence = read_float("Coherencia cuantica 0..1", 0.75)
    print()
    return ExternalAgent(
        name=name,
        entry_time=entry_time,
        mass_kg=max(0.0, mass_kg),
        velocity_fraction_c=clamp(velocity_fraction_c, 0.0, 0.999999),
        coherence=clamp(coherence, 0.0, 1.0),
    )

def create_branches(counts):
    total = sum(counts.values())
    branches = [
        {
            "state": state,
            "probability": freq / total,
        }
        for state, freq in counts.items()
        if freq > 0
    ]
    branches.sort(key=lambda branch: branch["probability"], reverse=True)
    return [branch for branch in branches if branch["probability"] > 0.10]


def cycle_result_to_row(result: CycleResult) -> dict[str, str | int | float]:
    top_branch = result.branches[0] if result.branches else {"state": "-", "probability": 0.0}
    branch_list = "; ".join(
        f"{branch['state']}:{branch['probability']:.4f}"
        for branch in result.branches
    )
    return {
        "time": result.t,
        "jump": result.k,
        "effective_time": result.effective_t,
        "effective_jump": result.effective_k,
        "cycle_size": result.n,
        "agent_name": result.agent.name,
        "agent_entry_time": result.agent.entry_time,
        "agent_mass_kg": result.agent.mass_kg,
        "agent_velocity_fraction_c": result.agent.velocity_fraction_c,
        "agent_coherence": result.agent.coherence,
        "physical_influence": result.physical_influence,
        "kinetic_energy_j": result.kinetic_energy,
        "gravitational_radius_m": result.gravitational_radius,
        "restored_index": result.restored_index,
        "restored_event": HISTORY[result.restored_index],
        "measured_restored_index": result.measured_restored_index,
        "measured_restored_event": HISTORY[result.measured_restored_index],
        "past_index": result.past_index,
        "present_index": result.present_index,
        "future_index": result.future_index,
        "memory_units": result.memory_units,
        "horizon_area_m2": result.horizon_area,
        "horizon_entropy_j_per_k": result.horizon_entropy,
        "top_branch_state": top_branch["state"],
        "top_branch_probability": top_branch["probability"],
        "branch_list": branch_list,
    }


def save_cycle_result_to_csv(result: CycleResult, csv_path: Path) -> Path:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_NAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(cycle_result_to_row(result))
    return csv_path


def run_velocity_sweep(count: int, output_path: Path) -> Path:
    count = max(1, count)
    velocities = [i / (count - 1) * 0.99 for i in range(count)] if count > 1 else [0.0]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "velocity_fraction_c",
            "restored_index",
            "restored_event",
            "measured_restored_index",
            "measured_restored_event",
            "top_branch_state",
            "top_branch_probability",
            "physical_influence",
            "effective_time",
            "effective_jump",
        ])
        for velocity in velocities:
            agent = ExternalAgent(
                name="observador",
                entry_time=0,
                mass_kg=70.0,
                velocity_fraction_c=velocity,
                coherence=0.75,
            )
            result = run_time_cycle(CURRENT_TIME, FUTURE_JUMP, HISTORY, agent)
            top_branch = result.branches[0] if result.branches else {"state": "-", "probability": 0.0}
            writer.writerow([
                f"{velocity:.6f}",
                result.restored_index,
                HISTORY[result.restored_index],
                result.measured_restored_index,
                HISTORY[result.measured_restored_index],
                top_branch["state"],
                f"{top_branch['probability']:.6f}",
                result.physical_influence,
                result.effective_t,
                result.effective_k,
            ])
    return output_path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Simulacion de restauracion de estados en un espacio temporal discreto"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Guardar el resultado de la corrida en un archivo CSV.",
    )
    parser.add_argument(
        "--csv-file",
        type=Path,
        default=DEFAULT_RESULT_CSV,
        help="Ruta de salida del CSV para el resultado individual.",
    )
    parser.add_argument(
        "--velocity-sweep",
        action="store_true",
        help="Ejecutar un barrido de velocidades y guardar los resultados en CSV.",
    )
    parser.add_argument(
        "--sweep-count",
        type=int,
        default=50,
        help="Cantidad de puntos en el barrido de velocidad.",
    )
    parser.add_argument(
        "--sweep-csv-file",
        type=Path,
        default=DEFAULT_SWEEP_CSV,
        help="Ruta de salida del CSV para el barrido de velocidad.",
    )
    parser.add_argument(
        "--probability-sweep",
        action="store_true",
        help="Ejecutar un barrido de probabilidad para un estado objetivo.",
    )
    parser.add_argument(
        "--target-state",
        type=int,
        default=7,
        help="Indice del estado objetivo para el barrido de probabilidades.",
    )
    parser.add_argument(
        "--probability-sweep-count",
        type=int,
        default=50,
        help="Número de valores de velocidad y coherencia a muestrear en cada dimensión.",
    )
    parser.add_argument(
        "--probability-sweep-shots",
        type=int,
        default=1024,
        help="Numero de disparos qiskit por medición de restauracion.",
    )
    parser.add_argument(
        "--probability-sweep-repeats",
        type=int,
        default=1,
        help="Repeticiones para promediar la probabilidad empírica en cada par (v, coherencia).",
    )
    parser.add_argument(
        "--probability-sweep-csv",
        type=Path,
        default=Path(__file__).with_name("probability_surface.csv"),
        help="Ruta de salida para el CSV de la superficie de probabilidad.",
    )
    return parser.parse_args(argv)


def branch_tree_svg(branches: list[dict[str, float]], x: int, y: int) -> str:
    if not branches:
        return f'<text x="{x}" y="{y}" class="small">Sin ramas temporales relevantes</text>'

    lines = [
        f'<text x="{x}" y="{y}" class="small">Presente</text>',
        f'<text x="{x + 12}" y="{y + 20}" class="small">│</text>',
    ]
    for index, branch in enumerate(branches[:5]):
        prefix = "└──" if index == len(branches[:5]) - 1 else "├──"
        line_y = y + 40 + index * 22
        lines.append(
            f'<text x="{x + 8}" y="{line_y}" class="small">{escape(prefix)} Rama {escape(branch["state"])} ({branch["probability"]:.2%})</text>'
        )
    return "\n".join(lines)

def read_text(prompt: str, default: str) -> str:
    try:
        value = input(f"{prompt} [{default}]: ").strip()
    except EOFError:
        return default
    return value or default


def read_int(prompt: str, default: int) -> int:
    while True:
        try:
            value = input(f"{prompt} [{default}]: ").strip()
        except EOFError:
            return default

        if not value:
            return default

        try:
            return int(value)
        except ValueError:
            print("  Ingresa un numero entero.")


def read_float(prompt: str, default: float) -> float:
    while True:
        try:
            value = input(f"{prompt} [{default}]: ").strip()
        except EOFError:
            return default

        if not value:
            return default

        try:
            return float(value)
        except ValueError:
            print("  Ingresa un numero.")


def apply_external_agent(
    time: int, jump: int, agent: ExternalAgent, physical_influence: int
) -> tuple[int, int]:
    return time + agent.entry_time, jump + physical_influence


def mark_agent_in_history(history: list[str], index: int, agent: ExternalAgent) -> list[str]:
    marked_history = history.copy()
    marked_history[index] = f"{history[index]} | agente externo: {agent.name}"
    return marked_history


def run_time_cycle(
    time: int, jump: int, history: list[str], agent: ExternalAgent
) -> CycleResult:
    cycle_size = len(history)
    physical_influence = measure_physical_influence_with_qiskit(agent, cycle_size)
    dilated_time = round(relativistic_time(agent, time))
    dilated_jump = round(relativistic_time(agent, jump))
    effective_time = dilated_time + agent.entry_time
    effective_jump = dilated_jump + physical_influence
    restored = restoration_index(effective_time, effective_jump, cycle_size)
    measured_restored, branches = measure_restoration_with_qiskit(restored, agent, cycle_size)
    memory_units = measured_restored + 1
    area = horizon_area_from_restoration(measured_restored)

    return CycleResult(
        t=time,
        k=jump,
        effective_t=effective_time,
        effective_k=effective_jump,
        n=cycle_size,
        agent=agent,
        physical_influence=physical_influence,
        kinetic_energy=kinetic_energy(agent),
        gravitational_radius=gravitational_radius(agent),
        past_index=past_index(effective_time, cycle_size),
        present_index=present_index(effective_time, cycle_size),
        future_index=future_index(effective_time, effective_jump, cycle_size),
        restored_index=restored,
        measured_restored_index=measured_restored,
        branches=branches,
        memory_units=memory_units,
        horizon_area=area,
        horizon_entropy=horizon_entropy(area),
    )


def print_state(label: str, index: int, history: list[str]) -> None:
    print(f"{label:<13}: H[{index}] = {history[index]}")


def create_timeline_register(result: CycleResult, history: list[str]) -> TimelineRegister:
    return TimelineRegister(
        past=text_signature(history[result.past_index]),
        present=text_signature(history[result.present_index]),
        future=text_signature(history[result.future_index]),
    )


def cycle_timeline_register(register: TimelineRegister) -> TimelineRegister:
    return TimelineRegister(
        past=register.future,
        present=register.past,
        future=register.present,
    )


def print_timeline_register(title: str, register: TimelineRegister) -> None:
    print(title)
    print(f"  pasado  : {register.past:02d} ({register.past:0{REGISTER_BITS}b})")
    print(f"  presente: {register.present:02d} ({register.present:0{REGISTER_BITS}b})")
    print(f"  futuro  : {register.future:02d} ({register.future:0{REGISTER_BITS}b})")


def role_names_for_index(index: int, result: CycleResult) -> list[str]:
    roles = []
    if index == result.past_index:
        roles.append("pasado")
    if index == result.present_index:
        roles.append("presente")
    if index == result.future_index:
        roles.append("futuro")
    if index == result.restored_index:
        roles.append("restaurado")
    return roles


def node_color(index: int, result: CycleResult) -> str:
    if index == result.restored_index:
        return "#d946ef"
    if index == result.present_index:
        return "#2563eb"
    if index == result.future_index:
        return "#16a34a"
    if index == result.past_index:
        return "#f97316"
    return "#64748b"


def point_on_circle(index: int, total: int, center_x: int, center_y: int, radius: int):
    angle = (2 * math.pi * index / total) - (math.pi / 2)
    return center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)


def write_timeline_graph(
    result: CycleResult, history: list[str], graph_path: Path
) -> Path:
    width = 980
    height = 760
    center_x = 490
    center_y = 310
    radius = 210
    entropy_width = int(360 * result.memory_units / result.n)

    nodes = []
    for index, event in enumerate(history):
        x, y = point_on_circle(index, result.n, center_x, center_y, radius)
        color = node_color(index, result)
        roles = role_names_for_index(index, result)
        role_text = ", ".join(roles) if roles else "evento"
        label = f"H[{index}]"
        short_event = event.split("|")[0].strip()
        nodes.append(
            f"""
            <g>
              <circle cx="{x:.2f}" cy="{y:.2f}" r="25" fill="{color}" />
              <text x="{x:.2f}" y="{y + 5:.2f}" text-anchor="middle"
                    class="node-label">{escape(label)}</text>
              <text x="{x:.2f}" y="{y + 44:.2f}" text-anchor="middle"
                    class="small">{escape(role_text)}</text>
              <text x="{x:.2f}" y="{y + 64:.2f}" text-anchor="middle"
                    class="tiny">{escape(short_event[:28])}</text>
            </g>
            """
        )

    entry_index = cycle_index(result.effective_t, result.n)
    entry_x, entry_y = point_on_circle(entry_index, result.n, center_x, center_y, radius)
    restored_x, restored_y = point_on_circle(
        result.restored_index, result.n, center_x, center_y, radius
    )

    branch_area = branch_tree_svg(result.branches, 640, 628)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img"
     aria-label="Grafico de simulacion temporal">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6"
            orient="auto" markerUnits="strokeWidth">
      <path d="M2,2 L10,6 L2,10 Z" fill="#111827" />
    </marker>
    <style>
      .title {{ font: 700 28px Arial, sans-serif; fill: #111827; }}
      .subtitle {{ font: 16px Arial, sans-serif; fill: #334155; }}
      .body {{ font: 15px Arial, sans-serif; fill: #1f2937; }}
      .small {{ font: 13px Arial, sans-serif; fill: #334155; }}
      .tiny {{ font: 11px Arial, sans-serif; fill: #475569; }}
      .node-label {{ font: 700 14px Arial, sans-serif; fill: white; }}
      .formula {{ font: 16px Consolas, monospace; fill: #111827; }}
    </style>
  </defs>

  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="40" y="48" class="title">Simulacion de restauracion de estados discretos</text>
  <text x="40" y="78" class="subtitle">
    Evolucion cuantica y observador relativista en un espacio temporal discreto
  </text>

  <circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none"
          stroke="#cbd5e1" stroke-width="4" stroke-dasharray="8 10" />
  <path d="M {entry_x:.2f} {entry_y:.2f} L {restored_x:.2f} {restored_y:.2f}"
        stroke="#111827" stroke-width="3" fill="none" marker-end="url(#arrow)" />
  <circle cx="{entry_x:.2f}" cy="{entry_y:.2f}" r="35" fill="none"
          stroke="#ef4444" stroke-width="4" />
  <text x="{entry_x:.2f}" y="{entry_y - 42:.2f}" text-anchor="middle"
        class="small">entrada: {escape(result.agent.name)}</text>

  {''.join(nodes)}

  <rect x="40" y="560" width="900" height="150" rx="8" fill="#ffffff"
        stroke="#e2e8f0" />
  <text x="64" y="596" class="formula">
    restauracion_E = H[(t' + k') mod N] = H[({result.effective_t} + {result.effective_k}) mod {result.n}]
  </text>
  <text x="64" y="626" class="body">
    indice restaurado: {result.restored_index} | influencia fisica: {result.physical_influence} | memoria m: {result.memory_units}
  </text>
  <text x="64" y="656" class="formula">
    S = k_B c^3 A / (4 G hbar), A = 4 m l_p^2
  </text>
  <rect x="64" y="676" width="360" height="18" rx="9" fill="#e2e8f0" />
  <rect x="64" y="676" width="{entropy_width}" height="18" rx="9" fill="#d946ef" />
  <text x="444" y="691" class="small">
    S = {result.horizon_entropy:.6e} J/K
  </text>
  <g class="branch-tree">
    {branch_area}
  </g>
</svg>
"""
    graph_path.write_text(svg, encoding="utf-8")
    return graph_path



def main() -> int:
    args = parse_args()

    if args.velocity_sweep:
        sweep_path = run_velocity_sweep(args.sweep_count, args.sweep_csv_file)
        print(f"Barrido de velocidad guardado en: {sweep_path}")
        return 0

    if args.probability_sweep:
        velocities = [i / (args.probability_sweep_count - 1) * 0.99 for i in range(args.probability_sweep_count)] if args.probability_sweep_count > 1 else [0.0]
        coherences = [i / (args.probability_sweep_count - 1) for i in range(args.probability_sweep_count)] if args.probability_sweep_count > 1 else [0.0]
        samples = make_probability_surface(
            velocities,
            coherences,
            args.target_state,
            shots=args.probability_sweep_shots,
            repeats=args.probability_sweep_repeats,
        )
        csv_path = save_probability_surface_csv(samples, args.probability_sweep_csv)
        print(f"Barrido de probabilidad guardado en: {csv_path}")
        model = fit_probability_power_law(samples)
        print_probability_model(model, args.target_state)
        return 0

    agent = create_external_agent()

    try:
        result = run_time_cycle(CURRENT_TIME, FUTURE_JUMP, HISTORY, agent)
    except RuntimeError as exc:
        print(exc)
        return 1

    if args.csv:
        csv_path = save_cycle_result_to_csv(result, args.csv_file)
        print(f"Resultado individual guardado en CSV: {csv_path}")

    simulated_history = mark_agent_in_history(
        HISTORY, result.restored_index, result.agent
    )
    graph_path = write_timeline_graph(result, simulated_history, GRAPH_PATH)

    print("Simulacion de restauracion de estados en un espacio temporal discreto")
    print(
        '"Modelo computacional de restauracion de estados en un espacio temporal discreto, '
        'con evolucion cuantica y observadores relativistas"'
    )
    print()
    print(f"N = {result.n}")
    print(f"t base = {result.t}")
    print(f"k base = {result.k}")
    print(f"agente externo = {result.agent.name}")
    print(f"entrada del agente = {result.agent.entry_time}")
    print(f"masa del agente = {result.agent.mass_kg:.6g} kg")
    print(f"velocidad del agente = {result.agent.velocity_fraction_c:.6g} c")
    print(f"coherencia cuantica = {result.agent.coherence:.6g}")
    gamma = lorentz_factor(result.agent.velocity_fraction_c)
    print(f"energia cinetica = {result.kinetic_energy:.6e} J")
    print(f"radio gravitacional = {result.gravitational_radius:.6e} m")
    print(f"dilatacion temporal gamma = {gamma:.6f}")
    print(f"influencia fisica medida = {result.physical_influence}")
    print(f"t' = {result.effective_t}")
    print(f"k' = {result.effective_k}")
    print()
    print("Ecuaciones:")
    print("  E                  = (nombre, entrada, masa, velocidad, coherencia)")
    print("  gamma              = 1 / sqrt(1 - beta^2)")
    print("  energia            = (gamma - 1) m c^2")
    print("  radio_grav         = 2 G m / c^2")
    print("  influencia_fisica  = medicion_cuantica(energia, radio_grav, coherencia)")
    print(f"  t'                 = gamma * {result.t} + {result.agent.entry_time}")
    print(f"  k'                 = gamma * {result.k} + {result.physical_influence}")
    print(f"  presente(t')       = H[{result.effective_t} mod {result.n}]")
    print(f"  pasado(t')         = H[({result.effective_t} - 1) mod {result.n}]")
    print(
        f"  futuro(t', k')     = H[({result.effective_t} + "
        f"{result.effective_k}) mod {result.n}]"
    )
    print(
        f"  restauracion_E     = H[({result.effective_t} + "
        f"{result.effective_k}) mod {result.n}]"
    )
    print("  S                  = k_B c^3 A / (4 G hbar)")
    print("  A                  = 4 m l_p^2")
    print("  m                  = indice_restaurado + 1")
    print()
    print("Estados:")
    print_state("pasado", result.past_index, simulated_history)
    print_state("presente", result.present_index, simulated_history)
    print_state("futuro", result.future_index, simulated_history)
    print_state("restaurado", result.restored_index, simulated_history)
    print()

    initial_register = create_timeline_register(result, simulated_history)
    cycled_register = cycle_timeline_register(initial_register)
    print_timeline_register("Linea temporal inicial:", initial_register)
    print()
    print_timeline_register("Linea temporal despues del ciclo:", cycled_register)
    print()

    print(
        "Qiskit midio el indice restaurado como "
        f"{result.measured_restored_index}, que corresponde a: "
        f"{simulated_history[result.measured_restored_index]}"
    )
    temporal_message = decode_temporal_state(
    result.measured_restored_index)

    print(
    f"Interpretacion temporal: {temporal_message}"
    )
    print()
    print("Horizonte de restauracion:")
    print(f"  unidades de memoria m = {result.memory_units}")
    print(f"  area A                = {result.horizon_area:.6e} m^2")
    print(f"  entropia S            = {result.horizon_entropy:.6e} J/K")
    print(
        "  lectura simbolica     = la memoria restaurada queda codificada "
        "como entropia del horizonte"
    )
    print()
    print(f"Grafico generado en: {graph_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
