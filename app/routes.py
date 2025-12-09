from flask_restx import Namespace, Resource, fields
from app import mongo

api = Namespace('api', description='API operations')

user_model = api.model('User', {
    'username': fields.String(required=True, description='User username'),
    'email': fields.String(required=True, description='User email'),
    'password': fields.Integer(description='User password')
})

@api.route('/users')
class UserList(Resource):
    @api.doc('list_users')
    @api.marshal_list_with(user_model)
    def get(self):
        """List all users"""
        users = list(mongo.db.users.find({}, {'_id': 0}))
        return users
    
    @api.doc('create_user')
    @api.expect(user_model)
    @api.marshal_with(user_model, code=201)
    def post(self):
        """Create a new user"""
        user_data = api.payload
        mongo.db.users.insert_one(user_data)
        return user_data, 201

@api.route('/users/<string:name>')
@api.param('name', 'The user name')
class User(Resource):
    @api.doc('get_user')
    @api.marshal_with(user_model)
    def get(self, name):
        """Get a user by name"""
        user = mongo.db.users.find_one({'name': name}, {'_id': 0})
        if user:
            return user
        api.abort(404, f"User {name} not found")
    
    @api.doc('delete_user')
    @api.response(204, 'User deleted')
    def delete(self, name):
        """Delete a user"""
        result = mongo.db.users.delete_one({'name': name})
        if result.deleted_count:
            return '', 204
        api.abort(404, f"User {name} not found")
    
    @api.doc('update_user')
    @api.expect(user_model)
    @api.marshal_with(user_model)
    def put(self, name):
        """Update a user"""
        user_data = api.payload
        mongo.db.users.update_one({'name': name}, {'$set': user_data})
        return user_data