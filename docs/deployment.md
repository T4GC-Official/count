## Quickstart

If you already have a running cluster and want to deploy a chatbot, first modify your task (in your projects `deployments/prod` or `deployments/test`)
```json
  "family": "${org}-chatbot-test",
...
  "containerDefinitions": [
    {
      "name": "chatbot",
      "image": "bprashanth/cc-${org}-chatbot:latest",
...
      "environment": [
        {
          "name": "API_KEY",
          "value": "${API_KEY}"
        }
      ],
...
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cc",
          "awslogs-region": "ap-south-1",
          "awslogs-stream-prefix": "${om}-chatbot-test"
        }
      }
    }
...
```
NOTE: It is important that you do not actually check in your `API_KEY`. Everything else in the json above can be checked in. 

Then, modify your supervisor file (in your project)
```yaml
[program:mongod]
command=/usr/local/bin/docker-entrypoint.sh mongod --config /etc/mongo/mongod_default.conf --dbpath /data/cc/${org}/chatbot/test
...
[program:chatbot]
command=python3 /usr/src/app/chatbot.py --host localhost --bot_name ${bot_name}
```
You need to repush your docker image after this (in your project)
```shell
$ make build push IMAGE=bprashanth/cc-lipok-chatbot TAG=0.2 DOCKERFILE=./Dockerfile
```

Then, in THIS project, make sure `deploy_app.yml` is pointed at the right location 
```yaml

```

Finally, in this project, run
```shell
$ ansible-playbook deploy_app.yml -e "state=sync"
```

## Logs

If you want to check the logs of a running task
```
$ aws logs tail "/ecs/$CLUSTER" --log-stream-name-prefix "$SERVICE_NAME" --follow
```

* The `log_group` is setup at cluster creation time using the cluster name 
* Each task is responsible for naming its own `log-stream-name-prefix`, usually it names it after the service 
* You should see intervealed logs for all tasks in the service 

