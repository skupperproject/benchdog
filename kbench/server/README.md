# Kbench server

~~~
kubectl create namespace benchdog-server
kubectl config set-context --current --namespace benchdog-server
kubectl create -f strimzi.yaml
kubectl create -f cluster.yaml -f topic.yaml
~~~

~~~
kubectl delete -f strimzi.yaml
~~~
