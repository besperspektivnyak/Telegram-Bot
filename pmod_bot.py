from telebot import types
import json
import requests

TOKEN = os.environ['TELEGRAM_TOKEN']
some_api_token = os.environ['SOME_API_TOKEN']
import telebot
bot = telebot.TeleBot(TOKEN)
population_id = None
global host_url

with open('config.json') as file:
    global host_url
    path = json.load(file)
    host_url = path['host_url']


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global population_id
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, займёмся исследованием популяций?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Этот бот поможет тебе в исследовании собственной популяции. Команда"
                                               " /start начинает твою работу с популяцией. Следуй инструкциям на каждом шаге")
    elif message.text == '/start':
        bot.send_message(message.from_user.id, "Давай создадим тебе собственную популяцию для исследований")
        population_id = create_population()
        if population_id is not None:
            bot.send_message(message.from_user.id, "Популяция успешно создана, давай добавим в неё особей")
            bot.send_message(message.from_user.id,
                             "Укажи подряд два значения: жизнеспособность особи от 0 до 1 и шанс размножиться от 0 до 1")
            bot.send_message(message.from_user.id, "Например, так: 0.5 0.3")
            bot.register_next_step_handler(message, add_individual)

        else:
            bot.send_message(message.from_user.id, "Произошла какая-то ошибка, попробуй начать сначала")
    else:
        bot.send_message(message.from_user.id, 'Я тебя не понимаю. Напиши /help')


def create_population() -> int:
    response = requests.get(host_url)
    if response.status_code == 200:
        new_data = json.loads(response.json())
        return new_data['id']


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global individual_parameters
    if call.data == "Добавить ещё":
        bot.send_message(call.message.chat.id, "Тогда введи новые параметры")
        bot.register_next_step_handler(call.message, add_individual)
    elif call.data == "Перейти к исследованиям":
        bot.send_message(call.message.chat.id, "Введи агрессивность среды от 0.1 до 1 и скорость мутаций особей от 0 до 0.1")
        bot.register_next_step_handler(call.message, run_research)


def send_keyboard(message):
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Добавить ещё', callback_data='Добавить ещё')  # кнопка «Да»
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='Перейти к исследованиям', callback_data='Перейти к исследованиям')
    keyboard.add(key_no)
    bot.send_message(message.from_user.id,
                     text="Что делать дальше?",
                     reply_markup=keyboard)


def add_individual(message):
    individual_parameters = {"type": 'bacteria'}
    try:
        parameters = list(map(float, message.text.split()))
        individual_parameters['lifetime'] = 3
        individual_parameters['p_for_death'] = 1 - parameters[0]
        individual_parameters['p_for_reproduction'] = parameters[1]
        requests.post(host_url + str(population_id) + '/add/', data=individual_parameters)
    except Exception:
        bot.send_message(message.from_user.id, 'Что-то не так с параметрами, попробуй ещё')
        bot.register_next_step_handler(message, add_individual)
    send_keyboard(message)


def run_research(message):
    research_parameters = {"n": 1, "s_t": "uniform", "m_t": 'normal'}
    try:
        parameters = list(map(float, message.text.split()))
        research_parameters['s_m'] = parameters[0]
        research_parameters['m_m'] = parameters[1]
        # ТУТ ФОРМИРУЕТСЯ ЗАПРОС НА ЗАПУСК РЕСЕРЧА
        # ПОТОМ ПРЯМ JSON ОТПРАВИТЬ В ОТВЕТ
        response = requests.post(host_url + str(population_id) + '/run/', data=research_parameters)
        if response.status_code == 200:
            new_data = response.json()
            bot.send_message(message.from_user.id, "В твоей популяции: {alive} живых особей, {dead} "
                                                   "мертвых особей".format(**new_data))
    except Exception:
        bot.send_message(message.from_user.id, 'Что-то не так с параметрами, попробуй ещё')
        bot.register_next_step_handler(message, run_research)


bot.polling(none_stop=True, interval=0)
