# OM Chatbot 

This subdirectory contains the code for the OM chatbot POC.  The main purpose
of this bot is to help OM capture financial details about their population of
farmers. 

## Quickstart 

```console
$ git clone git@github.com:bprashanth/t4g.git
$ cd organicmandya/ansible
$ ansible-playbook playbook.yaml --connection=local --inventory 127.0.0.1, -K
```

### Unittests

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
$ python3 ./chatbot_test.py
```

This will ask for your sudo password before starting, and install binaries as
necessary.  If you do not want it to overwrite your binaries, open the
`playbook.yaml` file and comment out the relevant plays. 

## Architecture 

* The chatbot relies solely on the telegram API for updates. 
* All updates are stored in mongo. 
* Summary reports are computed based on updates in mongo. 
```
 -----------> Telegram API
 |		/
 |             / get_updates
 |	      v
user <- chatbot  <----> mongo <---> summary
```

## Telegram API

Some notes on the telegram API. 

### Keyboards 

This bot uses the `ReplyKeyboardMarkup` ([src](https://core.telegram.org/bots/features#keyboards)).

### Get updates

We can't call `get_updates` with the last update id because it could be lower than the randomized (but current) update id. 
```
The update's unique identifier. Update identifiers start from a certain positive number and increase sequentially. This ID becomes especially handy if you're using Webhooks, since it allows you to ignore repeated updates or to restore the correct update sequence, should they get out of order. If there are no new updates for at least a week, then identifier of the next update will be chosen randomly instead of sequentially.
```
* Source of [get_updates](https://github.com/python-telegram-bot/python-telegram-bot/blob/146ec54a00466bbe0fd16b16791a850a7a9ef594/telegram/_bot.py#L4266) - sets offset to 0 when invoked without any arguments. 
* Source of [start_polling](https://github.com/python-telegram-bot/python-telegram-bot/blob/v21.3/telegram/ext/_updater.py#L214) - sets offset to None when invoked on restart. 
```
offset:

    Integer: Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned.
    Special Values:
        0: All unconfirmed updates are returned.
        None: Same as not setting the parameter; all unconfirmed updates are returned.
```

### Combining the keyboard and getupdates 

* Create an updater 
* Retrieve its dispatcher to add handlers (?) - there is no other way to plug in your keyboard
* `start_polling`

## Mongo

* Adding collections 
```
test> db.createCollection("testcollection", {capped: true, size: 5000000, max: 1000000})
{ ok: 1 }

```
* Aws [cheatsheet](https://mongodb-devhub-cms.s3.us-west-1.amazonaws.com/Mongo_DB_Shell_Cheat_Sheet_1a0e3aa962.pdf)
* Mongo docker [page](https://hub.docker.com/_/mongo). Run it with a custom config and datadir: 
**NB: you must change your datadir and logdir in the command below for it to run**
```
$ docker run --name some-mongo --env-file chatbot.env -p 27017:27017 -v ./config:/etc/mongo -v /my/own/datadir:/var/lib/mongodb -v /my/own/logdir:/var/log/mongodb -d mongo:7.0.12-jammy --config /etc/mongo/mongod.conf
```
* See `./config/mongod.conf` for other config options  
 
## Appendix 

* [List](https://core.telegram.org/bots/samples) of telegram bot frameworks
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot?tab=readme-ov-file) API (used by telegram menu) 
* [pytelegrambot api](https://github.com/eternnoir/pyTelegramBotAPI)
* [telegram menu](https://github.com/mevellea/telegram_menu) lib has great examples of buttons 
### Test Bot details

* Name: ravenous
* Bot name: `ravenous_pig_bot`
* Address: `t.me/ravenous_pig_bot`


