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

    async def check_answer(self, question_id: int, user_answer: str) -> bool:
        async with self.app.database.session() as session:
            query = select(Questions.answer).where(Questions.id == question_id)
            result = await session.execute(query)
            correct_answer = result.scalar_one_or_none()

            if correct_answer is None:
                self.logger.error("Вопрос с id=%s не найден.", question_id)
                return False

            is_correct = (
                correct_answer.strip().lower() == user_answer.strip().lower()
            )
            self.logger.info(
                "Ответ %s для вопроса id=%s.",
                "правильный" if is_correct else "неправильный",
                question_id,
            )

            return is_correct

    async def list_questions(self) -> list[Questions]:
        async with self.app.database.session() as session:
            query = select(Questions)
            result = await session.execute(query)
            questions = result.scalars().all()
            return list(questions)


class UserAccessor(BaseAccessor):
    async def join_user(
        self, int_user_id: int, username: str, chat_id: int
    ) -> Users:
        async with self.app.database.session() as session:
            user = Users(
                int_user_id=int_user_id,  # Telegram ID пользователя
                user_id=username,  # Имя пользователя
                chat_id=chat_id,  # Идентификатор чата
            )

            session.add(user)
            await session.commit()

            return user

    async def get_users_by_chat_id(self, chat_id: int) -> list[str]:
        async with self.app.database.session() as session:
            query = select(Users.user_id).where(Users.chat_id == chat_id)
            result = await session.execute(query)
            return result.scalars().all()


class GameAccessor(BaseAccessor):
    async def create_or_update_game(
        self,
        code_of_chat: int,
        captain_id: str | None,
        points_awarded: int | None,
        question_id: int | None,
        round_number: int | None,
        respondent_id: str | None,
        is_working: int | None,
    ) -> Game:
        async with self.app.database.session() as session:
            # Пытаемся найти существующую запись
            query = select(Game).where(Game.code_of_chat == code_of_chat)
            result = await session.execute(query)
            game = result.scalar_one_or_none()

            if game:
                # Обновляем только переданные параметры
                for key, value in locals().items():
                    if hasattr(game, key) and value is not None:
                        setattr(game, key, value)
            else:
                # Создаём новую запись, если не найдено
                game = Game(
                    code_of_chat=code_of_chat,
                    captain_id=captain_id,
                    points_awarded=points_awarded,
                    question_id=question_id,
                    round_number=round_number,
                    respondent_id=respondent_id,
                    is_working=is_working,
                )
                session.add(game)

            await session.commit()

        return game

    async def reset_respondent_id(self, code_of_chat: int) -> bool:
        async with self.app.database.session() as session:
            # Пытаемся найти запись по code_of_chat
            query = select(Game).where(Game.code_of_chat == code_of_chat)
            result = await session.execute(query)
            game = result.scalar_one_or_none()

            if game:
                # Сбрасываем respondent_id в None
                game.respondent_id = None
                await session.commit()
                return True  # Возвращаем True, если операция успешна
            return False  # Если игра не найдена

    async def get_all_code_of_chat(self) -> list[int]:
        async with self.app.database.session() as session:
            # Выполняем SELECT для получения всех code_of_chat
            query = select(Game.code_of_chat)
            result = await session.execute(query)
            return result.scalars().all()

    async def is_captain_set(self, code_of_chat: int) -> bool:
        async with self.app.database.session() as session:
            # Запрос для получения captain_id по code_of_chat
            query = select(Game.captain_id).where(
                Game.code_of_chat == code_of_chat
            )
            result = await session.execute(query)

            return result.scalar_one_or_none()

    async def get_game_by_chat_id(self, code_of_chat: int) -> Game | None:
        async with self.app.database.session() as session:
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
            return game

    async def get_round_number_by_chat_id(self, code_of_chat: int) -> int:
        async with self.app.database.session() as session:
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

            return round_number

    async def set_round_number(
        self, code_of_chat: int, round_number: int
    ) -> None:
        async with self.app.database.session() as session:
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

    async def assign_question_to_game(
        self, question_text: str, code_of_chat: int
    ) -> None:
        async with self.app.database.session() as session:
            query = select(Questions.id).where(
                Questions.question == question_text
            )
            result = await session.execute(query)
            question_id = result.scalar_one_or_none()

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

    async def get_respondent_id_by_chat_id(
        self, code_of_chat: int
    ) -> str | None:
        async with self.app.database.session() as session:
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
            return None

    async def get_question_by_chat_id(
        self, code_of_chat: int
    ) -> Questions | None:
        async with self.app.database.session() as session:
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

            return question

    async def get_points_awarded_by_chat_id(self, code_of_chat: int) -> int:
        try:
            async with self.app.database.session() as session:
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
                "Ошибка при получении points_awarded для code_of_chat=%s: %s",
                code_of_chat,
                str(e),
            )
        else:
            return points_awarded

    async def clear_game_users_and_asked_questions(
        self, code_of_chat: int
    ) -> None:
        async with self.app.database.session() as session:
            # Удаляем связанные записи из asked_questions
            delete_asked_questions_query = delete(AskedQuestions).where(
                AskedQuestions.chat_id == code_of_chat
            )
            await session.execute(delete_asked_questions_query)

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

    async def is_game_working(self, code_of_chat: int) -> bool:
        async with self.app.database.session() as session:
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

            return is_working == 1
