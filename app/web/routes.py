import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.web.views.views import QuestionAddView, QuestionListView

    app.router.add_view("/add_question", QuestionAddView)
    app.router.add_view("/questions", QuestionListView)
