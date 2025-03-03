from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from datetime import datetime, timedelta
import re
import random
import os


class Karadevfacekid:
    def __init__(self, token: str, bad_words_file: str = "badwords.txt", log_file: str = "violations.log"):
        self.TOKEN = token
        self.BAD_WORDS_FILE = bad_words_file
        self.LOG_FILE = log_file
        self.BAD_WORDS = self.load_bad_words()
        self.GREETINGS = [
            "Добро пожаловать, {username}! 🎉",
            "Привет, {username}! Рады видеть тебя в нашей группе! 😊",
            "{username}, добро пожаловать в наш уютный чат! 🥳"
        ]
        self.WARNINGS = [
            "@{username}, у нас запрещены такие выражения! ⚠️",
            "Эй, @{username}, следи за языком! 🚫",
            "@{username}, это слово запрещено в нашем чате!",
            "Ой, @{username}, так нельзя выражаться! 🙊"
        ]

        self.BAN_DURATIONS = {
            "suspicious_user": 3,
            "exceed_warning_limit": 1,
        }
        self.BAN_DURATION = 1
        self.violations = {}
        self.violation_messages = {}
        self.suspicious_users = {}
        self.message_count = {}
        self.warning_count = {}

        self.WARNING_LIMIT = 5

        self.is_enabled = True
        self.total_check_mode = False


    def load_bad_words(self):
        try:
            with open(self.BAD_WORDS_FILE, "r", encoding="utf-8") as file:
                words = [line.strip().lower() for line in file if line.strip()]
                return words
        except Exception as e:
            print(f"🚨 Ошибка: {e}")
            return []

    def contains_bad_words(self, text: str) -> bool:
        try:
            clean_text = text.lower()

            for word in self.BAD_WORDS:
                if self.total_check_mode:
                    pattern = ""
                    for char in word:
                        if char.isalpha():
                            pattern += f"{char}+[^а-я]*"
                        else:
                            pattern += re.escape(char)
                    pattern = pattern.rstrip("[^а-я]*")
                else:
                    pattern = re.sub(r"(\w)", r"\1+", word)
                if re.search(pattern, clean_text):
                    return True
            return False
        except Exception as e:
            print(f"🚨 Ошибка проверки: {e}")
            return False


    async def total_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update, context):
            await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды.")
            return
        try:
            action = context.args[0].lower() if context.args else None

            if action == "on":
                self.total_check_mode = True
                await update.message.reply_text(
                    "✅ Режим тотальной проверки включён. Бот будет реагировать на слова с пробелами, дефисами и другими символами.")
            elif action == "off":
                self.total_check_mode = False
                await update.message.reply_text(
                    "⛔ Режим тотальной проверки выключен. Бот будет реагировать только на слова без пробелов и дефисов.")
            elif action == "status":
                status = "включён.\n 🤝💪Да здравствует Северная Корея!💪🤝\n 👋 Привет Ким Чен Ын! ❤" if self.total_check_mode else "выключен. \n Спите спокойно."
                await update.message.reply_text(f"📊 Режим тотальной проверки: {status}")
            else:
                await update.message.reply_text(
                    "⚠️ Используйте команду так: /totalcheck on, /totalcheck off или /totalcheck status")
        except Exception as e:
            print(f"🚨 Ошибка: {e}")
            await update.message.reply_text("⚠️ Произошла ошибка при выполнении команды.")

    def log_violation(self, username: str, text: str):
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] @{username}: {text}\n")
        except Exception as e:
            print(f"⚠️ Ошибка записи в лог: {e}")


    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_enabled:
            return

        if not update.message or not update.message.text:
            return

        user = update.message.from_user

        if user.username and user.username.lower() in [u.lower() for u in self.suspicious_users]:
            try:
                await update.message.delete()
                await self._ban_user(context, update.message.chat_id, user)
                return
            except error.BadRequest as e:
                print(f"⚠️ Ошибка удаления сообщения: {e}")
        user = update.message.from_user
        text = update.message.text

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.message_count[user.username] = self.message_count.get(user.username, 0) + 1
        if self.contains_bad_words(text):
            try:
                warning = random.choice(self.WARNINGS).format(username=user.username)
                await update.message.reply_text(warning)

                self.log_violation(user.username, text)

                self.warning_count[user.username] = self.warning_count.get(user.username, 0) + 1

                if self.warning_count[user.username] >= self.WARNING_LIMIT:
                    print(self.warning_count[user.username])
                    await context.bot.ban_chat_member(
                        chat_id=update.message.chat_id,
                        user_id=user.id,
                        until_date=datetime.now() + timedelta(days=self.BAN_DURATIONS['exceed_warning_limit']))
                    await update.message.reply_text(
                        f"⛔ Пользователь @{user.username} был забанен на {self.BAN_DURATIONS['exceed_warning_limit']} дня за превышение лимита предупреждений."
                    )
                    self.warning_count[user.username] = 0
                else:
                    warnings_left = self.WARNING_LIMIT - self.warning_count[user.username]
                    await update.message.reply_text(
                        f"⚠️ @{user.username}, у вас {self.warning_count[user.username]}/{self.WARNING_LIMIT} предупреждений. "
                        f"Осталось {warnings_left} предупреждений до бана."
                    )

                if user.username in self.violations:
                    self.violations[user.username] += 1
                    self.violation_messages[user.username].append((timestamp, text))
                else:
                    self.violations[user.username] = 1
                    self.violation_messages[user.username] = [(timestamp, text)]
            except Exception as e:
                print(f"🚨 Ошибка при обработке сообщения: {e}")

    async def greet_new_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_enabled:
            return

        for member in update.message.new_chat_members:
            if member.username in self.suspicious_users:
                try:
                    await context.bot.ban_chat_member(
                        chat_id=update.message.chat_id,
                        user_id=member.id,
                        until_date=datetime.now() + timedelta(days=self.BAN_DURATIONS['suspicious_user']))
                    await update.message.reply_text(
                        f"⛔ Пользователь @{member.username} был забанен на {self.BAN_DURATIONS['suspicious_user']}, так как находится в списке подозрительных."
                    )
                except Exception as e:
                    print(f"🚨 Ошибка при бане пользователя: {e}")
                    await update.message.reply_text("⚠️ Не удалось забанить пользователя.")
            else:
                greeting = random.choice(self.GREETINGS).format(username=member.username)
                await update.message.reply_text(greeting)


    async def reload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.BAD_WORDS = self.load_bad_words()
        await update.message.reply_text(f"♻️ Обновлено! Запрещенных слов: {len(self.BAD_WORDS)}")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            parts = update.message.text.split()
            username = parts[1].replace("@", "")
            limit = int(parts[2]) if len(parts) > 2 else 5

            if username in self.violations:
                count = self.violations[username]
                messages = self.violation_messages.get(username, [])
                last_messages = messages[-limit:]

                response = f"📊 @{username} использовал(а) маты {count} раз(а).\n"
                response += "Последние сообщения с матами:\n"
                response += "\n".join(f"• [{timestamp}] {msg}" for timestamp, msg in last_messages)

                await update.message.reply_text(response)
            else:
                await update.message.reply_text(f"📊 @{username} не использовал(а) маты.")
        except IndexError:
            await update.message.reply_text("⚠️ Используйте команду так: /hist @username [N]")
        except ValueError:
            await update.message.reply_text("⚠️ N должно быть числом.")

    async def mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            mode = update.message.text.split()[1].lower()
            if mode == "enable":
                self.is_enabled = True
                await update.message.reply_text("✅ Бот включён. Все функции активны.")
            elif mode == "disable":
                self.is_enabled = False
                await update.message.reply_text("⛔ Бот отключён. Все функции неактивны.")
            else:
                await update.message.reply_text("⚠️ Используйте команду так: /mode enable или /mode disable")
        except IndexError:
            await update.message.reply_text("⚠️ Используйте команду так: /mode enable или /mode disable")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        status = "✅ Включён" if self.is_enabled else "⛔ Отключён"
        await update.message.reply_text(f"Статус бота: {status}")

    async def set_warning_limit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update, context):
            await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды.")
            return

        try:
            new_limit = int(context.args[0])
            if new_limit < 1:
                await update.message.reply_text("⚠️ Лимит предупреждений должен быть больше 0.")
                return

            self.WARNING_LIMIT = new_limit
            await update.message.reply_text(f"✅ Лимит предупреждений изменён на {new_limit}.")
        except (IndexError, ValueError):
            await update.message.reply_text("⚠️ Используйте команду так: /limit <число>.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Включить бота", callback_data="mode_enable")],
            [InlineKeyboardButton("Отключить бота", callback_data="mode_disable")],
            [InlineKeyboardButton("Статус бота", callback_data="status")],
            [InlineKeyboardButton("Очистить логи", callback_data="clearlog")],
            [InlineKeyboardButton("Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📜 Выберите действие:", reply_markup=reply_markup)

    async def enemy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin(update, context):
            await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды.")
            return

        try:
            parts = update.message.text.split()
            if len(parts) < 2:
                await update.message.reply_text(
                    "⚠️ Используйте команду так: /enemy add @username, /enemy list, /enemy delete all, /enemy delete @username")
                return

            action = parts[1].lower()

            if action == "add":
                if len(parts) < 3:
                    await update.message.reply_text("⚠️ Используйте команду так: /enemy add @username")
                    return
                username = parts[2].replace("@", "")
                self.suspicious_users[username] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await update.message.reply_text(f"✅ Пользователь @{username} добавлен в список подозрительных.")

            elif action == "list":
                if not self.suspicious_users:
                    await update.message.reply_text("✅ Список подозрительных пользователей пуст.")
                else:
                    response = "📜 Список подозрительных пользователей:\n"
                    for username, date_added in self.suspicious_users.items():
                        response += f"• @{username} (добавлен: {date_added})\n"
                    await update.message.reply_text(response)

            elif action == "delete":
                if len(parts) < 3:
                    await update.message.reply_text(
                        "⚠️ Используйте команду так: /enemy delete all или /enemy delete @username")
                    return

                target = parts[2].lower()
                if target == "all":
                    self.suspicious_users.clear()
                    await update.message.reply_text("✅ Все подозрительные пользователи удалены из списка.")
                else:
                    username = target.replace("@", "")
                    if username in self.suspicious_users:
                        del self.suspicious_users[username]
                        await update.message.reply_text(f"✅ Пользователь @{username} удалён из списка подозрительных.")
                    else:
                        await update.message.reply_text(
                            f"⚠️ Пользователь @{username} не найден в списке подозрительных.")

            else:
                await update.message.reply_text(
                    "⚠️ Неизвестное действие. Используйте: /enemy add, /enemy list, /enemy delete")

        except Exception as e:
            print(f"🚨 Ошибка: {e}")
            await update.message.reply_text("⚠️ Произошла ошибка при выполнении команды.")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "mode_enable":
            self.is_enabled = True
            await query.edit_message_text("✅ Бот включён. Все функции активны.")
        elif query.data == "mode_disable":
            self.is_enabled = False
            await query.edit_message_text("⛔ Бот отключён. Все функции неактивны.")
        elif query.data == "status":
            status = "✅ Включён" if self.is_enabled else "⛔ Отключён"
            await query.edit_message_text(f"Статус бота: {status}")
        elif query.data == "clearlog":
            try:
                if os.path.exists(self.LOG_FILE):
                    with open(self.LOG_FILE, "w", encoding="utf-8") as f:
                        f.write("")
                    self.violations = {}
                    self.violation_messages = {}
                    await query.edit_message_text("🗑️ Логи с матами очищены.")
                else:
                    await query.edit_message_text("⚠️ Логи с матами отсутствуют.")
            except Exception as e:
                print(f"🚨 Ошибка при очистке логов: {e}")
                await query.edit_message_text("⚠️ Произошла ошибка при очистке логов.")
        elif query.data == "help":
            help_text = """
                📜 Доступные команды:

                • /mode enable — включить бота.
                • /mode disable — отключить бота.
                • /status — показать текущий статус бота.
                • /reload — перезагрузить список запрещённых слов.
                • /hist @username [N] — показать статистику матов для пользователя (по умолчанию N=5).
                • /clearlog — очистить логи с матами.
                • /enemy add @username — добавить пользователя в список подозрительных.
                • /enemy list — показать список подозрительных пользователей.
                • /enemy delete all — удалить всех подозрительных пользователей.
                • /enemy delete @username — удалить конкретного пользователя из списка.
                • /statistics @username — показать статистику пользователя.
                • /stat @username — алиас для /statistics.
                • /help — показать это сообщение.
            """
            await query.edit_message_text(help_text)

    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        admins = await context.bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)


    async def statistics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            parts = update.message.text.split()
            if len(parts) < 2:
                await update.message.reply_text("⚠️ Используйте команду так: /statistics @username или /stat @username")
                return

            username = parts[1].replace("@", "")
            chat_id = update.message.chat_id

            user_status = await self.get_user_status(chat_id, username, context)
            message_count = self.message_count.get(username, 0)
            mat_count = self.violations.get(username, 0)
            reputation = self.calculate_reputation(message_count, mat_count)
            is_dangerous = username in self.suspicious_users

            response = f"📊 Статистика @{username}:\n"
            response += f"- Кол-во сообщений: {message_count}\n"
            response += f"- Кол-во матов: {mat_count}\n"
            response += f"- Репутация: {reputation}\n"
            response += f"- Положение в чате: {user_status}\n"
            response += f"- Опасный ли пользователь: {'Да' if is_dangerous else 'Нет'}\n"

            await update.message.reply_text(response)
        except Exception as e:
            print(f"🚨 Ошибка: {e}")
            await update.message.reply_text("⚠️ Произошла ошибка при получении статистики.")

    async def get_user_status(self, chat_id: int, username: str, context: ContextTypes.DEFAULT_TYPE) -> str:
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            for admin in admins:
                if admin.user.username == username:
                    return "Администратор"
            return "Обычный участник"
        except Exception as e:
            print(f"🚨 Ошибка при получении статуса пользователя: {e}")
            return "Неизвестно"

    def calculate_reputation(self, message_count: int, mat_count: int) -> str:
        if message_count == 0:
            return "Нет данных"
        ratio = (message_count - mat_count) / message_count
        if ratio >= 0.9:
            return "Отличная"
        elif ratio >= 0.7:
            return "Хорошая"
        elif ratio >= 0.5:
            return "Средняя"
        else:
            return "Плохая"

    def run(self):
        app = ApplicationBuilder().token(self.TOKEN).build()

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.greet_new_members))
        app.add_handler(CommandHandler("reload", self.reload_command))
        app.add_handler(CommandHandler("clearlog", self.help_command))
        app.add_handler(CommandHandler("hist", self.history_command))
        app.add_handler(CommandHandler("mode", self.mode_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("enemy", self.enemy_command))
        app.add_handler(CommandHandler("statistics", self.statistics_command))
        app.add_handler(CommandHandler("stat", self.statistics_command))
        app.add_handler(CommandHandler("totalcheck", self.total_check_command))
        app.add_handler(CommandHandler("tc", self.total_check_command))
        app.add_handler(CommandHandler("limit", self.set_warning_limit_command))
        app.add_handler(CallbackQueryHandler(self.button_handler))

        print("🤖 Бот запущен!")
        app.run_polling()


if __name__ == "__main__":
    bot = Karadevfacekid(token="")
    bot.run()
