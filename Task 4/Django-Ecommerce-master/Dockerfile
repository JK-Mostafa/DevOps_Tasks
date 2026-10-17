FROM python:latest

WORKDIR /app

RUN apt-get update 

COPY . .

RUN python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
