from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from iso4217 import Currency
from werkzeug.security import generate_password_hash, check_password_hash
from functools import reduce

db = SQLAlchemy()

currencies = [
    Currency.usd,
    Currency.rub,
    Currency.eur
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password = db.Column(db.String(128), nullable=False)

    balances = db.relationship('Balance', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def __repr__(self) -> str:
        return '<User: {}>'.format(self.id)


class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ISO 4217
    currency = db.Column(db.String(3), nullable=False)

    name = db.Column(db.String(64), nullable=False)
    annual_income_percentage = db.Column(db.Integer, default=0)

    system = db.Column(db.Boolean, nullable=False, default=False)

    transactions = db.relationship('Transaction', backref='balance', lazy=True)

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_user_id(cls, user_id, id=None):
        return cls.query.filter_by(user_id=user_id, id=id).first() if id \
            else cls.query.filter_by(user_id=user_id, id=id).all()

    @classmethod
    def actual_balance(cls, id):
        balance = cls.query.filter_by(id=id).first()
        amounts = list(map(lambda t: t.amount, balance.transactions))
        return float(reduce(lambda x, y: x + y, amounts, 0))

    @classmethod
    def delete(cls, id):
        cls.query.filter_by(id=id).delete()
        db.session.commit()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        db.session.flush()
        return self.id

    def update(self):
        db.session.commit()

    def __repr__(self) -> str:
        return '<Balance: {}>'.format(self.id)


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    initial_amount = db.Column(db.Numeric, nullable=False)
    name = db.Column(db.String(64))

    # ISO 4217
    currency = db.Column(db.String(3), nullable=False)

    transactions = db.relationship('Transaction', backref='budget', lazy=True)

    @classmethod
    def delete(cls, id):
        cls.query.filter_by(id=id).delete()
        db.session.commit()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_user_id(cls, user_id, id=None):
        return cls.query.filter_by(user_id=user_id, id=id).first() if id \
            else cls.query.filter_by(user_id=user_id, id=id).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    initial_amount = db.Column(db.Numeric, nullable=False)
    balance_id = db.Column(db.Integer, db.ForeignKey('balance.id'))
    name = db.Column(db.String(64))
    currency = db.Column(db.String(3), nullable=False)

    @classmethod
    def find_by_user_id(cls, user_id, id=None):
        return cls.query.filter_by(user_id=user_id, id=id).first() if id \
            else cls.query.filter_by(user_id=user_id, id=id).all()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def delete(cls, id):
        goal = cls.query.filter_by(id=id).first()
        if goal.is_deletable():
            cls.query.filter_by(id=id).delete()
            db.session.commit()

    def update(self):
        db.session.commit()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def is_deletable(self, current_amount=None):
        if current_amount is None:
            current_amount = Balance.actual_balance(self.balance_id)

        return current_amount == 0 or current_amount >= self.initial_amount



class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance_id = db.Column(db.Integer, db.ForeignKey('balance.id'))
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Numeric, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(64))

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_user_id(cls, user_id, id=None):
        return cls.query.filter_by(user_id=user_id, id=id).first() if id \
            else cls.query.filter_by(user_id=user_id, id=id).all()

    @classmethod
    def find_by_balance_ids(cls, balance_ids):
        return cls.query.filter(Transaction.balance_id.in_(balance_ids)).all()

    @classmethod
    def find_by_budget_id(cls, budget_id):
        return cls.query.filter(Transaction.budget_id == budget_id).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def save_to_db_in_session(cls, *transactions):
        for transaction in transactions:
            db.session.add(transaction)

        db.session.commit()

    def update(self):
        db.session.commit()
