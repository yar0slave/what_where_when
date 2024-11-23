from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger

class BaseModel(DeclarativeBase):
    pass


class Questions(BaseModel):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(
        String, nullable=False, comment="Вопрос"
    )
    answer: Mapped[str] = mapped_column(
        String, nullable=False, comment="Ответ"
    )

    asked_questions: Mapped[list["AskedQuestions"]] = relationship(
        "AskedQuestions", back_populates="question_rel", cascade="all, delete-orphan"
    )


class AskedQuestions(BaseModel):
    __tablename__ = "asked_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Вопрос, который был",
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("game.code_of_chat", ondelete="CASCADE"),
        nullable=False,
        comment="Идентификатор чата команды",
    )

    question_rel: Mapped["Questions"] = relationship(
        "Questions", back_populates="asked_questions"
    )
    game: Mapped["Game"] = relationship("Game", back_populates="asked_questions")


class Game(BaseModel):
    __tablename__ = "game"

    code_of_chat: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="Как бы тоже айдишник, но тот который создает тг"
    )
    captain_id: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Идентификатор капитана команды"
    )
    points_awarded: Mapped[int | None] = mapped_column(
        nullable=True, comment="Количество начисленных очков"
    )
    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Вопрос, задаваемый в раунде",
    )
    round_number: Mapped[int | None] = mapped_column(
        nullable=True, comment="Номер раунда"
    )
    respondent_id: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Идентификатор ответчика команды"
    )

    asked_questions: Mapped[list["AskedQuestions"]] = relationship(
        "AskedQuestions", back_populates="game", cascade="all, delete-orphan"
    )


class Users(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, nullable=False, comment="Идентификатор участника команды"
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("game.code_of_chat", ondelete="CASCADE"),
        nullable=False,
        comment="Идентификатор чата команды",
    )
