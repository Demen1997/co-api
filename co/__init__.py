from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api

from co.config import Config
from co.models import db, User
from co.resources.auth import UserRegistration, UserLogin, TokenRefresh
from co.resources.main import Currencies, Balances, Transactions, Budgets, BudgetExpend

migrate = Migrate()
api = Api()
jwt = JWTManager()


def create_app(conf=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if conf is not None:
        app.config.from_object(conf)

    migrate.init_app(app, db)
    db.init_app(app)

    add_resources(api)

    # noinspection PyTypeChecker
    api.init_app(app)
    jwt.init_app(app)
    CORS(app)

    return app


def add_resources(a):
    a.add_resource(UserRegistration, '/auth/register')
    a.add_resource(UserLogin, '/auth/login')
    a.add_resource(TokenRefresh, '/auth/refresh')
    a.add_resource(Currencies, '/main/currencies')
    a.add_resource(Balances, '/main/balances')
    a.add_resource(Transactions, '/main/transactions')
    a.add_resource(BudgetExpend, '/main/transactions/expandBudget')
    a.add_resource(Budgets, '/main/budgets')
