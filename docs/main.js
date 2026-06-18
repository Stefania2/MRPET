const HISTORY = [
  "la semilla fue sembrada",
  "la raiz busco agua",
  "el tallo encontro luz",
  "la flor se abrio",
  "el fruto guardo memoria",
  "la semilla cayo otra vez",
  "la tierra recordo el ciclo",
  "el comienzo regreso",
];

const TEMPORAL_CODES = [
  "estado estable",
  "eco del pasado",
  "recuerdo recurrente",
  "bifurcacion logica",
  "linea alternativa",
  "salto de indice",
  "paradoja estable",
  "convergencia de ciclos",
];

const BOLTZMANN_CONSTANT = 1.380649e-23;
const LIGHT_SPEED = 299792458;
const GRAVITATIONAL_CONSTANT = 6.6743e-11;
const REDUCED_PLANCK_CONSTANT = 1.054571817e-34;
const PLANCK_LENGTH = 1.616255e-35;
const PLANCK_ENERGY = 1.9561e9;
const REGISTER_BITS = 6;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function mod(value, size) {
  return ((value % size) + size) % size;
}

function complex(re, im) {
  return { re, im };
}

function complexAdd(a, b) {
  return complex(a.re + b.re, a.im + b.im);
}

function complexMul(a, b) {
  return complex(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
}

function complexScale(a, scale) {
  return complex(a.re * scale, a.im * scale);
}

function complexRect(radius, angle) {
  return complex(radius * Math.cos(angle), radius * Math.sin(angle));
}

function complexAbs(a) {
  return Math.hypot(a.re, a.im);
}

function complexExp(angle) {
  return complex(Math.cos(angle), Math.sin(angle));
}

function textSignature(text) {
  return Array.from(text).reduce((sum, char) => sum + char.charCodeAt(0), 0);
}

function sixBitSignature(text) {
  return mod(textSignature(text), 2 ** REGISTER_BITS);
}

function lorentzFactor(beta) {
  const safeBeta = clamp(Math.abs(beta), 0, 0.999999);
  return 1 / Math.sqrt(1 - safeBeta ** 2);
}

function kineticEnergy(agent) {
  return (lorentzFactor(agent.velocityFractionC) - 1) * agent.massKg * LIGHT_SPEED ** 2;
}

function gravitationalRadius(agent) {
  return (2 * GRAVITATIONAL_CONSTANT * agent.massKg) / LIGHT_SPEED ** 2;
}

function planckArea() {
  return (GRAVITATIONAL_CONSTANT * REDUCED_PLANCK_CONSTANT) / LIGHT_SPEED ** 3;
}

function horizonAreaFromRestoration(restoredIndex) {
  return 4 * (restoredIndex + 1) * planckArea();
}

function horizonEntropy(area) {
  return (BOLTZMANN_CONSTANT * LIGHT_SPEED ** 3 * area) /
    (4 * GRAVITATIONAL_CONSTANT * REDUCED_PLANCK_CONSTANT);
}

function deterministicPhysicalInfluence(agent, cycleSize) {
  const energyRatio = Math.max(0, kineticEnergy(agent)) / PLANCK_ENERGY;
  const gravityRatio = Math.max(0, gravitationalRadius(agent)) / PLANCK_LENGTH;
  const coherence = clamp(agent.coherence, 0, 1);
  const namePhase = mod(textSignature(agent.name), 97) / 97;
  const phase =
    Math.log1p(energyRatio) * 1.7 +
    Math.log1p(gravityRatio) * 0.9 +
    Math.abs(agent.entryTime) * 0.31 +
    coherence * Math.PI +
    namePhase * Math.PI * 2;
  return mod(Math.floor(Math.abs(Math.sin(phase)) * 1000000), cycleSize);
}

function eventStateVector(history, agent) {
  const massScale = clamp(Math.log1p(agent.massKg) / 4, 0, 10);
  const velocityScale = clamp(agent.velocityFractionC, 0, 0.999999);
  const coherence = clamp(agent.coherence, 0, 1);

  const amplitudes = history.map((event, index) => {
    const signature = textSignature(event);
    let magnitude = 0.15 + 0.85 * ((((signature >> (index % 5)) & 0x1f) + 1) / 32);
    magnitude *= 1 + 0.18 * massScale * ((((signature >> 2) & 0x07) + 1) / 8);
    magnitude *= 1 + 0.24 * velocityScale * ((((signature >> 4) & 0x03) + 1) / 4);
    magnitude *= 1 + 0.1 * Math.abs(agent.entryTime) / 10 * ((((signature >> 1) & 0x03) + 1) / 4);
    magnitude *= 0.5 + 0.5 * coherence;

    let phase = ((signature % 17) / 17) * 2 * Math.PI;
    phase += agent.entryTime * 0.25;
    phase += massScale * 0.2 * ((((signature >> 3) & 0x03) + 1) / 4);
    phase += velocityScale * 2 * Math.PI;
    phase *= 0.4 + 0.6 * coherence;
    return complexRect(magnitude, phase);
  });

  const norm = Math.sqrt(amplitudes.reduce((sum, amplitude) => sum + complexAbs(amplitude) ** 2, 0));
  return amplitudes.map((amplitude) => complexScale(amplitude, norm === 0 ? 1 : 1 / norm));
}

function eventEnergies(agent) {
  const massScale = Math.max(0, agent.massKg / 50);
  const velocityScale = clamp(agent.velocityFractionC, 0, 0.999999);
  return HISTORY.map((event) => {
    const signature = textSignature(event);
    return ((signature % 64) + 20) * (1 + 0.3 * massScale) * (1 + 0.8 * velocityScale);
  });
}

function phaseEvolution(psi, energies, agent) {
  const phaseScale = 0.2 + 0.8 * clamp(agent.coherence, 0, 1);
  const dt = 1 + agent.entryTime * 0.2;
  return psi.map((amplitude, index) => {
    const phase = -energies[index] * phaseScale * dt * 0.02;
    return complexMul(amplitude, complexExp(phase));
  });
}

function qftTransform(psi) {
  const n = psi.length;
  const factor = 1 / Math.sqrt(n);
  return Array.from({ length: n }, (_, k) => {
    const sum = psi.reduce((acc, psiJ, j) => {
      const rotation = complexExp((2 * Math.PI * j * k) / n);
      return complexAdd(acc, complexMul(psiJ, rotation));
    }, complex(0, 0));
    return complexScale(sum, factor);
  });
}

function probabilitiesFromState(psi) {
  const raw = psi.map((amplitude) => complexAbs(amplitude) ** 2);
  const total = raw.reduce((sum, value) => sum + value, 0);
  return raw.map((value) => (total === 0 ? 1 / raw.length : value / total));
}

function shannonEntropy(probabilities) {
  return -probabilities
    .filter((probability) => probability > 0)
    .reduce((sum, probability) => sum + probability * Math.log2(probability), 0);
}

function stateDistance(before, after) {
  return Math.sqrt(after.reduce((sum, amplitude, index) => {
    const delta = complex(amplitude.re - before[index].re, amplitude.im - before[index].im);
    return sum + complexAbs(delta) ** 2;
  }, 0));
}

function spectralConcentration(spectrum) {
  const powers = spectrum.map((amplitude) => complexAbs(amplitude) ** 2);
  const total = powers.reduce((sum, value) => sum + value, 0);
  return total === 0 ? 0 : Math.max(...powers) / total;
}

function detectCyclePeriod(spectrum) {
  const magnitudes = spectrum.map((amplitude) => complexAbs(amplitude));
  const dominantFrequency = magnitudes.reduce(
    (best, value, index) => (value > magnitudes[best] ? index : best),
    0,
  );
  const period = Math.max(1, Math.round(spectrum.length / (dominantFrequency || 1)));
  return { period, dominantFrequency };
}

function buildTimelineRegister(result) {
  const past = sixBitSignature(result.timeline[result.pastIndex]);
  const present = sixBitSignature(result.timeline[result.presentIndex]);
  const future = sixBitSignature(result.timeline[result.futureIndex]);
  return {
    initial: { past, present, future },
    cycled: { past: future, present: past, future: present },
  };
}

function runSimulation(agent, currentTime, futureJump) {
  const cycleSize = HISTORY.length;
  const physicalInfluence = deterministicPhysicalInfluence(agent, cycleSize);
  const effectiveTime = currentTime + agent.entryTime;
  const effectiveJump = futureJump + physicalInfluence;
  const pastIndex = mod(effectiveTime - 1, cycleSize);
  const presentIndex = mod(effectiveTime, cycleSize);
  const futureIndex = mod(effectiveTime + effectiveJump, cycleSize);
  const restoredIndex = futureIndex;

  const timeline = [...HISTORY];
  timeline[restoredIndex] = `${timeline[restoredIndex]} | agente externo: ${agent.name}`;

  const psi = eventStateVector(HISTORY, agent);
  const evolved = phaseEvolution(psi, eventEnergies(agent), agent);
  const probabilities = probabilitiesFromState(evolved);
  const spectrum = qftTransform(evolved);
  const { period, dominantFrequency } = detectCyclePeriod(spectrum);
  const area = horizonAreaFromRestoration(restoredIndex);
  const timelineRegister = buildTimelineRegister({
    timeline,
    pastIndex,
    presentIndex,
    futureIndex,
  });

  return {
    agent,
    currentTime,
    futureJump,
    cycleSize,
    physicalInfluence,
    effectiveTime,
    effectiveJump,
    pastIndex,
    presentIndex,
    futureIndex,
    restoredIndex,
    period,
    dominantFrequency,
    measuredState: TEMPORAL_CODES[dominantFrequency % TEMPORAL_CODES.length],
    kineticEnergy: kineticEnergy(agent),
    gravitationalRadius: gravitationalRadius(agent),
    horizonArea: area,
    horizonEntropy: horizonEntropy(area),
    probabilityEntropy: shannonEntropy(probabilities),
    stateDistance: stateDistance(psi, evolved),
    spectralConcentration: spectralConcentration(spectrum),
    memoryUnits: restoredIndex + 1,
    timeline,
    timelineRegister,
    eventProbabilities: HISTORY.map((event, index) => ({ event, probability: probabilities[index] })),
    futureBranches: HISTORY.map((event, index) => ({ event, probability: probabilities[index] }))
      .sort((a, b) => b.probability - a.probability)
      .slice(0, 3),
    qftSpectrum: spectrum.map((amplitude, index) => ({ frequency: index, magnitude: complexAbs(amplitude) })),
  };
}

function parseFloatSafe(id, fallback) {
  const value = Number.parseFloat(document.getElementById(id).value);
  return Number.isFinite(value) ? value : fallback;
}

function parseIntSafe(id, fallback) {
  const value = Number.parseInt(document.getElementById(id).value, 10);
  return Number.isFinite(value) ? value : fallback;
}

function buildAgentFromForm() {
  return {
    name: document.getElementById("name").value.trim() || "observador",
    entryTime: parseIntSafe("entry_time", 0),
    massKg: Math.max(0, parseFloatSafe("mass_kg", 70)),
    velocityFractionC: clamp(parseFloatSafe("velocity_fraction_c", 0.01), 0, 0.999999),
    coherence: clamp(parseFloatSafe("coherence", 0.75), 0, 1),
  };
}

function formatBits(value) {
  return value.toString(2).padStart(REGISTER_BITS, "0");
}

function stateLine(label, value) {
  return `<div><span>${label}</span><strong>${value.toString().padStart(2, "0")} (${formatBits(value)})</strong></div>`;
}

function renderTimelineRegister(register) {
  document.getElementById("binary-timeline").innerHTML = `
    <div class="timeline-block">
      <h3>Registro logico inicial</h3>
      ${stateLine("pasado", register.initial.past)}
      ${stateLine("presente", register.initial.present)}
      ${stateLine("proyeccion", register.initial.future)}
    </div>
    <div class="timeline-block">
      <h3>Registro logico despues del ciclo</h3>
      ${stateLine("pasado", register.cycled.past)}
      ${stateLine("presente", register.cycled.present)}
      ${stateLine("proyeccion", register.cycled.future)}
    </div>
  `;
}

function renderResult(result) {
  document.getElementById("result-section").classList.remove("hidden");
  document.getElementById("summary-grid").innerHTML = `
    <article><span>Perturbacion analogica</span><strong>${result.physicalInfluence}</strong></article>
    <article><span>t'</span><strong>${result.effectiveTime}</strong></article>
    <article><span>k'</span><strong>${result.effectiveJump}</strong></article>
    <article><span>Indice recurrente</span><strong>H[${result.restoredIndex}]</strong></article>
    <article><span>Entropia P</span><strong>${result.probabilityEntropy.toFixed(4)} bits</strong></article>
    <article><span>Distancia estado</span><strong>${result.stateDistance.toFixed(4)}</strong></article>
    <article><span>Concentracion espectral</span><strong>${result.spectralConcentration.toFixed(4)}</strong></article>
    <article><span>Estado QFT</span><strong>${result.measuredState}</strong></article>
  `;

  document.getElementById("state-list").innerHTML = `
    <li><span>pasado</span><strong>H[${result.pastIndex}] = ${result.timeline[result.pastIndex]}</strong></li>
    <li><span>presente</span><strong>H[${result.presentIndex}] = ${result.timeline[result.presentIndex]}</strong></li>
    <li><span>proyeccion</span><strong>H[${result.futureIndex}] = ${result.timeline[result.futureIndex]}</strong></li>
    <li><span>recurrencia</span><strong>H[${result.restoredIndex}] = ${result.timeline[result.restoredIndex]}</strong></li>
  `;

  renderTimelineRegister(result.timelineRegister);
  renderProbabilityBars(result);
  renderCycle(result);
  document.getElementById("download-csv").onclick = () => downloadCSV(result);
}

function renderProbabilityBars(result) {
  document.getElementById("probability-list").innerHTML = result.eventProbabilities
    .map((item, index) => {
      const percent = item.probability * 100;
      return `
        <li>
          <div><span>H[${index}] ${item.event}</span><strong>${percent.toFixed(2)}%</strong></div>
          <meter min="0" max="100" value="${percent}"></meter>
        </li>
      `;
    })
    .join("");

  document.getElementById("branch-list").innerHTML = result.futureBranches
    .map((branch) => `<li>${branch.event} -> ${(branch.probability * 100).toFixed(2)}%</li>`)
    .join("");
}

function pointOnCircle(index, total, centerX, centerY, radius) {
  const angle = (2 * Math.PI * index) / total - Math.PI / 2;
  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY + radius * Math.sin(angle),
  };
}

function nodeRole(index, result) {
  const roles = [];
  if (index === result.pastIndex) roles.push("pasado");
  if (index === result.presentIndex) roles.push("presente");
  if (index === result.futureIndex) roles.push("proyeccion");
  if (index === result.restoredIndex) roles.push("recurrencia");
  return roles.join(", ") || "evento";
}

function nodeColor(index, result) {
  if (index === result.restoredIndex) return "#c026d3";
  if (index === result.presentIndex) return "#2563eb";
  if (index === result.futureIndex) return "#16a34a";
  if (index === result.pastIndex) return "#ea580c";
  return "#64748b";
}

function renderCycle(result) {
  const svg = document.getElementById("cycle-svg");
  const centerX = 310;
  const centerY = 250;
  const radius = 170;
  const entry = pointOnCircle(result.presentIndex, result.cycleSize, centerX, centerY, radius);
  const restored = pointOnCircle(result.restoredIndex, result.cycleSize, centerX, centerY, radius);

  const nodes = result.timeline.map((event, index) => {
    const point = pointOnCircle(index, result.cycleSize, centerX, centerY, radius);
    const shortEvent = event.split("|")[0].trim();
    return `
      <g>
        <circle cx="${point.x}" cy="${point.y}" r="25" fill="${nodeColor(index, result)}" filter="url(#node-shadow)"></circle>
        <text x="${point.x}" y="${point.y + 5}" text-anchor="middle" class="node-index">H[${index}]</text>
        <text x="${point.x}" y="${point.y + 43}" text-anchor="middle" class="node-role">${nodeRole(index, result)}</text>
        <text x="${point.x}" y="${point.y + 61}" text-anchor="middle" class="node-event">${shortEvent.slice(0, 24)}</text>
      </g>
    `;
  }).join("");

  svg.innerHTML = `
    <defs>
      <filter id="node-shadow" x="-30%" y="-30%" width="160%" height="160%">
        <feDropShadow dx="0" dy="9" stdDeviation="7" flood-color="#143a8b" flood-opacity="0.18"></feDropShadow>
      </filter>
      <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
        <path d="M2,2 L10,6 L2,10 Z" fill="#111827"></path>
      </marker>
    </defs>
    <circle cx="${centerX}" cy="${centerY}" r="102" fill="#f8fbff" stroke="#e2e8f0" stroke-width="2"></circle>
    <text x="${centerX}" y="${centerY - 10}" text-anchor="middle" class="node-role">periodo QFT</text>
    <text x="${centerX}" y="${centerY + 18}" text-anchor="middle" class="cycle-period">${result.period}</text>
    <circle cx="${centerX}" cy="${centerY}" r="${radius}" fill="none" stroke="#cbd5e1" stroke-width="4" stroke-dasharray="8 10"></circle>
    <path d="M ${entry.x} ${entry.y} L ${restored.x} ${restored.y}" stroke="#111827" stroke-width="3" marker-end="url(#arrow)"></path>
    ${nodes}
  `;
}

function createCSV(result) {
  const rows = [
    ["Campo", "Valor"],
    ["Agente", result.agent.name],
    ["Tiempo base", result.currentTime],
    ["Salto base", result.futureJump],
    ["Tiempo efectivo", result.effectiveTime],
    ["Salto efectivo", result.effectiveJump],
    ["Perturbacion analogica", result.physicalInfluence],
    ["Entropia de probabilidad", result.probabilityEntropy],
    ["Distancia entre estados", result.stateDistance],
    ["Concentracion espectral", result.spectralConcentration],
    [],
    ["Evento", "Probabilidad"],
    ...result.eventProbabilities.map((item) => [item.event, item.probability.toFixed(6)]),
  ];
  return rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
}

function downloadCSV(result) {
  const blob = new Blob([createCSV(result)], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "modelo_estados_discretos.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function init() {
  const form = document.getElementById("sim-form");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const result = runSimulation(
      buildAgentFromForm(),
      parseIntSafe("current_time", 11),
      parseIntSafe("future_jump", 5),
    );
    renderResult(result);
  });

  form.dispatchEvent(new Event("submit"));
}

window.addEventListener("DOMContentLoaded", init);
