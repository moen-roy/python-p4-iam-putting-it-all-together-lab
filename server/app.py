#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return {'errors': ['Username and password are required']}, 422

        user = User(
            username=username,
            image_url=image_url,
            bio=bio
        )
        user.password_hash = password

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

        session['user_id'] = user.id

        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }, 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Unauthorized'}, 401

        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }, 200

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not user.authenticate(password):
            return {'error': 'Invalid username or password'}, 401

        session['user_id'] = user.id

        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        session.pop('user_id', None)
        return '', 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        recipes = Recipe.query.all()
        recipes_data = []
        for recipe in recipes:
            recipes_data.append({
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username,
                    'image_url': recipe.user.image_url,
                    'bio': recipe.user.bio
                }
            })
        return recipes_data, 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
            db.session.add(recipe)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

        return {
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': recipe.user.id,
                'username': recipe.user.username,
                'image_url': recipe.user.image_url,
                'bio': recipe.user.bio
            }
        }, 201

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)