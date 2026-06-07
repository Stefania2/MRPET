# Laboratorio de Estados Discretos

Aplicacion web conceptual para estudiar historias como sistemas discretos de estados.
El proyecto ya no se plantea como una maquina del tiempo fisica, sino como un modelo
computacional inspirado en amplitudes complejas, evolucion de fase y analisis espectral.

## Enfoque investigable

El objetivo defendible es:

```text
Modelo computacional de memoria ciclica y bifurcacion probabilistica usando estados
discretos, fases complejas y analisis espectral inspirado en QFT.
```

El modelo combina:

- estados base `|H_i>` para representar eventos simbolicos
- tiempo logico `t`, desplazamiento `k` y ciclo `H[(t + k) mod N]`
- amplitudes complejas `alpha_i` normalizadas
- evolucion de fase mediante un operador analogico `U(theta)`
- probabilidades `P(H_i) = |alpha_i|^2`
- analisis QFT/manual para detectar recurrencias y frecuencia dominante
- metricas medibles: entropia de probabilidad, distancia entre estados y concentracion espectral

Las variables como masa, velocidad y coherencia se tratan como parametros analogicos de
perturbacion. No validan afirmaciones fisicas sobre relatividad, horizontes reales ni viajes
temporales.

## Hipotesis de trabajo

Una historia discreta puede representarse como:

```text
|psi_t> = sum_i alpha_i(t) |H_i>
|psi_t+1> = U(theta) |psi_t>
P(H_i) = |alpha_i|^2
F(k) = QFT(|psi_t+1>)
```

El prototipo permite observar:

- que ramas logicas concentran mayor probabilidad
- cuanto cambia el estado despues de aplicar fases
- que tan concentrado esta el espectro dominante
- cuanta incertidumbre tiene la distribucion de eventos
- si hay recurrencias detectables bajo perturbaciones controladas

## Web app en GitHub Pages

La version publica esta en la carpeta `docs/` y corre completamente en el navegador:

- `docs/index.html`
- `docs/main.js`
- `docs/styles.css`

No necesita Python, Flask ni Qiskit para funcionar en GitHub Pages.

### Despliegue

El workflow `.github/workflows/gh-pages.yml` publica automaticamente `docs/` en GitHub Pages cuando haces push a `main`.

En GitHub, revisa:

1. `Settings`
2. `Pages`
3. `Build and deployment`
4. Seleccionar `GitHub Actions`

Luego haz push a `main`. La action generara la URL publica del sitio.

## Uso de la web

Abre la pagina y ajusta:

- nombre del agente
- indice logico base `t`
- desplazamiento base `k`
- entrada logica del agente
- masa analogica
- velocidad analogica como fraccion de `c`
- coherencia de fase entre `0` y `1`

La app calcula:

```text
perturbacion = f(masa, velocidad, coherencia, entrada)
t' = t + entrada
k' = k + perturbacion
indice_recurrente = H[(t' + k') mod N]
entropia_P = -sum(P_i log2 P_i)
distancia_estado = ||psi_evolucionado - psi_inicial||
concentracion_espectral = max(|F_k|^2) / sum(|F_k|^2)
```

Tambien muestra:

- estados logicos de pasado, presente, proyeccion y recurrencia
- grafico circular del ciclo logico
- registro binario antes y despues del ciclo
- probabilidades de eventos
- ramas logicas dominantes
- descarga CSV

## Probar localmente

En Windows puedes usar:

```powershell
.\run_web_app.bat
```

Eso abre:

```text
http://127.0.0.1:5000/
```

Tambien puedes correr la version estatica manualmente:

```bash
cd docs
python -m http.server 8000
```

Abre:

```text
http://127.0.0.1:8000/
```

## App Flask opcional

El repositorio conserva una app Flask:

- `app.py`
- `templates/index.html`
- `requirements.txt`
- `Procfile`

Para correrla localmente:

```bash
python -m pip install -r requirements.txt
python app.py
```

Luego abre:

```text
http://127.0.0.1:5000/
```

## Archivos principales

- `docs/`: web app estatica para GitHub Pages.
- `app.py`: web app Flask opcional con metricas exportables.
- `templates/index.html`: interfaz Flask.
- `dewscifrar.py`: simulacion de consola con Qiskit cuando esta disponible.
- `.github/workflows/gh-pages.yml`: despliegue de GitHub Pages.
- `.github/workflows/deploy-heroku.yml`: despliegue opcional a Heroku.

## Limites cientificos

Este proyecto no demuestra viaje temporal ni prediccion fisica de futuros. Su valor esta en
formalizar una intuicion como sistema discreto medible: estados, operadores, distribuciones,
recurrencias y sensibilidad a perturbaciones.

## Errores comunes

Si corres `dewscifrar copy.py` y aparece:

```text
ModuleNotFoundError: No module named 'numpy'
```

estas ejecutando un script de consola avanzado, no la web app. Para la web app usa:

```powershell
.\run_web_app.bat
```

Si de todos modos quieres ejecutar `dewscifrar copy.py`, instala sus dependencias con el mismo Python:

```powershell
python -m pip install -r requirements-console.txt
```

Luego ejecuta:

```powershell
python "dewscifrar copy.py"
```
