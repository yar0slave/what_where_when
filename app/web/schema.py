from marshmallow import Schema, fields


class QuestionSchema(Schema):
    question = fields.Str(required=True)
    answer = fields.Str(required=True)
