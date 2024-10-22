import telebot 

bot_token = "7447994267:AAE93orftBiqYP1BXyEoCvYV8quuh9aDFPA";

bot = telebot.TeleBot(bot_token)

questions = [
    "What crop do you grow?",
    ["Rice", "Sugarcane", "Brinjal", "Cucmuber"]
]

@bot.message_handler(commands=['start'])
def send_survey(message):
    chat_id = message.chat.id

    bot.send_poll(
        chat_id, questions[0], questions[1])

@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    print(pollAnswer)

bot.polling()
