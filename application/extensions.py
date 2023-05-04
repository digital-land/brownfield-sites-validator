# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in factory.py
"""
from flask_sqlalchemy import SQLAlchemy
from flask_misaka import Misaka
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

misaka = Misaka()
db = SQLAlchemy()
migrate = Migrate(db=db)
csrf = CSRFProtect()
