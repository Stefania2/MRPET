FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto que usa Flask (por defecto 5000, pero luego mapearemos a 4001)
EXPOSE 5000

# Comando para ejecutar la app
CMD ["python", "app.py"]
