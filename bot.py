import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from data import PRICE_LIST, STOCK, UPCOMING, CONTACTS

# Логирование — показывает в терминале что происходит с ботом
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ──────────────────────────────────────────
# ГЛАВНОЕ МЕНЮ — кнопки которые видит пользователь
# ──────────────────────────────────────────

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 Прайс-лист",        callback_data="price")],
        [InlineKeyboardButton("📦 Остатки на складе",  callback_data="stock")],
        [InlineKeyboardButton("🚚 Ближайшие приходы",  callback_data="upcoming")],
        [InlineKeyboardButton("📞 Контакты",           callback_data="contacts")],
        [InlineKeyboardButton("📣 Наш канал",          url="https://t.me/frozen_fruits_opt_bot")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ──────────────────────────────────────────
# КОМАНДА /start — первое что видит пользователь
# ──────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = (
        f"Привет, {user_name}! 👋\n\n"
        "🍓 Добро пожаловать в бот оптовой торговли\n"
        "*замороженными фруктами и ягодами*\n\n"
        "Выбери что тебя интересует:"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

# ──────────────────────────────────────────
# ФОРМИРОВАНИЕ ТЕКСТОВ — берём данные из data.py
# и собираем красивые сообщения для пользователя
# ──────────────────────────────────────────

def build_price_text():
    lines = ["📋 *ПРАЙС-ЛИСТ*\n_(актуален на сегодня)_\n"]
    for item in PRICE_LIST:
        lines.append(
            f"{item['name']}\n"
            f"   💰 {item['price']} руб/кг   |   мин. заказ {item['min_order']} кг"
        )
    lines.append("\n_Цены указаны без НДС. При объёме от 500 кг — скидка, уточняйте у менеджера._")
    return "\n".join(lines)

def build_stock_text():
    lines = ["📦 *ОСТАТКИ НА СКЛАДЕ*\n"]
    for item in STOCK:
        if item["qty"] > 0:
            status = f"✅ {item['qty']} {item['unit']}"
        else:
            status = "❌ нет в наличии"
        lines.append(f"{item['name']}  —  {status}")
    lines.append("\n_Данные обновляются вручную. Для точной информации — свяжитесь с менеджером._")
    return "\n".join(lines)

def build_upcoming_text():
    if not UPCOMING:
        return "🚚 *БЛИЖАЙШИЕ ПРИХОДЫ*\n\nПока нет запланированных поставок."
    lines = ["🚚 *БЛИЖАЙШИЕ ПРИХОДЫ*\n"]
    for item in UPCOMING:
        lines.append(f"{item['name']}  —  {item['date']},  {item['qty']} кг")
    lines.append("\n_Даты ориентировочные. Уточняйте у менеджера._")
    return "\n".join(lines)

# Кнопка "Назад" — появляется под каждым разделом
back_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
])

# ──────────────────────────────────────────
# ОБРАБОТЧИК КНОПОК — реагирует на нажатия
# Смотрит какая кнопка нажата и показывает нужный текст
# ──────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu":
        await query.edit_message_text(
            "Выбери что тебя интересует:",
            reply_markup=main_menu_keyboard()
        )
    elif data == "price":
        await query.edit_message_text(
            build_price_text(),
            parse_mode="Markdown",
            reply_markup=back_button
        )
    elif data == "stock":
        await query.edit_message_text(
            build_stock_text(),
            parse_mode="Markdown",
            reply_markup=back_button
        )
    elif data == "upcoming":
        await query.edit_message_text(
            build_upcoming_text(),
            parse_mode="Markdown",
            reply_markup=back_button
        )
    elif data == "contacts":
        await query.edit_message_text(
            f"📞 КОНТАКТЫ\n{CONTACTS}",
            parse_mode=None,
            reply_markup=back_button
        )

# ──────────────────────────────────────────
# КОМАНДЫ АДМИНИСТРАТОРА
# Доступны только тебе — проверяем по ADMIN_ID
# ──────────────────────────────────────────

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /admin — показывает список доступных команд администратора
    if update.effective_user.id != ADMIN_ID:
        return
    text = (
        "🛠 *КОМАНДЫ АДМИНИСТРАТОРА*\n\n"
        "/broadcast текст — отправить сообщение в канал\n"
        "/post\\_to\\_channel — разместить приветственный пост с кнопкой в канале\n\n"
        "Чтобы обновить прайс или остатки:\n"
        "Открой файл `data.py` и измени цифры,\n"
        "затем перезапусти бота."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /broadcast текст — отправляет сообщение в канал от имени бота
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast ваше сообщение\n\n"
            "Пример: /broadcast 🍒 Вишня поступила! 1000 кг по 160 руб/кг"
        )
        return
    message = " ".join(context.args)
    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"📢 {message}",
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Сообщение отправлено в канал!")


async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /post_to_channel — размещает красивый пост с кнопкой-ссылкой на бота
    # Используй когда хочешь привлечь подписчиков канала в бота
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа.")
        return

    text = (
        "🍓 *Замороженные фрукты и ягоды оптом*\n\n"
        "Работаем напрямую с производителями\n\n"
        "📋 Актуальный прайс-лист\n"
        "📦 Остатки на складе\n"
        "🚚 Ближайшие поступления\n"
        "📞 Контакты менеджера\n\n"
        "👇 Всё это в нашем боте:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Открыть бота", url="https://t.me/frozen_fruits_opt_bot")]
    ])

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await update.message.reply_text("✅ Пост с кнопкой отправлен в канал!")


# ──────────────────────────────────────────
# ОБРАБОТЧИК ЛЮБОГО ТЕКСТА
# Если пользователь пишет что-то кроме команд — напоминаем про кнопки
# ──────────────────────────────────────────

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используй кнопки меню 👇",
        reply_markup=main_menu_keyboard()
    )


# ──────────────────────────────────────────
# ЗАПУСК БОТА
# Регистрируем все обработчики и запускаем бесконечный цикл
# ──────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команды пользователя
    app.add_handler(CommandHandler("start",            start))

    # Команды администратора
    app.add_handler(CommandHandler("admin",            admin_help))
    app.add_handler(CommandHandler("broadcast",        admin_broadcast))
    app.add_handler(CommandHandler("post_to_channel",  post_to_channel))

    # Кнопки
    app.add_handler(CallbackQueryHandler(button_handler))

    # Любой текст не являющийся командой
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    print("✅ Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()