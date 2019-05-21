import datetime
import re

from flask_jwt_extended import create_access_token, create_refresh_token, jwt_refresh_token_required, get_jwt_identity
from flask_restful import Resource, reqparse

from co import User


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        expires = datetime.timedelta(days=365)
        access_token = create_access_token(identity=get_jwt_identity(), expires_delta=expires)
        return {'accessToken': access_token}


# noinspection PyArgumentList
class UserRegistration(Resource):
    email_regex = '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True)
        parser.add_argument('password', help='This field cannot be blank', required=True)
        parser.add_argument('email', help='This field cannot be blank', required=True)

        data = parser.parse_args()

        if not re.match(self.email_regex, data['email']):
            return {'message': 'Given email isn\'t valid'}, 422

        if User.find_by_username(data['username']):
            return {'message': 'User {} already exists'.format(data['username'])}, 403

        new_user = User(
            username=data['username'],
            email=data['email']
        )

        new_user.set_password(data['password'])

        try:
            new_user.save_to_db()
            return {
                'message': 'User \"{}\" was created'.format(data['username'])
            }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    def post(self):
        bad_message = {'message': 'Login or password is invalid'}, 422

        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True)
        parser.add_argument('password', help='This field cannot be blank', required=True)

        data = parser.parse_args()
        user = User.find_by_username(data['username'])
        if not user:
            return bad_message

        if user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {
                'accessToken': access_token,
                'refreshToken': refresh_token
            }
        else:
            return bad_message
