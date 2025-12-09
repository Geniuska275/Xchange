from flask_restx import Namespace, Resource, fields
from app import mongo

api = Namespace('api', description='API operations')

user_model = api.model('User', {
    'name': fields.String(required=True, description='User name'),
    'email': fields.String(required=True, description='User email'),
    'age': fields.Integer(description='User age')
})

@api.route('/users')
class UserList(Resource):
    def get(self):
        """List all users"""
        users = list(mongo.db.users.find({}, {'_id': 0}))
        return users
    
    def post(self):
        """Create a new user"""
        user_data = api.payload
        mongo.db.users.insert_one(user_data)
        return user_data, 201