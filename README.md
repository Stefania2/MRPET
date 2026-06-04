# Simulador Web de Historias Probabilísticas

Este proyecto crea una aplicación web que modela la evolución de historias como estados cuánticos y aplica análisis de ciclo mediante QFT. El objetivo es explorar futuros alternativos y probabilidades de eventos en lugar de una máquina del tiempo física.

## Qué incluye

- `app.py`: aplicación Flask para ejecutar el algoritmo desde el navegador.
- `templates/index.html`: formulario de entrada, resultados en pantalla y descarga de CSV.
- `requirements.txt`: dependencias necesarias.

## Ejecutar localmente

1. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

2. Inicia la aplicación web:

```bash
python app.py
```

3. Abre un navegador y visita:

```
http://127.0.0.1:5000/
```

### Nota opcional

Si deseas ejecutar circuitos reales con Qiskit, instala también:

```bash
python -m pip install qiskit qiskit-aer
```

## Uso

- Introduce el nombre del agente, parámetros de entrada, masa, velocidad y coherencia.
- Ejecuta la simulación.
- Descarga el CSV de resultados para análisis o reinterpretaciones.

## Nota

Si Qiskit no está disponible en el entorno, la aplicación cae a un modo determinista de respaldo, pero la interfaz seguirá funcionando y permitirá descargar CSV.
