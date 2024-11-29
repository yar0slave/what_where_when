HELP_TEXT = (
    "📜 Доступные команды:\n\n"
    "🎮 Начало игры:\n"
    "/start - начать регистрацию\n"
    "/join - присоединиться к игре\n"
    "/finish_reg - закончить регистрацию\n\n"
    "/stat - статистика\n\n"
    "🎯 Во время игры:\n"
    "/choose @username - выбрать отвечающего (только для капитана)\n"
    "/answer текст - дать ответ на вопрос"
)

ONLY_CAPTAIN_TEXT = "❌ Только капитан может выбирать отвечающего!"

GAME_IN_PROGRESS_TEXT = "❌ Игра уже в процессе регистрации или идет"

START_TEXT = "🎲 Игра начинается! Приготовьтесь к первому вопросу..."

RULES_TEXT = (
    "🎮 Правила игры «Что? Где? Когда?»:\n\n"
    "1️⃣ Игра состоит 3 из  раундов\n"
    "2️⃣ В каждом раунде команде задается вопрос\n"
    "3️⃣ У команды есть 1 минута на обсуждение\n"
    "4️⃣ После обсуждения капитан выбирает отвечающего командой "
    "/choose @username\n"
    "5️⃣ За правильный ответ команда получает 1 балл\n"
    "6️⃣ За неправильный ответ или отсутствие ответа балл получает бот\n"
    "ответа балл получает бот\n\n"
    "👑 Капитан команды: @{captain}\n"
    "🎯 Количество раундов: {rounds}"
)

CAPTAIN_NOT_FOUND_TEXT = "Капитан не найден"

QUESTIONS_EMPTY_TEXT = "❌ Закончились вопросы! Игра завершается досрочно."
ROUND_ANNOUNCEMENT_TEMPLATE = (
    "🎯 Раунд {round_number}\n"
    "💭 Вопрос: {question_text}\n\n"
    "⏳ Время на обсуждение: {discussion_time} секунд"
)
DISCUSSION_WARNING_TEXT = "⚠️ 10 секунд до окончания обсуждения!"
CHOOSE_PLAYER_TEXT = (
    "👑 @{captain}, выберите отвечающего командой /choose @username"
)
PLAYER_NOT_FOUND_TEXT = "❌ Выбранный игрок не участвует в игре!"
PLAYER_ANSWER_PROMPT = (
    "🎯 @{player}, ваш ответ? Формат ответа: /answer ваш_ответ"
)
NOT_YOUR_TURN_TEXT = "❌ Сейчас не ваша очередь отвечать!"
CORRECT_ANSWER_TEXT = "✅ Правильный ответ! Команда получает балл."
WRONG_ANSWER_TEXT = "❌ Неправильно! Правильный ответ: {correct_answer}"
SCORE_TEXT = "📊 Счет: Команда {team_score} - {bot_score} Бот"
FINAL_WIN_TEXT = (
    "🏆 Поздравляем! Команда знатоков победила!\n"
    "Финальный счет: {team_score} - {bot_score}"
)
FINAL_LOSE_TEXT = (
    "😔 Команда знатоков проиграла.\n"
    "Финальный счет: {team_score} - {bot_score}"
)
FINAL_DRAW_TEXT = (
    "🤝 Ничья! Отличная игра!\n" "Финальный счет: {team_score} - {bot_score}"
)

REGISTRATION_START_TEXT = (
    "🎮 Начинается регистрация на игру «Что? Где? Когда?»\n\n"
    "📝 Чтобы присоединиться к игре, отправьте команду /join\n"
    "ℹ️ Требуется до {max_players} игроков\n"
    "❌ Для завершения регистрации администратор может отправить /finish_reg"
)
REGISTRATION_CLOSED_TEXT = "❌ Регистрация сейчас закрыта"
MAX_PLAYERS_REACHED_TEXT = "❌ Достигнуто максимальное количество игроков"
ALREADY_REGISTERED_TEXT = "❌ Вы уже зарегистрированы"
PLAYER_REGISTERED_TEXT = (
    "✅ @{username} зарегистрирован!\n"
    "👥 Количество игроков: {current_players}/{max_players}"
)
REGISTRATION_ALREADY_CLOSED_TEXT = "❌ Регистрация уже закрыта"
REGISTRATION_FINISHED_TEXT = (
    "✅ Регистрация завершена!\n\n"
    "Состав команды:\n{players_list}"
    "\n\nВсего игроков: {total_players}"
)

STATISTICS_TEXT = (
    "😄 Прошлые игроки набрали: {score_team} очков. Сможешь столько же?"
)

TOO_EARLY_TO_CHOOSE_TEXT = "❌ Пожалуйста, подождите окончания времени обсуждения перед выбором игрока."
TOO_EARLY_TO_ANSWER_TEXT = "❌ Пожалуйста, дождитесь, пока капитан выберет отвечающего."
