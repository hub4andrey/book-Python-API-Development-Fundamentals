from flask import request
from flask_restful import Resource
from http import HTTPStatus

from models.user import User
from utils import check_password

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)


black_list  =set()


class TokenResource(Resource):
    
    def post(self):
        
        data_in = request.get_json()
        email = data_in.get('email')
        password = data_in.get('password')
        
        user = User.get_by_email(email)
        
        if not user or not check_password(password, user.password):
            return {'message': f"email or password is incorrect"}, \
                HTTPStatus.UNAUTHORIZED
                
        if not user.is_active:
            return {'message': 'The user account is not activated yet'}, \
                HTTPStatus.FORBIDDEN
        
        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(identity=user.id)
        
        data_out = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            }
        
        return data_out, HTTPStatus.OK
    

class RefreshResource(Resource):
    
    @jwt_required(refresh=True)
    def post(self):
        current_user_id = get_jwt_identity()
        user = User.get_by_id(current_user_id)
        
        if not user.is_active:
            return {'message': 'The user account is not activated yet'}, \
                HTTPStatus.FORBIDDEN
        
        access_token = create_access_token(
            identity=current_user_id, fresh=False)
        
        return {'access_token': access_token}, HTTPStatus.OK


class RevokeResource(Resource):
     
    @jwt_required()
    def post(self):
        
        jti = get_jwt().get('jti')
        black_list.add(jti)
        
        return {'message': "Successfully logged out"}, HTTPStatus.OK
        