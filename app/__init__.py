from flask import Flask, render_template
from flask_restx import Api, Namespace, Resource, fields
from config import Config
from pymongo import MongoClient
from bson import ObjectId
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # MongoDB connection with error handling
    try:
        # Move credentials to environment variables for security
        MONGO_URI = os.environ.get('MONGO_URI') or "mongodb+srv://kingsleyaigbojie2023_db_user:Debbie2026.@cluster0.cp8y8rx.mongodb.net/?appName=Cluster0"
        
        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        db = client["xchange_db"]  # Use a more descriptive database name
        
        # Test connection
        db.command("ping")
        print("✓ MongoDB connected successfully!")
    except Exception as e:
        print(f"✗ MongoDB connection error: {e}")
        db = None
    
    # Initialize API with Swagger
    api = Api(
        app,
        version='1.0',
        title='Xchange APIs',
        description='API Documentation for Xchange',
        doc='/api/docs'
    )
    
    # Create namespace
    ns = Namespace('api', description='API operations')
    
    # Define models
    user_model = ns.model('User', {
        'username': fields.String(required=True, description='Username'),
        'email': fields.String(required=True, description='Email address'),
        'password': fields.String(required=True, description='Password')
    })
    
    user_response_model = ns.model('UserResponse', {
        'id': fields.String(description='User ID'),
        'username': fields.String(description='Username'),
        'email': fields.String(description='Email address')
    })
    
    # Helper function to serialize MongoDB documents
    def serialize_user(user):
        if user and '_id' in user:
            user['id'] = str(user['_id'])
            del user['_id']
        if user and 'password' in user:
            del user['password']  # Don't return passwords
        return user
    
    # Define API routes
    @ns.route('/users')
    class UserList(Resource):
        @ns.doc('list_users')
        @ns.marshal_list_with(user_response_model)
        def get(self):
            """List all users"""
            try:
                if db is None:
                    return {'error': 'Database not connected'}, 500
                
                users = list(db.users.find({}, {'password': 0}))  # Exclude passwords
                for user in users:
                    user['id'] = str(user['_id'])
                    del user['_id']
                return users
            except Exception as e:
                return {'error': str(e)}, 500
        
        @ns.doc('create_user')
        @ns.expect(user_model)
        @ns.marshal_with(user_response_model, code=201)
        def post(self):
            """Create a new user"""
            try:
                if db is None:
                    return {'error': 'Database not connected'}, 500
                
                user_data = api.payload
                
                # Check if user already exists
                existing_user = db.users.find_one({
                    '$or': [
                        {'username': user_data.get('username')},
                        {'email': user_data.get('email')}
                    ]
                })
                
                if existing_user:
                    ns.abort(400, "User with this username or email already exists")
                
                # Insert user
                result = db.users.insert_one(user_data)
                
                # Return user without password
                user_data['id'] = str(result.inserted_id)
                del user_data['password']
                
                return user_data, 201
            except Exception as e:
                return {'error': str(e)}, 500
    
    @ns.route('/users/<string:identifier>')
    @ns.param('identifier', 'User ID or username')
    class User(Resource):
        @ns.doc('get_user')
        @ns.marshal_with(user_response_model)
        def get(self, identifier):
            """Get a user by ID or username"""
            try:
                if db is None:
                    return {'error': 'Database not connected'}, 500
                
                # Try to find by ObjectId first, then by username
                if ObjectId.is_valid(identifier):
                    user = db.users.find_one({'_id': ObjectId(identifier)}, {'password': 0})
                else:
                    user = db.users.find_one({'username': identifier}, {'password': 0})
                
                if user:
                    return serialize_user(user)
                ns.abort(404, f"User '{identifier}' not found")
            except Exception as e:
                return {'error': str(e)}, 500
        
        @ns.doc('delete_user')
        @ns.response(200, 'User deleted')
        def delete(self, identifier):
            """Delete a user"""
            try:
                if db is None:
                    return {'error': 'Database not connected'}, 500
                
                # Try to delete by ObjectId first, then by username
                if ObjectId.is_valid(identifier):
                    result = db.users.delete_one({'_id': ObjectId(identifier)})
                else:
                    result = db.users.delete_one({'username': identifier})
                
                if result.deleted_count:
                    return {'message': 'User deleted successfully'}, 200
                ns.abort(404, f"User '{identifier}' not found")
            except Exception as e:
                return {'error': str(e)}, 500
        
        @ns.doc('update_user')
        @ns.expect(user_model)
        @ns.marshal_with(user_response_model)
        def put(self, identifier):
            """Update a user"""
            try:
                if db is None:
                    return {'error': 'Database not connected'}, 500
                
                user_data = api.payload
                
                # Try to update by ObjectId first, then by username
                if ObjectId.is_valid(identifier):
                    result = db.users.update_one(
                        {'_id': ObjectId(identifier)},
                        {'$set': user_data}
                    )
                else:
                    result = db.users.update_one(
                        {'username': identifier},
                        {'$set': user_data}
                    )
                
                if result.matched_count:
                    # Fetch and return updated user
                    if ObjectId.is_valid(identifier):
                        user = db.users.find_one({'_id': ObjectId(identifier)}, {'password': 0})
                    else:
                        user = db.users.find_one({'username': identifier}, {'password': 0})
                    return serialize_user(user)
                
                ns.abort(404, f"User '{identifier}' not found")
            except Exception as e:
                return {'error': str(e)}, 500
    
    # Add namespace to API
    api.add_namespace(ns, path='/api')
    
    # Web routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        try:
            if db:
                db.command("ping")
                return {'status': 'healthy', 'database': 'connected'}, 200
            return {'status': 'unhealthy', 'database': 'disconnected'}, 500
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 500
    
    return app
