#!/usr/bin/env bash
# Despliega todo en el orden correcto. Sirve para recrear el entorno tras un terraform apply
# (por ejemplo si los nodos spot son reclamados). Las operaciones F1-F4 de la defensa se hacen a mano.
#
# Uso:
#   scripts/deploy.sh            # aplica todo
#   scripts/deploy.sh delete     # borra todo lo de k8s/ (antes del terraform destroy)
set -euo pipefail

NS=maximos
cd "$(dirname "$0")/.."

if [ "${1:-}" = "delete" ]; then
  kubectl delete -f k8s/ -R --ignore-not-found
  exit 0
fi

if grep -rq 'PROJECT_ID/' k8s --include='*.yaml'; then
  echo "Faltan reemplazar REGION/PROJECT_ID en k8s/: ejecutar scripts/set-registry.sh" >&2
  exit 1
fi

kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/config/configmap.yaml

if ! kubectl get secret db-secret -n "$NS" >/dev/null 2>&1; then
  if [ -f k8s/config/secret.yaml ]; then
    kubectl apply -f k8s/config/secret.yaml
  else
    echo "No existe db-secret. Crearlo con:" >&2
    echo "  kubectl create secret generic db-secret -n $NS --from-literal=DB_USER=... --from-literal=DB_PASSWORD=..." >&2
    exit 1
  fi
fi

kubectl apply -f k8s/db/
kubectl rollout status deploy/db -n "$NS" --timeout=180s

kubectl apply -f k8s/pacientes/ -f k8s/citas/ -f k8s/frontend/
for d in pacientes citas frontend; do
  kubectl rollout status "deploy/$d" -n "$NS" --timeout=180s
done

kubectl get all -n "$NS"
echo "IP pública (puede tardar 1-3 min): kubectl get svc frontend -n $NS -w"
