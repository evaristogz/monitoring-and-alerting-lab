# Monitoreo y alertas | Laboratorio práctico

Este proyecto despliega una aplicación FastAPI con un stack completo de monitoreo usando Prometheus y Grafana en un cluster de Minikube.

Resultado de la Práctica Final del módulo "Liberando productos - SRE" de la XII Edición Bootcamp DevOps & Cloud Computing Full Stack de KeepCoding.

Se trata de una práctica con unos hitos marcados que tienen como objetivo aprender a implementar herramientas de monitoring (Prometheus + Grafana) junto a alertas mediante AlertManager y Slack (webhook) de una aplicación simple FastApi desplegada en Kubernetes.

[![⭐ Conecta conmigo en LinkedIn](https://img.shields.io/badge/⭐_Conecta_conmigo_en-LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&labelColor=000000)](https://www.linkedin.com/in/evaristogz/)

---

[🔽 Ir directamente a 🚀 Cómo desplegar el laboratorio 🔽](#cómo-desplegar-el-laboratorio)

## Índice de contenidos

- [Requisitos previos](#requisitos-previos)
- [🚀 Cómo desplegar el laboratorio](#cómo-desplegar-el-laboratorio)
  - [1. Preparar el entorno de Kubernetes](#1-preparar-el-entorno-de-kubernetes)
  - [2. Configurar repositorios de Helm](#2-configurar-repositorios-de-helm)
  - [3. Desplegar el stack de monitoreo](#3-desplegar-el-stack-de-monitoreo)
  - [4. Acceder a Grafana](#4-acceder-a-grafana)
  - [5. Desplegar la aplicación FastAPI](#5-desplegar-la-aplicación-fastapi)
  - [6. Acceder a la aplicación FastAPI](#6-acceder-a-la-aplicación-fastapi)
- [Verificación del despliegue](#verificación-del-despliegue)
- [CI/CD y Release de nuevas versiones](#cicd-y-release-de-nuevas-versiones)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Limpieza del entorno](#limpieza-del-entorno)

## Requisitos previos

- Minikube
- Helm
- kubectl
- **Canal de Slack configurado** con webhook para alertas

Ejecutado en Windows 11 con Docker Desktop 4.50.0, Docker Engine v28.5.1,Helm v3.18.6, minikube v1.36.0 y kubectl v1.34.0

## 🚀 Cómo desplegar el laboratorio

### 0. Configuración inicial de secretos

Antes de empezar, debes configurar tu webhook de Slack. Esto solo deberás hacerlo una única vez.

0.1. **Crear canal en Slack** para alertas (por ejemplo: *#tu-nombre-prometheus-alarms*)

0.2. **Configurar webhook entrante** en Slack:
   - Ir a tu workspace de Slack → Apps → Incoming Webhooks
   - Crear nuevo webhook para tu canal de alertas
   - Copiar la URL generada

0.3. **Crear archivo de secretos**:
   ```bash
   cp secret-values.yaml.template secret-values.yaml
   ```

0.4. **Editar `secret-values.yaml`** con tus valores:
   ```yaml
   alertmanager:
     config:
       global:
         slack_api_url: 'https://hooks.slack.com/services/TU_WORKSPACE/TU_CANAL/TU_TOKEN'
       slack_channel: '#tu-canal-prometheus-alarms'
   ```

### 1. Preparar el entorno de Kubernetes

Iniciar Minikube:

```bash
minikube start
```

Habilitar el servidor de métricas:

```bash
minikube addons enable metrics-server
```

### 2. Configurar repositorios de Helm

Agregar el repositorio de la comunidad de Prometheus:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### 3. Desplegar el stack de monitoreo

Crear el namespace para monitoring:

```bash
kubectl create namespace monitoring
```

Aplicar el ConfigMap del dashboard de Grafana:

```bash
kubectl apply -f grafana/fastapi-dashboard-configmap.yaml -n monitoring
```

Instalar el stack kube-prometheus (Prometheus + Grafana + AlertManager):

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values helm/monitoring-values.yaml \
  --values secret-values.yaml
```

Se utilizan dos archivos de valores:
- *helm/monitoring-values.yaml*: Configuración general (se puede versionar)
- *secret-values.yaml*: Valores sensibles como webhooks de Slack (NO versionar)

### 4. Acceder a Grafana

Obtener la contraseña de admin de Grafana:

```bash
kubectl --namespace monitoring get secrets prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo
```

Configurar port-forward para acceder a Grafana:

```bash
export POD_NAME=$(kubectl --namespace monitoring get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=prometheus" -oname)
kubectl --namespace monitoring port-forward $POD_NAME 3000
```

**Acceso a Grafana:**
- URL: http://localhost:3000
- Usuario: `admin`
- Contraseña: La obtenida en el comando anterior

Una vez dentro de Grafana, puedes revisar el dashboard "fastapi-monitoring-dashboard".

### 5. Desplegar la aplicación FastAPI

Crear el namespace para la aplicación:

```bash
kubectl create namespace fastapi-server
```

Desplegar la aplicación usando Helm:

```bash
helm install fastapi-server ./chart \
  --namespace fastapi-server \
  --set image.repository=ghcr.io/evaristogz/fastapi-server \
  --set image.tag=0.0.2 \
  --set metrics.enabled=true \
  --set grafana.dashboard.enabled=false
```

### 6. Acceder a la aplicación FastAPI

Configurar port-forward para acceder a la aplicación:

```bash
export POD_NAME=$(kubectl get pods --namespace fastapi-server -l "app.kubernetes.io/name=fastapi-server,app.kubernetes.io/instance=fastapi-server" -o jsonpath="{.items[0].metadata.name}")

export CONTAINER_PORT=$(kubectl get pod --namespace fastapi-server $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")

kubectl --namespace fastapi-server port-forward $POD_NAME 8080:$CONTAINER_PORT
```

**Acceso a la aplicación:**
- URL: http://127.0.0.1:8080

## Verificación del despliegue

### Comprobar que todos los pods están ejecutándose

```bash
# Verificar pods de monitoring
kubectl get pods -n monitoring

# Verificar pods de la aplicación
kubectl get pods -n fastapi-server
```

### Comprobar servicios

```bash
# Servicios de monitoring
kubectl get svc -n monitoring

# Servicios de la aplicación
kubectl get svc -n fastapi-server
```

### Probar endpoints de la aplicación

```bash
# Endpoint principal
curl http://localhost:8080/

# Endpoint de health
curl http://localhost:8080/health

# Métricas de Prometheus (puerto 8000 dentro del contenedor)
curl http://localhost:8080/metrics
```

## CI/CD y Release de nuevas versiones

### Workflow automático de GitHub Actions

Este proyecto incluye workflows de GitHub Actions que se ejecutan automáticamente:

1. **Test Workflow**: Se ejecuta en cada push y pull request para ejecutar tests
2. **Release & Build Workflow**: Se ejecuta al crear tags para generar releases automáticamente

### Crear una nueva release

Para crear una nueva versión de la aplicación y generar automáticamente la imagen Docker:

1. **Hacer commit de cambios**:
   ```bash
   git add .
   git commit -m "Test"
   git push origin main
   ```

2. **Crear y hacer push de tag de versión**:
   ```bash
   # Crear tag con versión semántica (ejemplo: v0.0.3)
   git tag v0.0.3
   git push origin v0.0.3
   ```

3. **El workflow automáticamente**:
   - Ejecutará los tests
   - Construirá la imagen Docker
   - La subirá a GitHub Container Registry (`ghcr.io`)

### Desplegar la nueva versión

Una vez que el workflow termine, actualizar el despliegue:

```bash
helm upgrade fastapi-server ./chart \
  --namespace fastapi-server \
  --set image.repository=ghcr.io/evaristogz/fastapi-server \
  --set image.tag=0.0.3 \
  --set metrics.enabled=true \
  --set grafana.dashboard.enabled=false
```

Puedes verificar las imágenes disponibles en [GitHub Packages](https://github.com/evaristogz/fastapi-server/pkgs/container/fastapi-server)

### Manejo de secretos

- **`secret-values.yaml`**: Contiene únicamente valores sensibles (webhook de Slack, API keys).
- **`helm/monitoring-values.yaml`**: Configuración general que puede ser versionada sin problemas.
- Se recomienda añadir `secret-values.yaml` al `.gitignore` para evitar exponer credenciales.

## Limpieza del entorno

Para limpiar el entorno completamente:

```bash
# Eliminar la aplicación FastAPI
helm uninstall fastapi-server -n fastapi-server
kubectl delete namespace fastapi-server

# Eliminar el stack de monitoring
helm uninstall prometheus -n monitoring
kubectl delete namespace monitoring

# Detener Minikube (opcional)
minikube stop
```

Recuerda que puede haber imágenes de Docker en tu GitHub Container Registry o en tu Docker Hub.