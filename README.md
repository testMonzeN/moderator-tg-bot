# Karadevfacekid Bot 🤖

Telegram-бот для модерации чата, проверки сообщений на маты, приветствия новых пользователей и управления подозрительными пользователями.

---
## Основные функции

- **Проверка сообщений на маты**: Бот автоматически удаляет сообщения с запрещёнными словами и отправляет предупреждение пользователю.
- **Приветствие новых пользователей**: Бот приветствует новых участников группы.
- **Управление подозрительными пользователями**:
  - Если подозрительный пользователь заходит в группу, бот задаёт вопрос админам: "Выгнать ли пользователя @username? (да/нет)".
  - Если админ выбирает "Да", бот банит пользователя на 3 дня.
  - Если админ выбирает "Нет", бот оставляет пользователя под наблюдением.
- **Статистика матов**: Бот ведёт статистику использования матов для каждого пользователя.
- **Управление ботом**: Включение/отключение бота, перезагрузка списка запрещённых слов, очистка логов.


---
## Команды

### Для всех пользователей
- `/help` — показать список доступных команд.
- `/stat @username` / `/statistics @username` - показать статистику человека

### Для администраторов
- `/mode enable` — включить бота.
- `/mode disable` — отключить бота.
- `/status` — показать текущий статус бота.
- `/reload` — перезагрузить список запрещённых слов.
- `/hist @username [N]` — показать статистику матов для пользователя (по умолчанию N=5).
- `/clear [N]` — удалить последние N сообщений.
- `/clearlog` — очистить логи с матами.
- `/enemy add @username` — добавить пользователя в список подозрительных.

---
## Установка и запуск

1. Убедитесь, что у вас установлен Python 3.8 или выше.
2. Установите необходимые зависимости:
   ```bash
   pip install python-telegram-bot
   ```
3. Создайте файл badwords.txt и добавьте туда запрещённые слова (каждое слово на новой строке).
4. Создайте бота через @BotFather и получите токен.
5. Замените "ВАШ_ТЕЛЕГРАМ_ТОКЕН" в файле main.py на ваш токен.
6. Запустите бота:
   ```bash
   python main.py
   ```
---

## Настройка

### Добавление подозрительных пользователей:
- Используйте команду /enemy add @username, чтобы добавить/удалить пользователя в список подозрительных. 
Пример: /enemy add @username.
Пример: /enemy delete all.
Пример: /enemy delete @username.
- Перезагрузка списка запрещённых слов:
Используйте команду /reload, чтобы обновить список слов из файла badwords.txt
- Отчистка логов:
Используйте команду /clearlog => нажмите на соответствующую кнопку.

---
## Примеры использования
1. Проверка матов:
- Пользователь пишет: "Это тестовое сообщение с матом."
- Бот удаляет сообщение и отвечает: "@username, у нас запрещены такие выражения! ⚠️"
2. Приветствие новых пользователей:
- Новый пользователь заходит в группу.
- Бот приветствует: "Добро пожаловать, @username! 🎉"
3. Управление подозрительными пользователями:
- Подозрительный пользователь @enemyuser заходит в группу.
- Бот отправляет: "⚠️ Выгнать ли пользователя @enemyuser? (да/нет)"
- Админ нажимает "Да".
- Бот банит пользователя на 3 дня и пишет: "⛔ Пользователь забанен на 3 дня."
4. Статистика матов:
- Админ пишет: /hist @username 5
- Бот отвечает:
````
📊 @username использовал(а) маты 3 раз(а).
Последние сообщения с матами:
• [2023-12-31 23:59:59] Это тестовое сообщение с матом.
• [2024-01-01 00:00:01] Ещё одно сообщение с матом.
````
