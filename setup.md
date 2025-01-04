
```bash
eval $(minikube docker-env)
```

```bash
docker build -t ingest-app:v1 .
```

# Using BuildKit
It seems that docker comes installed with the legacy builder for some reason.

DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

```bash
sudo apt install docker-buildx
```

```bash

pipenv shell
pipenv lock
pipenv sync
```

# Deploy
```bash
kubectl apply -f ingest-app-deployment.yaml
kubectl apply -f ingest-app-service.yaml
```