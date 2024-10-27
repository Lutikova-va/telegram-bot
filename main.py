import asyncio
import mydb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from telebot import types
from telebot.async_telebot import AsyncTeleBot

from Secrets.secrets import TELEGRAM_TOKEN

bot = AsyncTeleBot(TELEGRAM_TOKEN)

user_data = {}


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    try:
        logger.info(f"Received command '{message.text}' from user {message.from_user.id} in chat {message.chat.id}")
        greeting = ('Здравствуйте! Я - чат-бот ветеринарной клиники "Доктор Вет". В данный момент я нахожусь в '
                    'разработке.'
                    'Вот, какие команды у меня уже есть:')
        await bot.send_message(message.chat.id, greeting)
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn_appt = types.InlineKeyboardButton(text='Записаться', callback_data='sw_make')
        btn_see_appt = types.InlineKeyboardButton(text='Посмотреть записи', callback_data='sw_see')
        kb.add(btn_appt)
        kb.add(btn_see_appt)
        await bot.send_message(message.chat.id, "Здесь вы можете записаться на прием или посмотреть, какие записи у "
                                                "Вас уже есть",
                                reply_markup=kb)
        logger.info(f"Sent welcome message to user {message.from_user.id} in chat {message.chat.id}")
    except Exception as e:
        logger.error(f"Error in send_welcome: {e}", exc_info=True)


@bot.callback_query_handler(func=lambda call: True)
async def callback_make_see(callback: types.CallbackQuery):
    try:
        logger.info(f"Received callback query from user {callback.from_user.id}: {callback.data}")
        if callback.data == "sw_make":
            await ask_details(callback.from_user.id)
        elif callback.data == "sw_see":
            info = await mydb.get_info(callback.from_user.id)
            print(info)
            if info:
                for i in range(len(info)):
                    response_message = (f"Вы - {info[i][1]}, номер телефона {info[i][2]}, создали запись к врачу-{info[i][4]}, с "
                                        f"животным - {info[i][3]}, по поводу {info[i][5]}. Ожидайте звонка "
                                        f"для выяснения точной даты приема.")
            else:
                response_message = "Нет информации для отображения."
            await bot.send_message(callback.from_user.id, response_message)
    except Exception as e:
        logger.error(f"Error in callback_make_see for user {callback.from_user.id}: {e}", exc_info=True)


@bot.message_handler(commands=['makeappointment'])
async def ask_details(user_id):
    try:
        text = 'Введите ваше ФИО'
        await bot.send_message(user_id, text)
        user_data[user_id] = {'step': 'awaiting_name'}
        logger.info(f"User {user_id} is now in step: awaiting_name")
    except Exception as e:
        logger.error(f"Error in ask_details for user {user_id}: {e}", exc_info=True)


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id][
    'step'] == 'awaiting_name')
async def handle_name(message):
    try:
        logger.info(f"User {message.from_user.id} provided name: {message.text}")
        user_data[message.from_user.id]['name'] = message.text
        user_data[message.from_user.id]['step'] = 'awaiting_phone'
        await bot.send_message(message.chat.id, "Введите ваш номер телефона:")
        logger.info(f"User {message.from_user.id} is now in step: awaiting_phone")
    except Exception as e:
        logger.error(f"Error in handle_name for user {message.from_user.id}: {e}", exc_info=True)


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id][
    'step'] == 'awaiting_phone')
async def handle_phone(message):
    try:
        user_data[message.from_user.id]['phone'] = message.text
        logger.info(f"User {message.from_user.id} provided phone: {message.text}")
        user_data[message.from_user.id]['step'] = 'awaiting_animal_type'
        await bot.send_message(message.chat.id, "Введите вид вашего животного (например, собака, кошка):")
        logger.info(f"User {message.from_user.id} is now in step: awaiting_animal_type")
    except Exception as e:
        logger.error(f"Error in handle_phone for user {message.from_user.id}: {e}", exc_info=True)
        await bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id][
    'step'] == 'awaiting_animal_type')
async def handle_animal_type(message):
    try:
        user_data[message.from_user.id]['animal_type'] = message.text
        logger.info(f"User {message.from_user.id} provided animal type: {message.text}")
        user_data[message.from_user.id]['step'] = 'awaiting_doctor'
        logger.info(f"User {message.from_user.id} is now in step: awaiting_doctor")
        await bot.send_message(message.chat.id, "Введите специализацию врача, к которому хотите записаться:")
    except Exception as e:
        logger.error(f"Error in handle_animal_type for user {message.from_user.id}: {e}", exc_info=True)
        await bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id][
    'step'] == 'awaiting_doctor')
async def handle_doctor(message):
    try:
        user_data[message.from_user.id]['doctor'] = message.text
        logger.info(f"User {message.from_user.id} provided doctor specialization: {message.text}")
        user_data[message.from_user.id]['step'] = 'awaiting_problem'

        await bot.send_message(message.chat.id, "Опишите проблему, с которой вы обращаетесь:")
        logger.info(f"User {message.from_user.id} is now in step: awaiting_problem")
    except Exception as e:
        logger.error(f"Error in handle_doctor for user {message.from_user.id}: {e}", exc_info=True)
        await bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id][
    'step'] == 'awaiting_problem')
async def handle_problem(message):
    try:
        user_data[message.from_user.id]['problem'] = message.text
        logger.info(f"User {message.from_user.id} provided problem description: {message.text}")
        user_data[message.from_user.id]['step'] = None
        await confirm_details(message.from_user.id)
        logger.info(f"User {message.from_user.id} has completed the input process.")
    except Exception as e:
        logger.error(f"Error in handle_problem for user {message.from_user.id}: {e}", exc_info=True)
        await bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
message_id = None


@bot.message_handler(func=lambda message: message.text in [
    "Подтвердить",
    "Изменить ФИО",
    "Изменить телефон",
    "Изменить вид животного",
    "Изменить врача",
    "Изменить проблему"
])
async def handle_confirmation(message):
    user_id = message.from_user.id
    try:
        if user_id not in user_data:
            await bot.send_message(user_id, "Вы еще не начали процесс записи.")
            logger.warning(f"User {user_id} attempted to confirm without starting the process.")
            return

        if message.text == "Подтвердить":
            response_text = "Ваша запись успешно сохранена!"
            await bot.send_message(user_id, response_text)
            name = user_data[message.from_user.id]['name']
            phone = user_data[message.from_user.id]['phone']
            animal_type = user_data[message.from_user.id]['animal_type']
            doctor = user_data[message.from_user.id]['doctor']
            problem = user_data[message.from_user.id]['problem']
            await mydb.create_table()
            await mydb.add_new_appt(user_id, name, phone, animal_type, doctor, problem)
            logging.info("Попытка сохранить запись для пользователя %s , %s , %s , %s , %s , %s", user_id, name, phone, animal_type, doctor, problem)

            del user_data[user_id]

        else:
            field_mapping = {
                "Изменить ФИО": "awaiting_name_only",
                "Изменить телефон": "awaiting_phone_only",
                "Изменить вид животного": "awaiting_animal_type_only",
                "Изменить врача": "awaiting_doctor_only",
                "Изменить проблему": "awaiting_problem_only"
            }

            field = field_mapping.get(message.text)

            if field:
                user_data[user_id]['step'] = field

                prompts = {
                    'awaiting_name_only': "Введите ваше ФИО:",
                    'awaiting_phone_only': "Введите ваш номер телефона:",
                    'awaiting_animal_type_only': "Введите вид вашего животного:",
                    'awaiting_doctor_only': "Введите специализацию врача:",
                    'awaiting_problem_only': "Опишите проблему:"
                }

                await bot.send_message(user_id, prompts[field])
                logger.info("User %s is now in step: %s", user_id, field)
            else:
                await bot.send_message(user_id, "Неизвестная команда.")
                logger.warning(f"User {user_id} sent an unknown command: {message.text}")
    except Exception as e:
        logger.error(f"Error in handle_confirmation for user {user_id}: {e}", exc_info=True)
        await bot.send_message(user_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


@bot.message_handler(
    func=lambda message: message.from_user.id in user_data and (
            user_data[message.from_user.id].get('step') == 'awaiting_name_only' or
            user_data[message.from_user.id].get('step') == 'awaiting_phone_only' or
            user_data[message.from_user.id].get('step') == 'awaiting_animal_type_only' or
            user_data[message.from_user.id].get('step') == 'awaiting_doctor_only' or
            user_data[message.from_user.id].get('step') == 'awaiting_problem_only'))
async def update_user_data(message):
    try:
        user_id = message.from_user.id
        step = user_data[user_id]['step']

        if step == 'awaiting_name_only':
            user_data[user_id]['name'] = message.text
            logger.info("User %s updated their name to: %s", user_id, message.text)
            await bot.send_message(user_id, f"Ваше ФИО обновлено на: {message.text}.")
        elif step == 'awaiting_phone_only':
            user_data[user_id]['phone'] = message.text
            await bot.send_message(user_id, f"Ваш номер телефона обновлен на: {message.text}.")
            logger.info("User %s updated their phone to: %s", user_id, message.text)
        elif step == 'awaiting_animal_type_only':
            user_data[user_id]['animal_type'] = message.text
            await bot.send_message(user_id, f"Ваш вид животного обновлен на: {message.text}.")
            logger.info("User %s updated their animal type to: %s", user_id, message.text)
        elif step == 'awaiting_doctor_only':
            user_data[user_id]['doctor'] = message.text
            await bot.send_message(user_id, f"Специализация врача обновлено на: {message.text}.")
            logger.info("User %s updated their doctor specialization to: %s", user_id, message.text)
        elif step == 'awaiting_problem_only':
            user_data[user_id]['problem'] = message.text
            await bot.send_message(user_id, f"Описание проблемы обновлено на: {message.text}.")
            logger.info("User %s updated their problem description to: %s", user_id, message.text)
        user_data[user_id]['step'] = None
    except Exception as e:
        logger.error(f"Error updating user data for user {user_id}: {e}", exc_info=True)
        await bot.send_message(user_id, "Произошла ошибка при обновлении данных. Пожалуйста, попробуйте еще раз.")


@bot.message_handler(func=lambda message: True)
async def fallback_handler(message):
    try:
        user_id = message.from_user.id
        if user_id in user_data and user_data[user_id].get('step') is not None:
            await bot.send_message(user_id, "Пожалуйста, завершите текущий ввод данных.")
            logger.info("User %s is in the middle of data entry.", user_id)
        else:
            await bot.send_message(user_id, "Пожалуйста, используйте доступные команды.")
            logger.info("User %s sent a message without ongoing data entry.", user_id)
    except Exception as e:
        logger.error(f"Error in fallback_handler for user {user_id}: {e}", exc_info=True)
        await bot.send_message(user_id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


async def confirm_details(user_id):
    try:
        details = user_data[user_id]
        response_text = (f"Спасибо! Вот ваша запись:\n"
                        f"ФИО: {details['name']}\n"
                        f"Телефон: {details['phone']}\n"
                        f"Вид животного: {details['animal_type']}\n"
                        f"Врач: {details['doctor']}\n"
                        f"Проблема: {details['problem']}\n\n"
                        f"Если все верно, нажмите 'Подтвердить'. Если хотите изменить данные, выберите нужное поле.")

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_confirm = types.KeyboardButton("Подтвердить")
        btn_edit_name = types.KeyboardButton("Изменить ФИО")
        btn_edit_phone = types.KeyboardButton("Изменить телефон")
        btn_edit_animal = types.KeyboardButton("Изменить вид животного")
        btn_edit_doctor = types.KeyboardButton("Изменить врача")
        btn_edit_problem = types.KeyboardButton("Изменить проблему")

        kb.add(btn_confirm, btn_edit_name, btn_edit_phone, btn_edit_animal, btn_edit_doctor, btn_edit_problem)

        sent_message = await bot.send_message(user_id, response_text, reply_markup=kb)

        user_data[user_id]['message_id'] = sent_message.message_id
        logger.info("User %s received confirmation details.", user_id)

    except Exception as e:
        logger.error(f"Error in confirm_details for user {user_id}: {e}", exc_info=True)
        await bot.send_message(user_id, "Произошла ошибка при отправке ваших данных. Пожалуйста, попробуйте еще раз.")


asyncio.run(bot.polling())
