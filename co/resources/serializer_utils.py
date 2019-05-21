from functools import reduce


def serialize_balances(balances):
    return [serialize_balance(b) for b in balances]


def serialize_balance(balance):
    return {
        'id': balance.id,
        'name': balance.name,
        'currency': balance.currency,
        'annualIncomePercentage': balance.annual_income_percentage,
        'balance': float(reduce(lambda x, y: x + y, list(map(lambda t: t.amount, balance.transactions)), 0))
    }


def serialize_transactions(transactions, actual_balances):
    assert len(transactions) == len(actual_balances)

    response = list()
    for i in range(0, len(transactions)):
        response.append(serialize_transaction(transactions[i], actual_balances[i]))

    print(response)
    return response


def serialize_transaction(transaction, actual_balance):
    amount = float(transaction.amount)
    return {
        'id': transaction.id,
        'balanceId': transaction.balance_id,
        'balanceName': transaction.balance.name,
        'income': amount if amount >= 0 else 0,
        'expenses': amount if amount < 0 else 0,
        'datetime': str(transaction.datetime),
        'description': transaction.description,
        'actualBalance': actual_balance
    }


def serialize_budget(budget, current_amount):
    return {
        'id': budget.id,
        'name': budget.name,
        'initialAmount': float(budget.initial_amount),
        'currentAmount': current_amount,
        'relAmount': float(current_amount / float(budget.initial_amount) * 100),
        'currency': budget.currency
    }


def serialize_goal(target, current_amount):
    return {
        'id': target.id,
        'name': target.name,
        'currentAmount': current_amount,
        'initialAmount': float(target.initial_amount),
        'currency': target.currency,
        'isDeletable': target.is_deletable(current_amount)
    }
