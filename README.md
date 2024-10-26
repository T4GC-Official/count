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

Build and run locally
```
$ make build IMAGE=<your repo>/<your image name> TAG=latest DOCKERFILE=./Dockerfile
$ echo "API_KEY=<your-telegram-chatbot-api-key>" > ./.env
$ cd ansible
$ ansible-playbook playbook.yaml --connection=local --inventory 127.0.0.1, -K
```

## Deploying Count

See [deployment guide](./docs/deployment.md) for AWS deployment. 

## Contributing 

WIP
