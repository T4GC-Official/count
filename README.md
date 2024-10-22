# Count

<img src="https://github.com/T4GC-Official/count/raw/main/logo.png" width="100">

---

Count, also known as Count Von McCount, is an open source pocket accountant for tracking quant data across customizable categories. 

## Using count as a straw man for a quant based app

This was the main reson Count was developed. 

If your app's ux is as follows: 
1. User opens app regularly to enter data (eg household spending) 
2. You (as a NGO or research body) analyze this data (eg for population trends) 
3. You disseminate your findings back to the user through the app

And you are not certain whether your user base is capable of this journey - you don't need to develop the app to find out! 

First deploy Count and use it to test your program end to end. 

If your target population is unable to use Count - analyze why first - it is highley likely they will not be able to use your bespoke app as well. Fix these problems, then delve into the science of app development. 

Analyzing Count data is a manual process. You must use the scripts in the repo to analyze the trends. However doing so can tell you: 

1. Who has installed/uninstalled the app
2. Who has used the app and how often
3. Who understands the translations and responds correctly 
4. How many interactions failed due to network connectivity 
etc

Based on these findings you can identify next steps, eg: 

1. Should your app simply stay a chatbot? 
2. Does your app need voice/image/nlp formats to aid with understanding?
3. Are your users capable of regularly interacting with their phones?
4. Are your users capable of self reporting data?  
5. How good is the internet connectivity in your target group?
etc

## Using Count as a tool for data collection 

If you have an N stage survey, and one of the steps in that survey require frequent quantative data entry (eg price and type of groceries a house consumes, daily bp/spo2 readings etc) - you _may_ be able to use Count and retrieve a higher fidelity response to that specific question. Rather than implementing the entire questionnaire as a chatbot, keep your existing program (eg feet on street or web surveys) to collect the infrequently updated fields of the survey, and deploy Count to track the frequently changing fields. 


## Running Count 

WIP 

## Deploying Count

WIP

## Contributing 

WIP

## Adopters 

The [User Case Studies](./docs) directory has real-world use cases of organizations deploying Count. 


