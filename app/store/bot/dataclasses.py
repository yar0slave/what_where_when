from dataclasses import dataclass


@dataclass
class Question:
    text: str
    answer: str


@dataclass
class Player:
    username: str
    user_id: int
    is_captain: bool = False
