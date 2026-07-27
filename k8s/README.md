## Kubernetes — MoreAI Deployment

### Local testing with minikube
```bash
# install minikube
minikube start

# apply manifests
kubectl apply -k k8s/base/

# check pods
kubectl get pods -n moreai

# port forward for local testing
kubectl port-forward svc/moreai-service 8000:80 -n moreai

# check logs
kubectl logs -l app=moreai-api -n moreai --follow

# scale manually
kubectl scale deployment moreai-api --replicas=3 -n moreai

# check HPA
kubectl get hpa -n moreai
```

### Production deployment
```bash
# apply production overlay
kubectl apply -k k8s/overlays/production/

# rolling update
kubectl set image deployment/moreai-api \
  moreai-api=YOUR_ECR_URL/moreai:NEW_TAG \
  -n moreai

# rollback if needed
kubectl rollout undo deployment/moreai-api -n moreai
```