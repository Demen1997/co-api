from functools import reduce

from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from datetime import datetime

from co.models import currencies, User, Balance, Transaction, Budget

import co.resources.serializer_utils as ser_util
import co.resources.response_util as resp_util


def validate_balance_request(request):
    return request['name'].strip() \
           and request['annualIncomePercentage'] >= 0 \
           and request['currency'].strip()


def validate_budget_request(request):
    return request['name'].strip() \
           and request['initialAmount'] >= 0 \
           and request['currency'].strip()


def calculate_actual_balances(transactions):
    actual_balances_dict = {}
    actual_balances = []
    for t in transactions:
        try:
            actual_balance = actual_balances_dict[t.balance_id]
        except KeyError:
            actual_balance = Balance.actual_balance(t.balance_id)
            actual_balances_dict[t.balance_id] = actual_balance

        actual_balances.append(actual_balance)

    return actual_balances


def calculate_budget_current_amount(budget):
    transaction_amounts = list(map(lambda t: t.amount, Transaction.find_by_budget_id(budget.id)))
    return float(reduce(lambda x, y: x + y, transaction_amounts, 0) + budget.initial_amount)


class Currencies(Resource):
    @jwt_required
    def get(self):
        return list(map(lambda c: c.code, currencies))


class Balances(Resource):
    @jwt_required
    def get(self):
        request = reqparse.RequestParser() \
            .add_argument('id', type=int) \
            .add_argument('currency') \
            .parse_args()

        if request['id'] is None:
            balances = User.find_by_id(get_jwt_identity()).balances
            return ser_util.serialize_balances(balances) if not request['currency'] \
                else ser_util.serialize_balances(list(filter(lambda b: b.currency == request['currency'], balances)))

        if request['id'] <= 0:
            return resp_util.invalid_request('Given id isn\'t valid')

        balance = Balance.find_by_user_id(get_jwt_identity(), request['id'])
        if not balance:
            return resp_util.not_found()
        return ser_util.serialize_balance(balance)

    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('annualIncomePercentage', required=True, type=int)
        parser.add_argument('currency', required=True)

        data = parser.parse_args()
        if not validate_balance_request(data):
            return resp_util.invalid_request()

        Balance(
            user_id=get_jwt_identity(),
            name=data['name'],
            annual_income_percentage=data['annualIncomePercentage'],
            currency=data['currency']
        ).save_to_db()

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True, type=int)

        data = parser.parse_args()
        Balance.delete(data['id'])

    @jwt_required
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('id', required=True)

        data = parser.parse_args()
        if not data['name'].strip():
            return resp_util.invalid_request()

        balance = Balance.find_by_id(data['id'])
        balance.name = data['name']
        try:
            balance.update()
        except:
            return {'message': 'Something went wrong'}, 500


class BalancesAmount(Resource):
    @jwt_required
    def get(self):
        id = reqparse.RequestParser() \
            .add_argument('id', type=int, required=True) \
            .parse_args()['id']

        if id <= 0:
            return resp_util.invalid_request('Given id isn\'t valid')


class Transactions(Resource):
    @jwt_required
    def get(self):
        request = reqparse.RequestParser() \
            .add_argument('id', type=int) \
            .add_argument('balances') \
            .parse_args()

        user_id = get_jwt_identity()

        id = request['id']
        if id is not None:
            if id < 0:
                return resp_util.invalid_request()

            t = Transaction.find_by_user_id(user_id, id)

            return ser_util.serialize_transaction(t,
                                                  Balance.actual_balance(t.balance_id)) if t else resp_util.not_found()

        try:
            balances_string = request['balances']
        except KeyError:
            balances_string = ''

        balances_stripped_string = balances_string.strip()
        transactions = Transaction.find_by_user_id(user_id) if not balances_stripped_string \
            else Transaction.find_by_balance_ids(balances_stripped_string.split(','))

        return ser_util.serialize_transactions(transactions, calculate_actual_balances(transactions))

    @jwt_required
    def post(self):
        request = reqparse.RequestParser() \
            .add_argument('balanceId', type=int, required=True) \
            .add_argument('amount', type=float, required=True) \
            .add_argument('description') \
            .parse_args()

        user_id = get_jwt_identity()

        if request['balanceId'] not in list(map(lambda b: b.id, User.find_by_id(user_id).balances)):
            return resp_util.access_denied()

        Transaction(
            balance_id=request['balanceId'],
            user_id=user_id,
            amount=request['amount'],
            datetime=datetime.now(),
            description=request['description']
        ).save_to_db()


class Budgets(Resource):

    @jwt_required
    def get(self):
        id = reqparse.RequestParser() \
            .add_argument('id', type=int) \
            .parse_args()['id']

        if id is None:
            response = []
            for budget in User.find_by_id(get_jwt_identity()).budgets:
                response.append(ser_util.serialize_budget(budget, calculate_budget_current_amount(budget)))
            return response

        if id <= 0:
            return resp_util.invalid_request('Given id isn\'t valid')

        budget = Budget.find_by_user_id(get_jwt_identity(), id)
        if not budget:
            return resp_util.not_found()
        return ser_util.serialize_budget(budget, calculate_budget_current_amount(budget))

    @jwt_required
    def post(self):
        request = reqparse.RequestParser() \
            .add_argument('name', required=True) \
            .add_argument('initialAmount', required=True, type=int) \
            .add_argument('currency', required=True) \
            .parse_args()

        if not validate_budget_request(request):
            return resp_util.invalid_request()

        Budget(
            user_id=get_jwt_identity(),
            initial_amount=request['initialAmount'],
            name=request['name'],
            currency=request['currency']
        ).save_to_db()

    @jwt_required
    def put(self):
        request = reqparse.RequestParser() \
            .add_argument('name', required=True) \
            .add_argument('id', required=True).parse_args()

        if not request['name'].strip():
            return resp_util.invalid_request()

        budget = Budget.find_by_id(request['id'])
        budget.name = request['name']
        try:
            budget.update()
        except:
            return {'message': 'Something went wrong'}, 500

    @jwt_required
    def delete(self):
        request = reqparse.RequestParser() \
            .add_argument('id', required=True, type=int).parse_args()

        Budget.delete(request['id'])


class BudgetExpend(Resource):

    @jwt_required
    def post(self):
        request = reqparse.RequestParser() \
            .add_argument('balanceId', type=int, required=True) \
            .add_argument('amount', type=float, required=True) \
            .add_argument('description', required=True) \
            .add_argument('budgetId', type=int, required=True) \
            .parse_args()

        user_id = get_jwt_identity()

        if request['balanceId'] not in list(map(lambda b: b.id, User.find_by_id(user_id).balances)):
            return resp_util.access_denied()

        if request['budgetId'] not in list(map(lambda b: b.id, User.find_by_id(user_id).budgets)):
            return resp_util.access_denied()

        Transaction(
            balance_id=request['balanceId'],
            user_id=user_id,
            budget_id=request['budgetId'],
            amount=request['amount'],
            datetime=datetime.now(),
            description=request['description']
        ).save_to_db()
