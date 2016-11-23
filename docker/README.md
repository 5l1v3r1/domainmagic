Domainmagic docker images for CI builds

The following commands create a docker instance to test/build domainmagic on your local gitlab installation.

Replace localhost:5000 with IP and Port of your local docker registry.

```
docker build -t domainmagictestenv domainmagictestenv
docker tag domainmagictestenv localhost:5000/domainmagictestenv
docker push localhost:5000/domainmagictestenv
```