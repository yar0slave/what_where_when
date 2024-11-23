from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from app.base.base_accessor import BaseAccessor
from app.store.database.models import AskedQuestions, Game, Questions, Users


class QuizAccessor(BaseAccessor):
    async def create_question(
        self, question_text: str, answer_text: str
    ) -> Questions:
        async with self.app.database.session() as session:
            try:
                question = Questions(question=question_text, answer=answer_text)
                session.add(question)
                await session.commit()  # Фиксируем изменения
            except IntegrityError as e:
                await session.rollback()  # Откатываем транзакцию при ошибке
                self.app.logger.error("Ошибка при создании вопроса: %s", str(e))
                raise
            else:
                return question

    async def get_random_unasked_question(
        self, chat_id: int
    ) -> Questions | None:
        async with self.app.database.session() as session:
            try:
                subquery = select(AskedQuestions.question).where(
                    AskedQuestions.chat_id == chat_id
                )
                query = (
                    select(Questions)
                    .where(Questions.id.not_in(subquery))
                    .order_by(func.random())
                    .limit(1)
                )
                result = await session.execute(query)
                question = result.scalar_one_or_none()
            except Exception as e:
                self.logger.error(
                    "Ошибка при получении"
                    " случайного вопроса для chat_id=%s: %s",
                    chat_id,
                    e,
                )
                raise
            else:
                if question:
                    self.logger.info(
                        "Случайный вопрос для chat_id=%s получен: %s",
                        chat_id,
                        question.question,
                    )
                else:
                    self.logger.info(
                        "Все вопросы уже заданы для chat_id=%s.", chat_id
                    )
                return question

    async def mark_question_as_asked(
        self, chat_id: int, question_id: int
    ) -> None:
        async with self.app.database.session() as session:
            try:
                asked_question = AskedQuestions(
                    chat_id=chat_id, question=question_id
                )
                session.add(asked_question)
                await session.commit()

                self.logger.info(
                    "Вопрос с id=%s отмечен как заданный для chat_id=%s.",
                    question_id,
                    chat_id,
                )
            except Exception as e:
                await session.rollback()
                self.logger.error(
                    "Ошибка при отметке вопроса с id=%s для chat_id=%s: %s",
                    question_id,
                    chat_id,
                    e,
                )
                raise

    async def check_answer(self, question_id: int, user_answer: str) -> bool:
        async with self.app.database.session() as session:
            try:
                query = select(Questions.answer).where(
                    Questions.id == question_id
                )
                result = await session.execute(query)
                correct_answer = result.scalar_one_or_none()

                if correct_answer is None:
                    self.logger.error("Вопрос с id=%s не найден.", question_id)
                    return False

                is_correct = (
                    correct_answer.strip().lower()
                    == user_answer.strip().lower()
                )
                self.logger.info(
                    "Ответ %s для вопроса id=%s.",
                    "правильный" if is_correct else "неправильный",
                    question_id,
                )
            except Exception as e:
                self.logger.error(
                    "Ошибка при проверке ответа на вопрос id=%s: %s",
                    question_id,
                    e,
                )
                raise
            else:
                return is_correct


class UserAccessor(BaseAccessor):
    async def join_user(
        self, user_id: int, username: str, chat_id: int
    ) -> Users:
        async with self.app.database.session() as session:
            try:
                user = Users(id=user_id, user_id=username, chat_id=chat_id)

                session.add(user)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                self.logger.error(
                    "Ошибка при добавлении пользователя"
                    " с id=%s, username=%s, chat_id=%s: %s",
                    user_id,
                    username,
                    chat_id,
                    e,
                )
                raise
            else:
                return user

    async def get_users_by_chat_id(self, chat_id: int) -> list[str]:
        async with self.app.database.session() as session:
            try:
                query = select(Users.user_id).where(Users.chat_id == chat_id)
                result = await session.execute(query)
                usernames = result.scalars().all()

            except Exception as e:
                self.logger.error(
                    "Ошибка при получении никнеймов"
                    " пользователей для chat_id=%s: %s",
                    chat_id,
                    e,
                )
                raise
            else:
                return usernames

    async def delete_users_by_chat_id(self, chat_id: int) -> None:
        async with (
            self.app.database.session() as session
        ):  # Используем AsyncSession
            try:
                # Создаём запрос DELETE
                query = delete(Users).where(Users.chat_id == chat_id)

                # Выполняем запрос
                await session.execute(query)

                # Фиксируем изменения
                await session.commit()

                self.logger.info(
                    "Все пользователи с chat_id=%s успешно удалены.", chat_id
                )
            except IntegrityError as e:
                await session.rollback()  # Откат транзакции при ошибке
                self.logger.error(
                    "Ошибка целостности данных "
                    "при удалении пользователей с chat_id=%s: %s",
                    chat_id,
                    e,
                )
                raise
            except Exception as e:
                await (
                    session.rollback()
                )  # Откат транзакции при любой другой ошибке
                self.logger.error(
                    "Общая ошибка при удалении пользователей с chat_id=%s: %s",
                    chat_id,
                    e,
                )
                raise


class GameAccessor(BaseAccessor):
    async def create_or_update_game(self, **kwargs) -> Game:
        async with self.app.database.session() as session:
            try:
                code_of_chat = kwargs.get(
                    "code_of_chat", None
                )  # Проверяем наличие code_of_chat
                if code_of_chat is None:
                    raise ValueError(
                        "Поле code_of_chat обязательно для создания записи"
                    )

                # Пытаемся найти существующую запись
                query = select(Game).where(Game.code_of_chat == code_of_chat)
                result = await session.execute(query)
                game = result.scalar_one_or_none()

                if game:
                    # Обновляем только переданные параметры
                    for key, value in kwargs.items():
                        if hasattr(game, key):
                            setattr(game, key, value)
                else:
                    # Создаём новую запись, если не найдено
                    game = Game(**kwargs)
                    session.add(game)

                await session.commit()

            except IntegrityError as e:
                await session.rollback()
                self.logger.error("Ошибка при работе с таблицей game: %s", e)
                raise
            except Exception as e:
                await session.rollback()
                self.logger.error("Общая ошибка: %s", e)
                raise
            else:
                return game

    async def get_all_code_of_chat(self) -> list[int]:
        async with self.app.database.session() as session:
            try:
                # Выполняем SELECT для получения всех code_of_chat
                query = select(Game.code_of_chat)
                result = await session.execute(query)
                code_of_chat_list = (
                    result.scalars().all()
                )  # Получаем список значений
            except Exception as e:
                self.logger.error("Ошибка при получении code_of_chat: %s", e)
                raise
            else:
                return code_of_chat_list

    async def is_captain_set(self, code_of_chat: int) -> bool:
        async with self.app.database.session() as session:
            try:
                # Запрос для получения captain_id по code_of_chat
                query = select(Game.captain_id).where(
                    Game.code_of_chat == code_of_chat
                )
                result = await session.execute(query)
                captain_id = (
                    result.scalar_one_or_none()
                )  # Получаем значение или None

                return bool(
                    captain_id
                )  # Возвращаем True, если captain_id задан, иначе False

            except Exception as e:
                self.logger.error(
                    "Ошибка при проверке captain_id для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise

    async def get_game_by_chat_id(self, code_of_chat: int) -> Game | None:
        async with self.app.database.session() as session:
            try:
                # Создаём запрос для поиска игры по code_of_chat
                query = select(Game).where(Game.code_of_chat == code_of_chat)
                result = await session.execute(query)
                game = (
                    result.scalar_one_or_none()
                )  # Возвращает объект или None, если запись отсутствует

                if game:
                    self.logger.info(
                        "Игра с code_of_chat=%s найдена.", code_of_chat
                    )
                else:
                    self.logger.info(
                        "Игра с code_of_chat=%s не найдена.", code_of_chat
                    )
            except Exception as e:
                self.logger.error(
                    "Ошибка при получении игры с code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise
            else:
                return game

    async def get_round_number_by_chat_id(self, code_of_chat: int) -> int:
        async with self.app.database.session() as session:
            try:
                query = select(Game.round_number).where(
                    Game.code_of_chat == code_of_chat
                )
                result = await session.execute(query)
                round_number = result.scalar_one_or_none()

                if round_number is not None:
                    self.logger.info(
                        "Текущий номер раунда для code_of_chat=%s: %s",
                        code_of_chat,
                        round_number,
                    )
                else:
                    round_number = 0
                    self.logger.info(
                        "Игра с code_of_chat=%s не найдена.", code_of_chat
                    )

            except Exception as e:
                self.logger.error(
                    "Ошибка при получении номера"
                    " раунда для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
            else:
                return round_number

    async def set_round_number(
        self, code_of_chat: int, round_number: int
    ) -> None:
        async with self.app.database.session() as session:
            try:
                # Проверяем, существует ли запись с указанным code_of_chat
                query = select(Game).where(Game.code_of_chat == code_of_chat)
                result = await session.execute(query)
                game = result.scalar_one_or_none()

                if game is None:
                    self.logger.error(
                        "Игра с code_of_chat=%s не найдена.", code_of_chat
                    )
                    raise Exception

                # Обновляем номер раунда
                update_query = (
                    update(Game)
                    .where(Game.code_of_chat == code_of_chat)
                    .values(round_number=round_number)
                )
                await session.execute(update_query)
                await session.commit()

                self.logger.info(
                    "Номер раунда для code_of_chat=%s установлен на %s.",
                    code_of_chat,
                    round_number,
                )
            except Exception as e:
                await session.rollback()
                self.logger.error(
                    "Ошибка при установке"
                    " номера раунда для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise

    async def assign_question_to_game(
        self, question_text: str, code_of_chat: int
    ) -> None:
        async with self.app.database.session() as session:
            try:
                # Находим question_id по тексту вопроса
                query = select(Questions.id).where(
                    Questions.question == question_text
                )
                result = await session.execute(query)
                question_id = result.scalar_one_or_none()

                # Обновляем question_id в таблице `Game`
                update_query = (
                    update(Game)
                    .where(Game.code_of_chat == code_of_chat)
                    .values(question_id=question_id)
                )
                await session.execute(update_query)
                await session.commit()

                self.logger.info(
                    "Вопрос с id=%s назначен игре с code_of_chat=%s.",
                    question_id,
                    code_of_chat,
                )
            except Exception as e:
                await session.rollback()
                self.logger.error(
                    "Ошибка при назначении вопроса игре с code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )

    async def get_respondent_id_by_chat_id(
        self, code_of_chat: int
    ) -> str | bool:
        async with self.app.database.session() as session:
            try:
                # Запрос для получения respondent_id
                query = select(Game.respondent_id).where(
                    Game.code_of_chat == code_of_chat
                )
                result = await session.execute(query)
                respondent_id = result.scalar_one_or_none()

                if respondent_id is not None:
                    self.logger.info(
                        "respondent_id для code_of_chat=%s: %s",
                        code_of_chat,
                        respondent_id,
                    )
                    return respondent_id
            except Exception as e:
                self.logger.error(
                    "Ошибка при получении "
                    "respondent_id для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise

    async def get_question_by_chat_id(
        self, code_of_chat: int
    ) -> Questions | None:
        async with self.app.database.session() as session:
            try:
                # Запрос с присоединением таблицы Questions
                query = (
                    select(Questions)
                    .join(Game, Game.question_id == Questions.id)
                    .where(Game.code_of_chat == code_of_chat)
                )
                result = await session.execute(query)
                question = result.scalar_one_or_none()

                if question:
                    self.logger.info(
                        "Вопрос для code_of_chat=%s: %s",
                        code_of_chat,
                        question.question,
                    )
                else:
                    self.logger.info(
                        "Вопрос для code_of_chat=%s отсутствует.", code_of_chat
                    )

            except Exception as e:
                self.logger.error(
                    "Ошибка при получении вопроса для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise
            else:
                return question

    async def get_points_awarded_by_chat_id(self, code_of_chat: int) -> int:
        async with self.app.database.session() as session:
            try:
                # Запрос для получения points_awarded
                query = select(Game.points_awarded).where(
                    Game.code_of_chat == code_of_chat
                )
                result = await session.execute(query)
                points_awarded = result.scalar_one_or_none()

                if points_awarded:
                    self.logger.info(
                        "points_awarded для code_of_chat=%s: %s",
                        code_of_chat,
                        points_awarded,
                    )
                else:
                    self.logger.info(
                        "points_awarded для code_of_chat=%s отсутствует.",
                        code_of_chat,
                    )
                    points_awarded = 0

            except Exception as e:
                self.logger.error(
                    "Ошибка при получении points_awarded"
                    " для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise
            else:
                return points_awarded

    async def clear_game_users_and_asked_questions(
        self, code_of_chat: int
    ) -> None:
        async with self.app.database.session() as session:
            try:
                # Удаляем связанные записи из asked_questions
                delete_asked_questions_query = delete(AskedQuestions).where(
                    AskedQuestions.chat_id == code_of_chat
                )
                await session.execute(delete_asked_questions_query)

                # Удаляем связанные записи из users
                delete_users_query = delete(Users).where(
                    Users.chat_id == code_of_chat
                )
                await session.execute(delete_users_query)

                # Удаляем запись из game
                delete_game_query = delete(Game).where(
                    Game.code_of_chat == code_of_chat
                )
                await session.execute(delete_game_query)

                # Фиксируем изменения
                await session.commit()

                self.logger.info(
                    "Записи из таблиц `game`, `asked_questions`, "
                    "и `users` для code_of_chat=%s успешно удалены.",
                    code_of_chat,
                )
            except Exception as e:
                await session.rollback()  # Откат транзакции при ошибке
                self.logger.error(
                    "Ошибка при удалении записей для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise

    async def is_game_working(self, code_of_chat: int) -> bool:
        async with self.app.database.session() as session:
            try:
                # Запрос для получения is_working
                query = select(Game.is_working).where(
                    Game.code_of_chat == code_of_chat
                )
                result = await session.execute(query)
                is_working = result.scalar_one_or_none()

                if is_working is None:
                    self.logger.info(
                        "Запись с code_of_chat=%s не найдена.", code_of_chat
                    )
                    return False

                self.logger.info(
                    "is_working для code_of_chat=%s: %s",
                    code_of_chat,
                    is_working,
                )

            except Exception as e:
                self.logger.error(
                    "Ошибка при проверке is_working для code_of_chat=%s: %s",
                    code_of_chat,
                    e,
                )
                raise
            else:
                return is_working == 1
