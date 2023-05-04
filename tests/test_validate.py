from bs4 import BeautifulSoup
from flask import url_for


def test_upload_and_validate_file(app, csv_file):
    with app.test_client() as client:
        resp = client.get(url_for("frontend.validate"))
        soup = BeautifulSoup(resp.data.decode("utf-8"), "html5lib")
        assert soup.h1.text == "Upload your brownfield land register"
