from aiohttp.web import HTTPBadRequest, json_response
from aiohttp_apispec import request_schema, response_schema

from app.web.app import View
from app.web.schema import QuestionSchema


class QuestionAddView(View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        try:
            if not self.data:
                raise HTTPBadRequest(text='No data provided')

            if 'question' not in self.data or 'answer' not in self.data:
                raise HTTPBadRequest(text='Question and answer are required')

            await self.store.quiz.create_question(
                question_text=self.data["question"],
                answer_text=self.data["answer"]
            )

            return json_response(data={
                "question": self.data["question"],
                "answer": self.data["answer"]
            })

        except Exception as e:
            return json_response(
                status=500,
                data={'error': str(e)}
            )


class QuestionListView(View):
    async def get(self):
        try:
            questions = await self.store.quiz.list_questions()
            return json_response(data={
                "questions": [
                    {
                        "question": q.question,
                        "answer": q.answer
                    } for q in questions
                ]
            })
        except Exception as e:
            return json_response(
                status=500,
                data={'error': str(e)}
            )