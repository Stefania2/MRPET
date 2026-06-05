# Simulador Temporal

Aplicacion web conceptual para explorar una linea temporal ciclica con un agente externo. El modelo combina:

- ciclo temporal `H[(t + k) mod N]`
- parametros fisicos simplificados del agente: masa, velocidad y coherencia
- energia cinetica relativista y radio gravitacional
- entropia de horizonte `S = k_B c^3 A / (4 G hbar)`
- probabilidades de eventos y grafico circular de la simulacion
- linea temporal inicial y linea temporal despues del ciclo en formato binario

Esta no es una maquina del tiempo fisica. Es una simulacion matematica y visual para experimentar con ciclos, perturbaciones y restauracion simbolica.

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
- tiempo base `t`
- salto base `k`
- tiempo de entrada
- masa en kg
- velocidad como fraccion de `c`
- coherencia cuantica entre `0` y `1`

La app calcula:

```text
gamma = 1 / sqrt(1 - beta^2)
energia = (gamma - 1) m c^2
radio_grav = 2 G m / c^2
influencia_fisica = f(energia, radio_grav, coherencia)
t' = t + entrada
k' = k + influencia_fisica
restauracion_E = H[(t' + k') mod N]
```

Tambien muestra:

- estados de pasado, presente, futuro y restaurado
- grafico circular del ciclo temporal
- linea temporal inicial y despues del ciclo
- probabilidades de eventos
- futuros mas probables
- descarga CSV

## Probar localmente la version estatica

En Windows puedes usar:

```powershell
.\run_web_app.bat
```

Eso abre:

```text
http://127.0.0.1:8787/
```

Tambien puedes correrla manualmente:

```bash
cd docs
python -m http.server 8000
```

Abre:

```text
http://127.0.0.1:8000/
```

## App Flask opcional

El repositorio tambien conserva una app Flask:

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

- `dewscifrar.py`: simulacion de consola con Qiskit cuando esta disponible.
- `docs/`: web app estatica para GitHub Pages.
- `app.py`: web app Flask opcional.
- `.github/workflows/gh-pages.yml`: despliegue de GitHub Pages.
- `.github/workflows/deploy-heroku.yml`: despliegue opcional a Heroku.

## Errores comunes

Si corres `dewscifrar copy.py` y aparece:

```text
ModuleNotFoundError: No module named 'numpy'
```

estas ejecutando un script de consola avanzado, no la web app estatica. Para la web app usa:

```powershell
.\run_web_app.bat
```

Si de todos modos quieres ejecutar `dewscifrar copy.py`, instala sus dependencias con el mismo Python que estas usando:

```powershell
python -m pip install -r requirements-console.txt
```

Luego ejecuta:

```powershell
python "dewscifrar copy.py"
```
