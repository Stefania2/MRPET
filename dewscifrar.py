"""
Maquina del tiempo simbolica usando el algoritmo ciclico t mod N.

Base conceptual:
    "lo que es, ya ha sido, y lo que sera, ya fue;
     y Dios restaura lo que ha pasado"

Modelo matematico ciclico:
    H = [x0, x1, x2, ..., xN-1]

    presente(t)        = H[t mod N]
    pasado(t)          = H[(t - 1) mod N]
    futuro(t, k)       = H[(t + k) mod N]
    restauracion(t, k) = H[(t + k) mod N]

Agente externo:
    E = (nombre, entrada, masa, velocidad, coherencia)

    gamma = 1 / sqrt(1 - beta^2)
    energia = (gamma - 1) m c^2
    radio_gravitacional = 2 G m / c^2
    influencia_fisica = medicion_cuantica(energia, radio_gravitacional, coherencia)

    t' = t + entrada
    k' = k + influencia_fisica
    restauracion_E(t, k) = H[(t' + k') mod N]

Modelo de entropia del horizonte:
    S = k_B c^3 A / (4 G hbar)

    A = 4 m l_p^2
    l_p^2 = G hbar / c^3
    m = indice_restaurado + 1

    Entonces:
    S = k_B m

La restauracion ocurre porque cualquier tiempo cae de nuevo dentro de H
cuando se aplica el operador modulo N. La entropia S mide cuanta memoria
temporal se restaura en el horizonte simbolico.

Instalacion si hace falta:
    python -m pip install qiskit qiskit-aer

Ejecucion:
    python dewscifrar.py
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path


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


def build_physical_perturbation_circuit(QuantumCircuit, agent: ExternalAgent, bit_count: int):
    circuit = QuantumCircuit(bit_count, bit_count)

    for index, angle in enumerate(perturbation_angles(agent, bit_count)):
        circuit.ry(angle, index)

    circuit.barrier(label="agente_fisico")
    circuit.measure(range(bit_count), range(bit_count))
    return circuit


def measure_physical_influence_with_qiskit(agent: ExternalAgent, cycle_size: int) -> int:
    QuantumCircuit, transpile, backend = load_qiskit()
    bit_count = max(1, math.ceil(math.log2(cycle_size)))
    circuit = build_physical_perturbation_circuit(QuantumCircuit, agent, bit_count)
    compiled = transpile(circuit, backend)
    result = backend.run(compiled, shots=256).result()
    measured_bits = max(result.get_counts(), key=result.get_counts().get)

    # Qiskit entrega el bit clasico 0 al extremo derecho de la cadena medida.
    measured_bits = measured_bits.replace(" ", "")[::-1]
    return int(measured_bits, 2) % cycle_size


def build_restoration_circuit(QuantumCircuit, restored_index: int, bit_count: int):
    circuit = QuantumCircuit(bit_count, bit_count)
    restored_bits = f"{restored_index:0{bit_count}b}"

    for index, bit in enumerate(restored_bits):
        if bit == "1":
            circuit.x(index)

    circuit.barrier(label="indice_restaurado")
    circuit.measure(range(bit_count), range(bit_count))
    return circuit


def measure_restoration_with_qiskit(restored_index: int, cycle_size: int) -> int:
    QuantumCircuit, transpile, backend = load_qiskit()
    bit_count = max(1, math.ceil(math.log2(cycle_size)))
    circuit = build_restoration_circuit(QuantumCircuit, restored_index, bit_count)
    compiled = transpile(circuit, backend)
    result = backend.run(compiled, shots=1).result()
    measured_bits = max(result.get_counts(), key=result.get_counts().get)

    # Qiskit entrega el bit clasico 0 al extremo derecho de la cadena medida.
    measured_bits = measured_bits.replace(" ", "")[::-1]
    return int(measured_bits, 2)


def agent_signature(agent_name: str) -> int:
    return sum(agent_name.encode("utf-8"))


def text_signature(text: str) -> int:
    return sum(text.encode("utf-8")) % (2**REGISTER_BITS)


def create_external_agent() -> ExternalAgent:
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
    effective_time, effective_jump = apply_external_agent(
        time, jump, agent, physical_influence
    )
    restored = restoration_index(effective_time, effective_jump, cycle_size)
    measured_restored = measure_restoration_with_qiskit(restored, cycle_size)
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
  <text x="40" y="48" class="title">Simulacion de maquina del tiempo</text>
  <text x="40" y="78" class="subtitle">
    Ciclo temporal con agente externo y entropia del horizonte
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
</svg>
"""
    graph_path.write_text(svg, encoding="utf-8")
    return graph_path


def main() -> int:
    agent = create_external_agent()

    try:
        result = run_time_cycle(CURRENT_TIME, FUTURE_JUMP, HISTORY, agent)
    except RuntimeError as exc:
        print(exc)
        return 1

    simulated_history = mark_agent_in_history(
        HISTORY, result.restored_index, result.agent
    )
    graph_path = write_timeline_graph(result, simulated_history, GRAPH_PATH)

    print("Maquina del tiempo: algoritmo ciclico t mod N")
    print(
        '"lo que es, ya ha sido, y lo que sera, ya fue; '
        'y Dios restaura lo que ha pasado"'
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
    print(f"energia cinetica = {result.kinetic_energy:.6e} J")
    print(f"radio gravitacional = {result.gravitational_radius:.6e} m")
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
    print(f"  t'                 = {result.t} + {result.agent.entry_time}")
    print(f"  k'                 = {result.k} + {result.physical_influence}")
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
