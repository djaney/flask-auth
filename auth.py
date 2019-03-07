from flask import Flask
from flask_restplus import Api, fields
from werkzeug.exceptions import BadRequest
import os
import pymongo
from pymongo import errors
from bson import ObjectId

app = Flask(__name__)
api = Api(app)

JWTValidationParser = api.parser()
JWTValidationParser.add_argument('token', location='args', required=True)

JWTTokenModel = api.model('JWTToken', {
    'token': fields.String(),
})

UserModel = api.model('User', {
    'id': fields.String(required=True),
    'username': fields.String(required=True),
    'email': fields.String(),
    'password': fields.String(),
    'first_name': fields.String(),
    'last_name': fields.String()
}, mask="id,username,email,first_name,last_name")

CredentialsModel = api.model('Credentials', {
    'username': fields.String(required=True),
    'password': fields.String(required=True)
})


class MongoStore:
    def __init__(self):
        self.client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client[os.getenv('DATABASE')]
        self.table = self.db[os.getenv('TABLE_USERS')]

        # Create index
        while True:
            try:
                self.table.create_index([('username', pymongo.ASCENDING)], unique=True)
                break
            except BaseException:
                app.logger.debug("retrying mongodb connect...")

    def create(self, data):
        if 'id' in data:
            del data['id']
        try:
            return self.table.insert_one(data).inserted_id
        except errors.DuplicateKeyError:
            raise DuplicateUserError

    def find_one(self, params):
        data = self.table.find_one(params)
        data['id'] = data['_id']
        return data


class UserService:
    def __init__(self, store):
        """
        :param store: BaseStore
        """
        self.store = store

    def create(self, payload):
        _id = self.store.create(payload)
        return self.store.find_one({'_id': _id})

    def get(self, user_id):
        data = self.store.find_one({'_id': ObjectId(user_id)})
        data['id'] = str(data['_id'])
        del data['_id']
        return data

    def get_by_username(self, username):
        data = self.store.find_one({'username': username})
        data['id'] = str(data['_id'])
        del data['_id']
        return data


class MissingUserError(BadRequest):
    description = "Missing user"
    code = 404


class JWTDecodeError(BadRequest):
    description = "Error decoding JWT token"
    code = 401

    def __init__(self, description=None, response=None):
        super().__init__(description, response)


class DuplicateUserError(BadRequest):
    description = "User already exists"
