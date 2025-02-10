# This project provide verification for code problems.

## Install 


### Install from Docker hub

```bash

docker pull tuenguyen/code_sandbox:base
docker pull tuenguyen/code_sandbox:server
```

### Install Sandbox Docker[Optional, Slowly, Not recommended]

1. Download boost_1_84_0.tar.gz to booth/
2. Run the following command to build docker image

```bash

docker build -f ./scripts/Dockerfile.base -t code_sandbox:base
# change the base image in Dockerfile.server
sed -i '1s/.*/FROM code_sandbox:base/' ./scripts/Dockerfile.server
docker build -f ./scripts/Dockerfile.server -t code_sandbox:server
docker run -d --rm --privileged -p 8080:8080 code_sandbox:server make run-online
```

### Example

1. Start Sandbox Docker

```bash
docker run -d --rm --privileged -p 8080:8080 code_sandbox:server make run-online
```

2. Run Example

```bash
python3 example_verify.py
```

