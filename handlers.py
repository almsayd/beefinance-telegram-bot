from datetime import datetime
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, Application, CommandHandler, MessageHandler, filters, ContextTypes, \
    CallbackContext
from fsm import FSM, States
from datetime import datetime, timedelta
import database
# увидел как один ютубер использовал это, не знаю почему именно Final когда можно в обычную переменную засунуть их,
# скорее всего так мы понимаем что это глобальная переменная
BOT_USERNAME: Final = '@beefinance_bot'
TOKEN: Final = '7445793423:AAGfCF8rugBL3YGeu3Ub-ZP9Bz_E-CzyPQk'
TIMENOW: Final = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
user_states = {}
fsm = FSM()

app = None  # Initialize app as None or with a default value


def set_app_instance(application):
    global app
    app = application


# с прошлой версии бота оставил
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'привет' in processed or 'салам' in processed:
        return 'Саламчик'

    if 'как ты?' in processed:
        return 'пока сервер запущен, я живой )'

    if 'регистрация' in processed:
        return 'для регистрации пропишите /register имя баланс'

    return 'Я пока не понимаю что ты мне пишешь '


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # то что при /start получается
    message = update.message if update.message is not None else update.edited_message  # чтобы не было ошибок когда
    # человек редактирует команду, тк тг бот воспринимает откредактированное сообщение как новое

    user_id = update.effective_user.id
    fsm.set_state(user_id, States.START)

    keyboard = [
        [InlineKeyboardButton("Зарегистрироваться", callback_data='register')],
    ]
    button = InlineKeyboardMarkup(keyboard)

    print(f"User ({update.effective_user.username}) начал беседу ({TIMENOW}) в "
          f"{update.effective_chat.title or 'личном чате'}")
    await update.message.reply_text('Добро пожаловать! Нажми на кнопку чтобы зарегистрироваться',
                                    reply_markup=button)


async def help(update: Update, contex: ContextTypes.DEFAULT_TYPE):
    message = update.message if update.message is not None else update.edited_message
    # команда help
    print(
        f'User ({update.effective_user.username}) ({update.effective_user.full_name}) вызвал команду /help ({TIMENOW}) в'
        f' {update.effective_chat.title or
            'личном'
            ' чате'}')

    await message.reply_text('/deleteme - удаление профиля \n')


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE, username, balance):
    user_id = update.effective_user.id
    nickname = update.effective_user.full_name
    username = update.effective_user.username or "Нет юзера"

    if database.user_exists(user_id):
        print(f'User ({user_id}) ({nickname}) попытался создать существующий профиль ')
        await update.message.reply_text("Вы уже зарегистрированы")
    else:
        try:
            print(f"User ({user_id}) ({nickname}) успешно зарегистрировался с балансом {balance}")
            database.register_user(user_id, username, balance, nickname)
            await update.message.reply_text(f"{username} успешно зарегистрировался с балансом {balance}")
            user_states[user_id] = States.REGISTRATION_COMPLETE
        except Exception as e:
            await update.message.reply_text(f"Не удалось зарегистрировать вас : {e}")


def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Баланс", callback_data='show_balance')],
        [InlineKeyboardButton("Добавить доход", callback_data='add_income'),
         InlineKeyboardButton("Добавить расход", callback_data='add_expense')],
        [InlineKeyboardButton("Показать транзакции", callback_data='show_transactions'),
         InlineKeyboardButton("Статистика расходов", callback_data='show_expense_stats')],
        [InlineKeyboardButton("Установить напоминание", callback_data='add_reminder')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_income_categories():
    keyboard = [
        [InlineKeyboardButton("Зарплата", callback_data='income_зарплата'),
         InlineKeyboardButton("Подарок", callback_data='income_подарок')],
        [InlineKeyboardButton("Инвестиции", callback_data='income_инвестиции'),
         InlineKeyboardButton("Фриланс", callback_data='income_фриланс')],
        [InlineKeyboardButton("Другое", callback_data='income_другое'),
         InlineKeyboardButton("Добавить свою категорию", callback_data='add_custom_category_income')],
        [InlineKeyboardButton('Назад', callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_expense_categories():
    keyboard = [
        [InlineKeyboardButton('Продукты питания', callback_data='expense_продукты'),
         InlineKeyboardButton('Транспорт', callback_data='expense_транспорт')],
        [InlineKeyboardButton('Жилье', callback_data='expense_жилье'),
         InlineKeyboardButton('Развлечение', callback_data='expense_развлечение')],
        [InlineKeyboardButton('Образование', callback_data='expense_образование'),
         InlineKeyboardButton('Добавить свою категорию', callback_data='add_custom_category_expense')],
        [InlineKeyboardButton('Назад', callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_everyday_buttons():
    keyboard = [
        [InlineKeyboardButton("Да", callback_data='everyday_yes'),
         InlineKeyboardButton("Нет", callback_data='everyday_no')]
    ]
    return InlineKeyboardMarkup(keyboard)


async def menu(update: Update, contex: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    nickname = update.effective_user.full_name
    buttons = get_menu_keyboard()

    if database.user_exists(user_id):
        print(f"User ({user_id}) ({username}) вызвал меню")
        if update.callback_query:
            await update.callback_query.answer()
            try:
                await update.callback_query.edit_message_text(text="Выберите действие:", reply_markup=buttons)
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    pass  # игнорируем ошибку, если сообщение не изменилось
                else:
                    raise  # перебрасываем исключение, если ошибка другая
        else:
            await update.message.reply_text('Выберите действие: ', reply_markup=buttons)
    else:
        print(f'User ({user_id}) ({username}) ({nickname}) попытался вызвать меню не зарегистировавшись')
        if update.callback_query:
            await update.callback_query.answer("Прежде чем вызвать меню зарегистрируйтесь!", show_alert=True)
        else:
            await update.message.reply_text("Прежде чем вызвать меню зарегистрируйтесь")


async def prompt_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id

    if fsm.get_state(user_id) == States.START:
        await query.answer()
        await query.edit_message_text("Введите ваш начальный баланс:")
        fsm.set_state(user_id, States.AWAITING_BALANCE)
    else:
        await query.answer("Что то пошло не так, начните с команды /start", show_alert=True)


async def process_registration_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    if fsm.get_state(user_id) == States.AWAITING_BALANCE:
        try:
            balance = int(update.message.text)
            username = update.effective_user.username or "Нет юзернейма"
            await register(update, context, username, balance)
            fsm.set_state(user_id, States.REGISTRATION_COMPLETE)
        except ValueError:
            await update.message.reply_text("Баланс должен быть числом, попробуйте снова")
    elif fsm.get_state(user_id) == States.WAITING_FOR_INCOME_AMOUNT:
        await handle_income_amount(update, context)
    elif fsm.get_state(user_id) == States.AWAITING_CUSTOM_INCOME_CATEGORY_NAME:
        await handle_category_and_ask_for_amount(update, context)
    elif fsm.get_state(user_id) == States.AWAITING_CUSTOM_INCOME_AMOUNT:
        try:
            amount = int(update.message.text)
            # Повторно вызываем функцию для обработки суммы, т.к. пользователь уже ввел название категории
            await handle_amount_and_save_transaction(update, context)
        except ValueError:
            # Если пользователь снова ввел некорректное значение, выводим сообщение об ошибке и ожидаем ввода снова
            await update.message.reply_text("Баланс должен быть числом, попробуйте снова")

    elif fsm.get_state(user_id) == States.WAITING_FOR_EXPENSE_AMOUNT:
        await handle_expense_amount(update, context)
    elif fsm.get_state(user_id) == States.AWAITING_CUSTOM_EXPENSE_CATEGORY_NAME:
        await handle_category_and_ask_for_amount(update, context)
    elif fsm.get_state(user_id) == States.AWAITING_CUSTOM_EXPENSE_AMOUNT:
        try:
            amount = int(update.message.text)
            # Повторно вызываем функцию для обработки суммы, т.к. пользователь уже ввел название категории
            await handle_amount_and_save_transaction(update, context)
        except ValueError:
            # Если пользователь снова ввел некорректное значение, выводим сообщение об ошибке и ожидаем ввода снова
            await update.message.reply_text("Баланс должен быть числом, попробуйте снова")

    elif fsm.get_state(user_id) == States.AWAITING_STATS_START_DATE:
        context.user_data['start_date'] = update.message.text
        await request_stats_end_date(update, context)
    elif fsm.get_state(user_id) == States.AWAITING_STATS_END_DATE:
        context.user_data['end_date'] = update.message.text
        await show_expense_stats(update, context)

    elif fsm.get_state(user_id) in (
            States.AWAITING_REMINDER_DATE, States.AWAITING_REMINDER_TIME, States.AWAITING_REMINDER_MESSAGE):
        await process_reminder_text(update, context)

    else:
        text = update.message.text if update.message else ""
        response = handle_response(text)
        await update.message.reply_text(response)
        print(f"({update.effective_user.full_name}) Получен текст от ({user_id}  {username}) пользователя: {text}   "
              f"\nОтвет бота:"
              f" {response}")


async def button_show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    username = update.effective_user.username
    nickname = update.effective_user.full_name
    buttons = get_menu_keyboard()

    balance = database.get_balance(user_id)
    print(f'User ({user_id}) ({username}) ({nickname}) показан баланс в {balance}')
    await context.bot.send_message(chat_id=user_id, text=f'Ваш баланс : {balance}')

    try:
        await query.edit_message_text(text='Выберите действие: ', reply_markup=buttons)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass  # Игнорируем ошибку, если сообщение не изменилось
        else:
            raise  # Перебрасываем исключение, если ошибка другая


async def delete_own_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message if update.message is not None else update.edited_message

    if database.user_exists(user_id):
        database.delete_user(user_id)
        print(f'User ({update.effective_user.username}) ({user_id}) удалил свой профиль  ')
        await message.reply_text("Ваш профиль был успешно удален")
    else:
        print(f'User ({update.effective_user.username}) пытался удалить профиль которого нет')
        await message.reply_text("Профиль не найден")


# эту функцию я взял с прошлой версии этого бота,где я игрался с ботом и хотел чтобы я получал в конфу все сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message if update.message is not None else update.edited_message
    message_type: str = message.chat.type
    text: str = message.text

    if message_type in ['group', 'supergroup']:  # проверка что если его добавят в группу он не отвечал всем подряд а
        # только когда его отметят
        if BOT_USERNAME in text:
            print(f'User ({update.effective_user.username}) in ({update.effective_chat.title}): {text}  ({TIMENOW})')
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    print(f'User ({update.effective_user.username}) in private: {text}  ({TIMENOW})')
    print(f'Bot: response to ({update.effective_user.username}) : {response}  ({TIMENOW})')
    await message.reply_text(response)


async def select_income_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    category = query.data.split('_')[1]
    context.user_data['category'] = category
    fsm.set_state(user_id, States.WAITING_FOR_INCOME_AMOUNT)
    await query.edit_message_text(text=f"Выбрана категория '{category}', пожалуйста, введите сумму дохода:")
    print(f'User ({user_id}) ({update.effective_user.username}) выбрал категорию {category}')


async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    buttons = get_income_categories()  # меню категорий доходов
    user_id = update.effective_user.id
    fsm.set_state(user_id, States.WAITING_FOR_INCOME_CATEGORY)
    if query:
        print(f'User ({update.effective_user.id}) ({update.effective_user.username}) выбрал добавить доход')
        await query.answer()
        await query.edit_message_text(text='Выберите категорию дохода:', reply_markup=buttons)
    else:
        message = update.message if update.message else update.edited_message
        if message:
            await message.reply_text(text='Выберите категорию дохода:', reply_markup=buttons)


async def handle_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if fsm.get_state(user_id) == States.WAITING_FOR_INCOME_AMOUNT:
        try:
            amount = int(update.message.text)
            user_id = update.effective_user.id
            category = context.user_data['category']

            if database.add_transaction(user_id, amount, 'income', category):
                await update.message.reply_text(
                    f"Доход в размере {amount}  в категории '{category}' успешно добавлен.")
                fsm.set_state(user_id, States.INCOME_ADDITION_COMPLETE)
                # чтобы меню добавления доходов никуда не уходила
                await add_income(update, context)

            else:
                await update.message.reply_text("Ошибка при добавлении транзакции.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите числовое значение для суммы.")
    else:
        await update.message.reply_text("Сначала выберите категорию дохода")


async def add_custom_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    callback_data = query.data

    if "add_custom_category_income" in callback_data:
        context.user_data['category_type'] = 'income'
        fsm_state = States.AWAITING_CUSTOM_INCOME_CATEGORY_NAME
    elif "add_custom_category_expense" in callback_data:
        context.user_data['category_type'] = 'expense'
        fsm_state = States.AWAITING_CUSTOM_EXPENSE_CATEGORY_NAME
    else:
        print(callback_data)
        await query.answer("Ошибка операциии", show_alert=True)
        return

    await query.answer()
    await query.message.reply_text("Введите название новой категории")
    fsm.set_state(user_id, fsm_state)


async def handle_category_and_ask_for_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_state = fsm.get_state(user_id)

    if current_state == States.AWAITING_CUSTOM_INCOME_CATEGORY_NAME or current_state == States.AWAITING_CUSTOM_EXPENSE_CATEGORY_NAME:
        # пользователь вводит название категории
        category_name = update.message.text
        context.user_data['custom_category_name'] = category_name

        await update.message.reply_text("Введите сумму для новой категории:")
        if current_state == States.AWAITING_CUSTOM_INCOME_CATEGORY_NAME:
            fsm.set_state(user_id, States.AWAITING_CUSTOM_INCOME_AMOUNT)
        else:
            fsm.set_state(user_id, States.AWAITING_CUSTOM_EXPENSE_AMOUNT)

    elif current_state == States.AWAITING_CUSTOM_INCOME_AMOUNT or current_state == States.AWAITING_CUSTOM_EXPENSE_AMOUNT:
        try:
            amount = int(update.message.text)
            category_name = context.user_data.get('custom_category_name')
            category_type = 'income' if current_state == States.AWAITING_CUSTOM_INCOME_AMOUNT else 'expense'

            await update.message.reply_text(
                f"Транзакция в категории '{category_name}' на сумму {amount} успешно добавлена")
            fsm.set_state(user_id, States.NONE)  # сброс состояния пользователя
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите числовое значение")


async def handle_amount_and_save_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    category_type = context.user_data.get('category_type')
    category = context.user_data.get('custom_category_name')
    amount_text = update.message.text

    try:
        amount = int(amount_text)
        if category_type == 'income':
            if database.add_transaction(user_id, amount, 'income', category):
                await update.message.reply_text(f"Доход в категории '{category}' на сумму {amount} успешно добавлен")
                fsm.set_state(user_id, States.INCOME_ADDITION_COMPLETE)
            else:
                await update.message.reply_text("Ошибка при добавлении транзакции.")
        elif category_type == 'expense':
            if database.add_transaction(user_id, -amount, 'expense',
                                        category):  # Assuming expenses are negative amounts
                await update.message.reply_text(f"Расход в категории '{category}' на сумму {amount} успешно добавлен")
                fsm.set_state(user_id, States.EXPENSE_ADDITION_COMPLETE)
            else:
                await update.message.reply_text("Ошибка при добавлении транзакции")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите числовое значение для суммы")
    finally:
        fsm.reset_state(user_id)


# отпаравка сообщения для всех юзеров сразу (о не отмечена в /help)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("Пожалуйста, укажите сообщение для рассылки")
        return

    users = database.fetch_all_users()
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            print(f"Сообщение отправлено пользователю {user_id}  ({datetime.now()})")
        except Exception as e:
            print(f'Ошибка при отправке сообщения пользователю {user_id}: {e} ({TIMENOW})')


async def show_transactions_button_handler(update, context):
    await show_transactions(update, context)


async def request_stats_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    fsm.set_state(user_id, States.AWAITING_STATS_START_DATE)
    if update.message:
        await update.message.reply_text("Введите начальную дату в формате ГГГГ-ММ-ДД:")
    elif update.callback_query:
        await update.callback_query.message.reply_text("Введите начальную дату в формате ГГГГ-ММ-ДД:")
        await update.callback_query.answer()


async def request_stats_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    fsm.set_state(user_id, States.AWAITING_STATS_END_DATE)
    if update.callback_query:
        await update.callback_query.message.reply_text("Введите конечную дату в формате ГГГГ-ММ-ДД:")
    else:
        await update.message.reply_text("Введите конечную дату в формате ГГГГ-ММ-ДД:")


async def show_expense_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    start_date = context.user_data['start_date']
    end_date = context.user_data['end_date']
    stats = database.get_expense_stats(user_id, start_date, end_date)
    if stats:
        message = "Статистика расходов:\n" + "\n".join(
            [f"Категория: {row[0]}, Сумма: {row[1]}, Дата: {row[2]}" for row in stats])
    else:
        message = "За указанный период транзакций не найдено"
    if update.callback_query:
        await update.callback_query.message.reply_text(message)
    else:
        await update.message.reply_text(message)
    fsm.reset_state(user_id)


async def show_transactions(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id

    fsm.set_state(user_id, States.VIEWING_TRANSACTIONS)

    transactions = database.get_transactions(user_id)
    if transactions:
        message = "Ваши транзакции:\n" + "\n".join(
            [f"Тип: {t[1]}, Категория: {t[2]}, Сумма: {t[0]}, Дата: {t[3]}" for t in transactions])
    else:
        message = "Транзакции не найдены"

    await query.answer()
    await context.bot.send_message(chat_id=user_id, text=message)
    fsm.reset_state(user_id)

    await query.edit_message_reply_markup(reply_markup=None)

    buttons = get_menu_keyboard()
    await context.bot.send_message(chat_id=user_id, text="Выберите действие:", reply_markup=buttons)


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    buttons = get_expense_categories()
    user_id = update.effective_user.id
    fsm.set_state(user_id, States.WAITING_FOR_EXPENSE_CATEGORY)

    if query:
        print(f'User ({update.effective_user.id}) ({update.effective_user.username}) выбрал добавить расход')
        await query.answer()
        await query.edit_message_text(text='Выберите категорию расхода:', reply_markup=buttons)
    else:
        message = update.message if update.message else update.edited_message
        if message:
            await message.reply_text(text='Выберите категорию расхода:', reply_markup=buttons)


async def handle_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if fsm.get_state(user_id) == States.WAITING_FOR_EXPENSE_AMOUNT:
        try:
            amount = int(update.message.text)
            user_id = update.effective_user.id
            category = context.user_data['category']

            if database.add_transaction(user_id, amount, 'expense', category):
                await update.message.reply_text(
                    f"Расход в размере {amount}  в категории '{category}' успешно добавлен")
                fsm.set_state(user_id, States.AWAITING_CUSTOM_EXPENSE_CATEGORY_NAME)
                # чтобы меню добавления доходов никуда не уходила
                await add_expense(update, context)

            else:
                await update.message.reply_text("Ошибка при добавлении транзакции")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите числовое значение для суммы.")
    else:
        await update.message.reply_text("Сначала выберите категорию расхода")


async def select_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    category = query.data.split('_')[1]
    context.user_data['category'] = category
    fsm.set_state(user_id, States.WAITING_FOR_EXPENSE_AMOUNT)
    await query.edit_message_text(text=f"Выбрана категория '{category}'. Пожалуйста, введите сумму расхода:")
    print(f'User ({user_id}) ({update.effective_user.username}) выбрал категорию {category}')


async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    fsm.set_state(user_id, States.AWAITING_REMINDER_DATE)
    await update.callback_query.message.reply_text("Введите месяц и день в формате ММ-ДД:")
    await update.callback_query.answer()


async def handle_reminder_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    date_text = update.message.text

    context.user_data['reminder_date'] = date_text
    fsm.set_state(user_id, States.AWAITING_REMINDER_TIME)

    await update.message.reply_text("Введите час и минуты в формате ЧЧ:ММ:")


async def handle_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    time_text = update.message.text

    context.user_data['reminder_time'] = time_text
    fsm.set_state(user_id, States.AWAITING_REMINDER_MESSAGE)

    await update.message.reply_text("Введите сообщение для напоминания:")


async def handle_reminder_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text

    context.user_data['reminder_message'] = message_text

    fsm.set_state(user_id, States.AWAITING_EVERYDAY_RESPONSE)

    reply_markup = create_everyday_buttons()

    await update.message.reply_text('Хотите получать это сообщение каждый день?', reply_markup=reply_markup)


async def handle_everyday_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    is_every_day = query.data == 'everyday_yes'
    date = context.user_data.get('reminder_date')
    time = context.user_data.get('reminder_time')

    message = context.user_data.get('reminder_message')
    database.set_reminder(user_id, message, date, time, is_every_day)

    fsm.set_state(user_id, States.REMINDER_ADDITION_COMPLETE)
    await query.edit_message_text("Напоминание добавлено")

# это message handler который отвечает за напоминалки
async def process_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = fsm.get_state(user_id)

    if state == States.AWAITING_REMINDER_DATE:
        await handle_reminder_date(update, context)
    elif state == States.AWAITING_REMINDER_TIME:
        await handle_reminder_time(update, context)
    elif state == States.AWAITING_REMINDER_MESSAGE:
        await handle_reminder_message(update, context)
    elif state == States.AWAITING_EVERYDAY_RESPONSE:
        await handle_everyday_response(update, context)
    else:
        await update.message.reply_text("Неизвестное состояние")


async def send_reminders():
    print('Скрипт по отправке напоминаний сработал >>')
    reminders = database.get_reminders_for_now()
    if reminders:
        for user_id, message, isEveryDay in reminders:
            try:
                await app.bot.send_message(chat_id=user_id, text=message)
                print(f"Напоминание отправлено пользователю {user_id} : {message}")
                database.delete_sent_reminders(user_id, datetime.now().strftime('%Y-%m-%d'),
                                               datetime.now().strftime('%H:%M'))
            except Exception as e:
                print(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")

# curl -X POST https://api.telegram.org/bot7445793423:AAGfCF8rugBL3YGeu3Ub-ZP9Bz_E-CzyPQk/sendMessage -d
# chat_id=2050771063 -d text="test"
