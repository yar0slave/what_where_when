from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    pass


class Questions(BaseModel):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(
        String, nullable=False, comment="Вопрос"
    )
    answer: Mapped[str] = mapped_column(String, nullable=False, comment="Ответ")


class AskedQuestions(BaseModel):
    __tablename__ = "asked_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
        comment="Вопрос, который был",
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("game.id"),
        nullable=False,
        comment="Идентификатор чата команды",
    )


class Game(BaseModel):
    __tablename__ = "game"

    id: Mapped[int] = mapped_column(primary_key=True)
    captain_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="Идентификатор капитана команды",
    )
    points_awarded: Mapped[int] = mapped_column(
        comment="Количество начисленных очков"
    )
    code_of_chat: Mapped[int] = mapped_column(
        comment="Как бы тоже айдишник, но тот который создает тг"
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=True,
        comment="Вопрос, задаваемый в раунде",
    )
    round_number: Mapped[int] = mapped_column(comment="Номер раунда")
    respondent_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="Идентификатор ответчика команды",
    )


class Users(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        nullable=False,
        comment="Идентификатор участника команды",
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("game.id"),
        nullable=False,
        comment="Идентификатор чата команды",
    )
