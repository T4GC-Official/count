# Count

<img src="https://github.com/T4GC-Official/count/raw/main/logo.png" width="300">

Count, also known as Count Von McCount, is an open source pocket accountant for tracking quant data across customizable categories. 

---

Count was initially developed as a straw man for a quant based app. 

This was the main journey in this app: 

* User enters data on household spending, daily 
* We analyze this data for population trends
* We disseminate advisories back to our users

We had some doubts about our users' ability to adopt the app's full functionality. To address this, we simplified the app to its core features (Count), released it, and are gathering feedback from a dedicated group of field testers. 

In the meantime, we found an unexpected application for Count. One of our partners needed to collect frequent, quantitative data (specifically, the price and type of groceries a household buys) as part of a multi-stage survey. By integrating Count, we aim to improve the accuracy and quality of responses for this specific question.

https://github.com/user-attachments/assets/a312d0e1-b29a-43d1-9994-21a7808af49b

## Running Count 

There are a several different ways to install and run count, depending on your environment    
1. On a new VM: auto install the setup dependencies through the `setup_bot.sh` script     
2. On a Mac: manually install docker and docker-compose (the instructions for a mac keep changing and you will have to look these up yourself)     
3. On a "stale" VM or a linux laptop: use the ansible setup. Though this option is a bit heavier than the others, it ensures a clean setup of count.     
4. On windows: currently untested, provision a linux vm, ssh into it and do setp 1. 

### On a new VM (or a mac)

Run these commands 
```
$ sudo apt-get install git 
$ mkdir -p src/github.com/T4GC-Official/count 
$ cd src/github.com/T4GC-Official/count 
$ git clone @https://github.com/T4GC-Official/count.git 
$ cd count 
```
At this point, if you're on a mac you should just manually install docker and docker-compose according to pulic documentation. 
If you're on a vm, you can run
```
$ ./hack/setup_bot.sh
```
The following 2 steps should be the same whether on a mac or a VM
```
$ newgrp docker
# Your telegram chatbot key is retrieved via telegra's botfather chatroom. 
# If you are looking for a specific chatbot's API keys, ask the creators of that chatroom. 
$ echo "API_KEY=<your-telegram-chatbot-api-key>" > ./.env
$ docker compose up -d --build 
```

### Ansible deployment (on a linux laptop) 

There are several advantages to using ansible. Most notably, the setup is cleaner - so for example if you are running count on an existing VM with unknown dependencies already `apt-get installed` (or on your linux laptop) - you would like for that not _not_ conflict with your count deployment. Ansible setup handles this by rsyncing the source and a clean set of requirements into a temp directory. To run through ansible, first, install [docker](https://docs.docker.com/get-started/get-docker/) and [docker compose](https://docs.docker.com/compose/install/), then, build the image and run it locally
```
$ make build IMAGE=<your repo>/<your image name> TAG=latest DOCKERFILE=./Dockerfile
$ echo "API_KEY=<your-telegram-chatbot-api-key>" > ./.env
$ cd ansible
$ ansible-playbook playbook.yaml --connection=local --inventory 127.0.0.1, -K
```

## Data dumps 

You can get data dumps as excel files in your email. First ask the creator of the chatbot (if it isn't you) for the SMTP password. This is the app password of the gmail account in the "from" field of the emails. This password is typically stored in the same `.env` file as the `API_KEY` of the chatbot. 
```console 
$ docker ps 
CONTAINER ID   IMAGE           COMMAND                  CREATED          STATUS          PORTS       NAMES
5cfd1acdd549   count-chatbot   "supervisord -c /etc…"   20 minutes ago   Up 20 minutes   27017/tcp   chatbot

$ docker exec -it chatbot /bin/bash

# python3 hack/mongo_to_excel.py --email recipient@example.com --smtp-user your.email@gmail.com --smtp-password "your-16-char-app-password" 
```
For example to email `yourself@hotmail.com` the usage report, set that as the `--email` and set `--smtp-user` to `lipokchatbot@gmail.com`. Ask the creator of `lipokchatbot@gmail.com` for the `app password` for that account (or check `.env`) and use that as `--smtp-password`. 

## Deploying Count

See [deployment guide](./docs/deployment.md) for AWS fargate deployment. Note that if you are OK simply SSH-ing into a VM on AWS then you can simply following the steps in the "Running Count" section. 

## Contributing 

WIP
