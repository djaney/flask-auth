from flask import Flask
from flask_restplus import Api, fields
from werkzeug.exceptions import BadRequest
import os
import pymongo
from pymongo import errors
from bson import ObjectId
import uuid

MONGO_URI = os.getenv('MONGODB_URI')
DATABASE = os.getenv('DATABASE')
TABLE_USERS = os.getenv('TABLE_USERS')

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


class BaseStore:
    def create(self, data):
        """
        :param data:
        :return: id
        """
        raise NotImplementedError

    def find_one(self, params):
        """
        :param params:
        :return: object
        """
        raise NotImplementedError


class MemoryStore(BaseStore):
    def __init__(self):
        self.memory = []

    def create(self, data):
        data['id'] = str(uuid.uuid1())
        self.memory.append(data)
        return data['id']

    def find_one(self, params):
        for item in self.memory:
            found = True
            for k, v in params.items():
                if item.get(k) is None or item.get(k) != v:
                    found = False
            if found:
                return item
        return None


class MongoStore(BaseStore):
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[DATABASE]
        self.table = self.db[TABLE_USERS]

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
            return str(self.table.insert_one(data).inserted_id)
        except errors.DuplicateKeyError:
            raise DuplicateUserError

    def find_one(self, params):
        if 'id' in params:
            params['id'] = ObjectId(params['id'])
        data = self.table.find_one(params)
        data['id'] = str(data['_id'])
        del data['_id']
        return data


class UserService:
    def __init__(self, store):
        """
        :param store: BaseStore
        """
        self.store = store

    def create(self, payload):
        _id = self.store.create(payload)
        return self.store.find_one({'id': _id})

    def get(self, user_id):
        data = self.store.find_one({'id': user_id})
        return data

    def get_by_username(self, username):
        data = self.store.find_one({'username': username})
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
