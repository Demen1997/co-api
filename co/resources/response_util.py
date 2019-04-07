def not_found():
    return {}, 404


def invalid_request(message='Received request wasn\'t valid'):
    return {'message': message}, 422


def access_denied(message='Access denied'):
    return {'message': message}, 403
