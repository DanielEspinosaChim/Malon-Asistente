FROM python:3.11-slim

WORKDIR /app

# 1. Instalamos dependencias del sistema (Casi nunca cambian, se queda en cache)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 2. COPIAMOS SOLO EL REQUIREMENTS (Esta es la clave)
# Docker revisa si este archivo cambió. Si es igual, usa la cache para el siguiente paso.
COPY requirements.txt .

# 3. INSTALAMOS LIBRERÍAS
# Solo se ejecutará si el paso anterior (el requirements) cambió.
RUN pip install --no-cache-dir -r requirements.txt

# 4. COPIAMOS EL RESTO DEL CÓDIGO
# Esto se hace al final para que, si cambias el app.py o el Agente.py, 
# NO se tengan que volver a instalar las librerías.
COPY . .

# 5. Pasos finales
RUN mkdir -p temp_audio
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]