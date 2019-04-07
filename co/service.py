from co.models import db, Balance, Goal


class BalanceService(object):

    @staticmethod
    def get_by_id(id):
        return Balance.query.filter_by(id=id).first()

    @staticmethod
    def get_by_user_id(user_id):
        return Balance.query.filter_by(user_id=user_id).all()

    @staticmethod
    def create(user_id, currency, name, income_percentage):
        balance = Balance(user_id=user_id, currency=currency, name=name, annual_income_percentage=income_percentage)
        db.session.add(balance)
        db.session.commit()

    @staticmethod
    def delete(id):
        balance = Balance.query.filter_by(id=id).first()
        db.session.delete(balance)
        db.session.commit()

    @staticmethod
    def update_session():
        db.session.commit()


class GoalService(object):

    @staticmethod
    def get_by_id(id):
        return Balance.query.filter_by(id=id).first()

    @staticmethod
    def get_by_user_id(user_id: int):
        return Goal.query.filter_by(user_id=user_id).all()

    @staticmethod
    def create(user_id, currency, name):
        goal = Goal(user_id=user_id, currency=currency, name=name)
        db.session.add(goal)
        db.session.commit()

    @staticmethod
    def delete(id):
        goal = Goal.query.filter_by(id=id).first()
        db.session.delete(goal)
        db.session.commit()
