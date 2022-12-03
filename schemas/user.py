from marshmallow import (
    Schema, 
    fields)
from flask import (
    url_for, 
    current_app)

from utils import hash_password


class UserSchema(Schema):
    """
    https://github.com/TrainingByPackt/Python-API-Development-Fundamentals/blob/master/Lesson10/Exercise64/schemas/user.py
    """
    
    class Meta:
        ordered = True

    
    id = fields.Int(dump_only=True)
    username = fields.String(required=True)
    email = fields.String(required=True)
    password = fields.Method(
        required=True, 
        load_only=True,
        deserialize='load_password')
    avatar_url = fields.Method(serialize='dump_avatar_url')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    
    def load_password(self, test_string):
        return hash_password(test_string)
    
    def dump_avatar_url(self, user):
        if user.avatar_image:

            return url_for(
                'static', 
                filename='images/avatars/{}'.format(user.avatar_image), 
                _external=True)

        return url_for(
            'static', 
            filename='images/assets/default-avatar.jpg',
            _external=True)
