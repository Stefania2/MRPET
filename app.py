from __future__ import annotations

import csv
import cmath
import io
import math
from dataclasses import dataclass
from html import escape

from flask import Flask, Response, render_template, request, url_for

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import QFT
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except Exception:
    QISKIT_AVAILABLE = False
    QuantumCircuit = None
    transpile = None
    QFT = None
    AerSimulator = None

app = Flask(__name__)

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
BOLTZMANN_CONSTANT = 1.380649e-23
LIGHT_SPEED = 299_792_458
GRAVITATIONAL_CONSTANT = 6.67430e-11
REDUCED_PLANCK_CONSTANT = 1.054571817e-34
PLANCK_LENGTH = 1.616255e-35
PLANCK_ENERGY = 1.9561e9

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
    15: "restauracion completa",
}


@dataclass(frozen=True)
class ExternalAgent:
    name: str
    entry_time: int
    mass_kg: float
    velocity_fraction_c: float
    coherence: float


@dataclass(frozen=True)
class SimulationResult:
    agent: ExternalAgent
    current_time: int
    future_jump: int
    cycle_size: int
    effective_time: int
    effective_jump: int
    cycle_period: int
    dominant_frequency: int
    event_probabilities: list[dict[str, float]]
    future_branches: list[dict[str, float]]
    qft_spectrum: list[dict[str, float]]
    horizon_area: float
    horizon_entropy: float
    timeline: list[str]
    measured_state: str
    qiskit_used: bool


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


def event_text_signature(text: str) -> int:
    return sum(text.encode("utf-8"))


def event_weight(event: str) -> float:
    return float((event_text_signature(event) % 16) + 1)


def event_state_vector(history: list[str], agent: ExternalAgent) -> list[complex]:
    mass_scale = clamp(math.log1p(agent.mass_kg) / 4.0, 0.0, 10.0)
    velocity_scale = clamp(agent.velocity_fraction_c, 0.0, 0.999999)
    coherence = clamp(agent.coherence, 0.0, 1.0)

    amplitudes: list[complex] = []
    for index, event in enumerate(history):
        signature = event_text_signature(event)
        magnitude = 0.15 + 0.85 * (((signature >> (index % 5)) & 0x1F) + 1) / 32.0
        event_mass_factor = 1.0 + 0.18 * mass_scale * (((signature >> 2) & 0x07) + 1) / 8.0
        event_vel_factor = 1.0 + 0.24 * velocity_scale * (((signature >> 4) & 0x03) + 1) / 4.0
        entry_factor = 1.0 + 0.10 * abs(agent.entry_time) / 10.0 * (((signature >> 1) & 0x03) + 1) / 4.0
        magnitude *= event_mass_factor * event_vel_factor * entry_factor
        magnitude *= 0.5 + 0.5 * coherence
        phase = (signature % 17) / 17.0 * 2 * math.pi
        phase += agent.entry_time * 0.25
        phase += mass_scale * 0.20 * (((signature >> 3) & 0x03) + 1) / 4.0
        phase += velocity_scale * 2 * math.pi
        phase *= 0.4 + 0.6 * coherence
        amplitudes.append(cmath.rect(magnitude, phase))

    norm = math.sqrt(sum(abs(amplitude) ** 2 for amplitude in amplitudes))
    if norm == 0:
        return [complex(1 / math.sqrt(len(history)), 0) for _ in history]

    return [amplitude / norm for amplitude in amplitudes]


def event_energies(agent: ExternalAgent) -> list[float]:
    mass_scale = max(0.0, agent.mass_kg / 50.0)
    velocity_scale = clamp(agent.velocity_fraction_c, 0.0, 0.999999)
    energies: list[float] = []
    for event in HISTORY:
        signature = event_text_signature(event)
        local = ((signature % 64) + 20) * (1.0 + 0.3 * mass_scale)
        energies.append(local * (1.0 + 0.8 * velocity_scale))
    return energies


def phase_evolution(psi: list[complex], energies: list[float], agent: ExternalAgent) -> list[complex]:
    phase_scale = 0.2 + 0.8 * clamp(agent.coherence, 0.0, 1.0)
    dt = 1.0 + agent.entry_time * 0.2
    return [
        amplitude * cmath.exp(-1j * energy * phase_scale * dt * 0.02)
        for amplitude, energy in zip(psi, energies)
    ]


def qft_transform(psi: list[complex]) -> list[complex]:
    n = len(psi)
    factor = 1 / math.sqrt(n)
    return [
        factor * sum(psi[j] * cmath.exp(2j * math.pi * j * k / n) for j in range(n))
        for k in range(n)
    ]


def detect_cycle_period(spectrum: list[complex]) -> tuple[int, int]:
    n = len(spectrum)
    magnitudes = [abs(amplitude) for amplitude in spectrum]
    if not any(magnitudes):
        return n, 0
    dominant = max(range(n), key=lambda i: magnitudes[i])
    period = n // (dominant or 1)
    return period, dominant


def probabilities_from_state(psi: list[complex]) -> list[float]:
    raw = [abs(amplitude) ** 2 for amplitude in psi]
    total = sum(raw)
    if total == 0:
        return [1.0 / len(raw) for _ in raw]
    return [value / total for value in raw]


def top_future_branches(probabilities: list[float], history: list[str], count: int = 3) -> list[dict[str, float]]:
    indexed = sorted(
        enumerate(probabilities),
        key=lambda item: item[1],
        reverse=True,
    )[:count]
    return [
        {
            "event": history[index],
            "probability": probability,
        }
        for index, probability in indexed
    ]


def qft_spectrum_summary(spectrum: list[complex]) -> list[dict[str, float]]:
    return [
        {
            "frequency": index,
            "magnitude": abs(amplitude),
        }
        for index, amplitude in enumerate(spectrum)
    ]


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

    angles: list[float] = []
    for index in range(bit_count):
        phase = (
            energy_phase / (index + 1)
            + gravity_phase * (index + 1) / bit_count
            + entry_phase
            + decoherence_phase
        )
        angles.append((phase % (2 * math.pi)) * coherence)
    return angles


def build_cycle_operator(agent: ExternalAgent, history: list[str]) -> tuple[list[complex], list[float]]:
    psi0 = event_state_vector(history, agent)
    energies = event_energies(agent)
    evolved = phase_evolution(psi0, energies, agent)
    return evolved, energies


def qft_analysis(psi: list[complex]) -> tuple[list[dict[str, float]], int, int]:
    spectrum = qft_transform(psi)
    period, dominant_frequency = detect_cycle_period(spectrum)
    return qft_spectrum_summary(spectrum), period, dominant_frequency


def simulate_future_branches(psi: list[complex], history: list[str]) -> list[dict[str, float]]:
    probabilities = probabilities_from_state(psi)
    return top_future_branches(probabilities, history)


def decode_temporal_state(value: int) -> str:
    return TEMPORAL_CODES.get(value % 16, "estado desconocido")


def run_simulation(agent: ExternalAgent, current_time: int, future_jump: int) -> SimulationResult:
    cycle_size = len(HISTORY)
    effective_time = current_time + agent.entry_time
    effective_jump = future_jump + int(agent.coherence * 10)
    evolved_state, energies = build_cycle_operator(agent, HISTORY)
    spectrum, cycle_period, dominant_frequency = qft_analysis(evolved_state)
    future_branches = simulate_future_branches(evolved_state, HISTORY)
    event_probabilities = [
        {"event": event, "probability": prob}
        for event, prob in zip(HISTORY, probabilities_from_state(evolved_state))
    ]
    memory_units = cycle_period + 1
    area = horizon_area_from_restoration(cycle_period)
    return SimulationResult(
        agent=agent,
        current_time=current_time,
        future_jump=future_jump,
        cycle_size=cycle_size,
        effective_time=effective_time,
        effective_jump=effective_jump,
        cycle_period=cycle_period,
        dominant_frequency=dominant_frequency,
        event_probabilities=event_probabilities,
        future_branches=future_branches,
        qft_spectrum=spectrum,
        horizon_area=area,
        horizon_entropy=horizon_entropy(area),
        timeline=HISTORY,
        measured_state=decode_temporal_state(dominant_frequency),
        qiskit_used=False,
    )


def simulation_to_csv(result: SimulationResult) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Campo", "Valor"])
    writer.writerow(["Nombre agente", result.agent.name])
    writer.writerow(["Tiempo base", result.current_time])
    writer.writerow(["Salto base", result.future_jump])
    writer.writerow(["Tiempo efectivo", result.effective_time])
    writer.writerow(["Salto efectivo", result.effective_jump])
    writer.writerow(["Periodo detectado (QFT)", result.cycle_period])
    writer.writerow(["Frecuencia dominante", result.dominant_frequency])
    writer.writerow(["Interpretación temporal", result.measured_state])
    writer.writerow(["Área horizonte", f"{result.horizon_area:.6e}"])
    writer.writerow(["Entropía horizonte", f"{result.horizon_entropy:.6e}"])
    writer.writerow(["Qiskit usado", "sí" if result.qiskit_used else "no"])
    writer.writerow([])

    writer.writerow(["Evento", "Probabilidad"])
    for item in result.event_probabilities:
        writer.writerow([item["event"], f"{item['probability']:.6f}"])

    writer.writerow([])
    writer.writerow(["Rama futura", "Probabilidad"])
    for branch in result.future_branches:
        writer.writerow([branch["event"], f"{branch['probability']:.6f}"])

    return output.getvalue()


def parse_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_agent_from_request(form) -> ExternalAgent:
    return ExternalAgent(
        name=escape(form.get("name", "observador")) or "observador",
        entry_time=parse_int(form.get("entry_time"), 0),
        mass_kg=max(0.0, parse_float(form.get("mass_kg"), 70.0)),
        velocity_fraction_c=clamp(parse_float(form.get("velocity_fraction_c"), 0.01), 0.0, 0.999999),
        coherence=clamp(parse_float(form.get("coherence"), 0.75), 0.0, 1.0),
    )


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    agent = ExternalAgent("observador", 0, 70.0, 0.01, 0.75)
    current_time = CURRENT_TIME
    future_jump = FUTURE_JUMP
    if request.method == "POST":
        agent = build_agent_from_request(request.form)
        current_time = parse_int(request.form.get("current_time"), CURRENT_TIME)
        future_jump = parse_int(request.form.get("future_jump"), FUTURE_JUMP)
        result = run_simulation(agent, current_time, future_jump)
    return render_template(
        "index.html",
        result=result,
        agent=agent,
        current_time=current_time,
        future_jump=future_jump,
        qiskit_available=QISKIT_AVAILABLE,
    )


@app.route("/download")
def download_csv():
    name = request.args.get("name", "observador")
    entry_time = parse_int(request.args.get("entry_time"), 0)
    mass_kg = max(0.0, parse_float(request.args.get("mass_kg"), 70.0))
    velocity_fraction_c = clamp(parse_float(request.args.get("velocity_fraction_c"), 0.01), 0.0, 0.999999)
    coherence = clamp(parse_float(request.args.get("coherence"), 0.75), 0.0, 1.0)
    current_time = parse_int(request.args.get("current_time"), CURRENT_TIME)
    future_jump = parse_int(request.args.get("future_jump"), FUTURE_JUMP)

    agent = ExternalAgent(name, entry_time, mass_kg, velocity_fraction_c, coherence)
    result = run_simulation(agent, current_time, future_jump)
    csv_data = simulation_to_csv(result)
    response = Response(csv_data, mimetype="text/csv")
    response.headers.set("Content-Disposition", "attachment", filename="dewscifrar_simulation.csv")
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
