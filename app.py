#!/usr/bin/env python3
from flask_restplus import Resource
from auth import app, api, UserService, JWTDecodeError, MongoStore, MemoryStore,  \
    CredentialsModel, JWTValidationParser, JWTTokenModel, UserModel, MissingUserError
import jwt
import os

if os.getenv('MONGO_URI') is not None:
    store = MongoStore()
else:
    store = MemoryStore()
user_service = UserService(store)

user_ns = api.namespace('users', description='Users')
jwt_ns = api.namespace('jwt', description='JWT')

JWT_SECRET = os.getenv('SECRET', 'secret')


@user_ns.route('/')
class UserList(Resource):
    @api.doc("Create User")
    @api.expect(UserModel)
    @api.marshal_with(UserModel)
    def post(self):
        return user_service.create(api.payload)


@user_ns.route('/<string:id>')
class User(Resource):
    @user_ns.marshal_with(UserModel)
    def get(self, id):
        return user_service.get(id)


@jwt_ns.route('/')
class JWTRequest(Resource):
    @jwt_ns.doc("Request JWT Token")
    @jwt_ns.expect(CredentialsModel)
    @jwt_ns.marshal_with(JWTTokenModel)
    def post(self):

        user = user_service.get_by_username(api.payload.get('username'))
        if user is not None:
            encoded = jwt.encode({
                'id': user.get('id'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name')
            }, JWT_SECRET, algorithm='HS256')
            return {'token': encoded.decode('utf-8')}
        else:
            raise MissingUserError


@jwt_ns.route('/validate')
class JWTValidate(Resource):
    @jwt_ns.doc("Validate JWT Token")
    @jwt_ns.expect(JWTValidationParser)
    @jwt_ns.marshal_with(UserModel)
    def get(self):
        args = JWTValidationParser.parse_args()
        try:
            decoded = jwt.decode(args.get('token'), JWT_SECRET, algorithms=['HS256'])
            user = user_service.get(decoded.get('id'))
            return user
        except jwt.exceptions.ExpiredSignatureError:
            raise JWTDecodeError("expired JWT token")
        except jwt.exceptions.ImmatureSignatureError:
            raise JWTDecodeError("immature JWT token")
        except jwt.exceptions.DecodeError:
            raise JWTDecodeError("error decoding JWT token")
        except jwt.exceptions.InvalidTokenError:
            raise JWTDecodeError("invalid JWT token")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
