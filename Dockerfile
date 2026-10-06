FROM python:3.12-slim

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Bog'liqliklarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini nusxalash
COPY . .

# Ma'lumotlar bazasi saqlanishi uchun data papkasi
RUN mkdir -p /app/data

# Botni ishga tushirish
CMD ["python", "main.py"]
