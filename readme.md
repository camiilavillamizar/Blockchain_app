# Blockchain App

1. [How to start the whole application with docker](#How-to-start-the-whole-application-with-docker)
2. [How to start the application without docker](#How-to-start-the-application-without-docker)
   - [How to start the frontend application](#How-to-start-the-frontend-application)
   - [How to start the node application](#How-to-start-the-node-application)
     - [Common Steps](#Common-Steps)
     - [Windows](#Windows)
     - [Mac & Linux](#mac--linux)
3. [How to start a node tunnel](#How-to-start-a-node-tunnel)
    - [Windows](#Windows-1)
    - [Mac](#Mac)
    - [Linux](#Linux)

## How to start the whole application with docker

```sh
  docker-compose -f "docker-compose.yml" up -d --build 
```

## How to start the application without docker

### How to start the frontend application

``` sh
    cd ./blockchain
    pip install -r requirements.txt
    python run_app.py
```

### How to start the node application

#### Common Steps

``` sh
    cd ./node_server
    pip install -r requirements.txt
```

#### Windows

``` sh
   SET FLASK_APP=node_server.py
   flask run --port=8000 --host=0.0.0.0
```

#### Mac & Linux

``` sh
    FLASK_APP=node_server.py flask run --port=8000 --host=0.0.0.0
```

## How to start a node tunnel

#### Windows

``` sh
 # replace PORT by the PORT NODE 
 # example ./start_tunnel_windows.sh 8000
 ./start_tunnel_windows.sh PORT 
```

#### Linux

``` sh
 # replace PORT by the PORT NODE 
 # example ./start_tunnel_linux.sh 8000
 ./start_tunnel_linux.sh PORT #replace PORT by the PORT NODE
```

#### Mac

``` sh
 # replace PORT by the PORT NODE 
 # example ./start_tunnel_mac.sh 8000
 ./start_tunnel_mac.sh PORT #replace PORT by the PORT NODE
```
