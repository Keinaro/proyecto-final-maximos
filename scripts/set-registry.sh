#!/usr/bin/env bash
# Reemplaza los marcadores REGION y PROJECT_ID de las rutas de imagen en k8s/ por los valores reales.
# Se ejecuta una sola vez, cuando P5 entregue el proyecto, y el resultado se commitea.
#
# Uso: REGION=us-central1 PROJECT_ID=mi-proyecto scripts/set-registry.sh
set -euo pipefail

: "${REGION:?Definir REGION, ej. us-central1}"
: "${PROJECT_ID:?Definir PROJECT_ID}"

cd "$(dirname "$0")/.."

grep -rl 'REGION-docker.pkg.dev/PROJECT_ID/' k8s --include='*.yaml' | while read -r f; do
  sed -i "s#REGION-docker.pkg.dev/PROJECT_ID/#${REGION}-docker.pkg.dev/${PROJECT_ID}/#g" "$f"
  echo "actualizado: $f"
done

grep -rn 'image:' k8s --include='*.yaml'
