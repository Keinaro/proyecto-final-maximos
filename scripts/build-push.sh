#!/usr/bin/env bash
# Construye (linux/amd64), etiqueta con la ruta completa de Artifact Registry y sube las imágenes (C1, C2).
#
# Uso:
#   REGION=us-central1 PROJECT_ID=mi-proyecto scripts/build-push.sh                 # las 3 apps en v1.0.0 + db
#   REGION=... PROJECT_ID=... TAG=v1.1.0 scripts/build-push.sh pacientes           # solo pacientes en v1.1.0 (F3)
#
# Requiere haber ejecutado una vez: gcloud auth configure-docker REGION-docker.pkg.dev
set -euo pipefail

: "${REGION:?Definir REGION, ej. us-central1}"
: "${PROJECT_ID:?Definir PROJECT_ID}"
TAG="${TAG:-v1.0.0}"
REG="${REGION}-docker.pkg.dev/${PROJECT_ID}/vet-repo"

cd "$(dirname "$0")/.."

apps=("$@")
mirror_db=false
if [ ${#apps[@]} -eq 0 ]; then
  apps=(pacientes citas frontend)
  mirror_db=true
fi

for app in "${apps[@]}"; do
  if [ "$app" = "db" ]; then
    mirror_db=true
    continue
  fi
  echo "==> ${REG}/${app}:${TAG}"
  docker build --platform linux/amd64 \
    --build-arg APP_VERSION="${TAG#v}" \
    -t "${REG}/${app}:${TAG}" "services/${app}"
  docker push "${REG}/${app}:${TAG}"
done

# Copia de postgres:16 al repo: C3 no permite imágenes de Docker Hub en los manifiestos.
if [ "$mirror_db" = true ]; then
  echo "==> ${REG}/db:16"
  docker pull --platform linux/amd64 postgres:16
  docker tag postgres:16 "${REG}/db:16"
  docker push "${REG}/db:16"
fi

gcloud artifacts docker images list "${REG}" --include-tags
