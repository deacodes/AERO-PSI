FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 AERO_PSI_CLOUD_CACHE=/tmp/aeropsi-runtime
WORKDIR /app
COPY requirements.txt requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt && useradd --uid 10001 --create-home app
COPY aero_psi/ ./aero_psi/
COPY frontend/ ./frontend/
COPY mappings/ ./mappings/
COPY deploy/start.sh ./deploy/start.sh
USER app
EXPOSE 8080
CMD ["sh", "deploy/start.sh"]
