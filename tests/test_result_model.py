from application.frontend.models import ResultModel


def test_post_model(session, result):
    result_model = ResultModel(result)
    session.add(result_model)
    session.commit()

    assert result_model.id
    assert len(result.rows) == 2
