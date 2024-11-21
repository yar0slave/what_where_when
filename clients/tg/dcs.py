from dataclasses import field
from typing import ClassVar

from marshmallow import EXCLUDE, Schema
from marshmallow_dataclass import dataclass


@dataclass
class MessageFrom:
    id: int
    first_name: str
    last_name: str | None
    username: str

    class Meta:
        unknown = EXCLUDE


@dataclass
class Chat:
    id: int
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    title: str | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: MessageFrom = field(metadata={"data_key": "from"})
    chat: Chat
    text: str | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class MyChatMember:
    chat: Chat
    from_: MessageFrom = field(metadata={"data_key": "from"})
    date: int
    old_chat_member: dict
    new_chat_member: dict

    class Meta:
        unknown = EXCLUDE


@dataclass
class UpdateObj:
    update_id: int
    message: Message | None = None
    my_chat_member: MyChatMember | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class GetUpdatesResponse:
    ok: bool
    result: list[UpdateObj]

    Schema: ClassVar[type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class SendMessageResponse:
    ok: bool
    result: Message

    Schema: ClassVar[type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE
