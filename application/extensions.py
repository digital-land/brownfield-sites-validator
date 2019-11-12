# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in factory.py
"""
from flask_sqlalchemy import SQLAlchemy
from flask_misaka import Misaka
from flask_migrate import Migrate

misaka = Misaka()
db = SQLAlchemy()
migrate = Migrate(db=db)