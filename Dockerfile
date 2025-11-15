# 1) Milyen alap image-ből indulunk?
FROM python:3.11-slim

# 2) Nem szeretnénk, hogy Python buffereljen (jobb logolás)
ENV PYTHONUNBUFFERED=1

# 3) Mappa a konténeren belül, ahol az app lesz
WORKDIR /app

# 4) requirements bemásolása a konténerbe
COPY requirements.txt .

# 5) pip csomagok telepítése
RUN pip install --no-cache-dir -r requirements.txt

# 6) a teljes projekt bemásolása a konténerbe
COPY . .

# 7) A port, amin az app fut a konténeren belül
EXPOSE 8000

# 8) Parancs, ami elindul, amikor a konténer fut
# Ha FastAPI-s appod main.py-ben van, és a FastAPI objektum app a neve:
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
