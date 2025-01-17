# Deploying count to AWS 

This project is deployed through [launchpad](tbd). Steps to deployment: 

1. Create the AWS ECS cluster via launchpad
2. Modify your configs with site specific info
3. Deploy your service (the om-chatbot) 

## Create the AWS ECS cluster 

Running 
```
# First edit deploy_app.yml to set your cluster name etc.
$ ansible-playbook deploy_app.yml -e "state=create"
```
Will create an AWS ECS cluster. 
And running 
```
$ ansible-playbook deploy_app.yml -e "state=describe"
```
Will display resources for that cluster, including the EFS volumes used in the next step. 

## Configs

Before deploying services in the cluster, you will need to modify the templates. 
The deployment config templates are in `/deployment/test` and `/deployment/prod` respectively. 
The modifications required are currently manual (tbd): 

1. Task ARNs
```
  "executionRoleArn": "",
  "taskRoleArn": "",
```
To
```
  "executionRoleArn": "arn:aws:iam::<numeric string>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<numeric string>:role/ecsMinimalTaskRole",
```
There are launchpad helper scripts ([here](tbd)) to generate/validate these ARNs. 

You need these in order to `exec` into your containers, and mount the EFS volume. 

2. EFS volume name 

Launchpad sets up the cluster to have one EFS volume which all services and tasks can write into. You can figure out the name of this volume post cluster creation.
```
  "volumes": [
    {
      "name": "mongo-efs",
      "efsVolumeConfiguration": {
        "fileSystemId": "<efs id>"
      }
    }
  ]
```

NB: the entrypoint script will create a nested data dir within the supervisord script (see [here](https://github.com/T4GC-Official/count/blob/b9d91bed0b2a0978d82d507bc2425fe7e47a4a85/supervisord.conf#L8)). This is suboptimal but temporary. 

3. Secrets (API KEY)

Add your telegram chatbot api key (the same key you placed in .env for the local setup) 
```
      "environment": [
        {
          "name": "API_KEY",
          "value": "<your api key>"
        }
      ],
```

4. Logs 

Launch pad will auto create a logs group with your specified `cluster-name`
```
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/<cluster-name>",
          "awslogs-region": "ap-south-1",
          "awslogs-stream-prefix": "om-chatbot-test"
        }
      }
```

5. Resources 

The resources are auto defaulted to the lowest values available in fargate.
You can consult launchpad [docs](tbd) for how to measure this. 

6. Image 

Lastly, make sure your image is pushed 
```
$ make build push IMAGE=<repo>/<image> TAG=latest DOCKERFILE=./Dockerfile
```
matches 
```
      "image": "bprashanth/cc-om-chatbot:latest",
```

## Deployment

Run 
```
# Edit deploy_app.yml to point it at deployment/test/ to use test configs
$ ansible-playbook deploy_app.yml -e "state=sync"
```
Will deploy the chatbot as a service in that cluster. 

NB: The name of the **file** is templated in as the service name. Hence to
deploy a "test" service, you need to name the file in "deployment/test/" -
"om-chatbot-test.yml". 

See launchpad [documentation](tbd) for more details. 


