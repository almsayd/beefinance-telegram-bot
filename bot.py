import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import (Application, Updater, ContextTypes, CommandHandler, MessageHandler, filters,
                          CallbackQueryHandler)

# 22.07 ластовый день как я пилю этого бота. Делал долго и сегодня вот прощаюсь , без багов никуда , поэтому жду ваш
# фидбек


import database
import handlers
from fsm import FSM



 # инициализация статусов
fsm = FSM()

if __name__ == '__main__':
    app = Application.builder().token("7445793423:AAGfCF8rugBL3YGeu3Ub-ZP9Bz_E-CzyPQk").build()

    handlers.set_app_instance(app)
    # Обработчики команд которые не используются пользователем
    app.add_handler(CommandHandler('start', lambda update, context: handlers.start(update, context)))
    app.add_handler(
        CommandHandler('deleteme', lambda update, context: handlers.delete_own_profile(update, context)))
    app.add_handler(CommandHandler('help', lambda update, context: handlers.help(update, context)))
    app.add_handler(CommandHandler('expense', lambda update, context: handlers.add_expense(update, context)))
    app.add_handler(CommandHandler('broadcast', lambda update, context: handlers.broadcast(update, context)))
    app.add_handler(CommandHandler('menu', lambda update, context: handlers.menu(update, context)))

    # CallbackQueryHandlers для inline кнопок
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.prompt_registration(update, context),
                                         pattern='^register$'))
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.menu(update, context), pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.button_show_balance(update, context),
                                         pattern='^show_balance$'))
    app.add_handler(
        CallbackQueryHandler(lambda update, context: handlers.add_income(update, context), pattern='^add_income$'))
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.select_income_category(update, context),
                                         pattern='^income_'))
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.add_custom_category(update, context),
                                         pattern='^add_custom_category_income'))

    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.menu(update, context), pattern='^back$'))

    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.add_expense(update, context),
                                         pattern='^add_expense$'))
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.select_expense_category(update, context),
                                         pattern='^expense_'))
    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.add_custom_category(update, context),
                                         pattern='^add_custom_category_expense'))

    app.add_handler(
        CallbackQueryHandler(lambda update, context: handlers.show_transactions_button_handler(update, context),
                             pattern='^show_transactions'))

    app.add_handler(CallbackQueryHandler(lambda update, context: handlers.request_stats_start_date(update, context),
                                         pattern='^show_expense_stats$'))

    app.add_handler(
        CallbackQueryHandler(lambda update, context: handlers.add_reminder(update, context), pattern='^add_reminder$'))

    app.add_handler(
        CallbackQueryHandler(lambda update, context: handlers.handle_everyday_response(update, context),
                             pattern='^everyday_'))

    # обработчик сообщений он отвечает за все а не только за регистрацию
    app.add_handler(MessageHandler(filters.TEXT, lambda update, context: handlers.process_registration_text(update,
                                                                                                            context)))

    sc = AsyncIOScheduler()
    sc.add_job(handlers.send_reminders, 'interval', minutes=1)
    sc.start()

    database.create_db()

    print('Polling>>>')
    print('Schedule is working >>> ')
    app.run_polling()
