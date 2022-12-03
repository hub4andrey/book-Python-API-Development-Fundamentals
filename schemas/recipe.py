from flask import url_for
from marshmallow import (
    Schema,
    fields,
    post_dump,
    validate,
    validates,
    ValidationError
)
from sqlalchemy import asc, desc

from schemas.user import UserSchema
from schemas.pagination import PaginationSchema



def validate_num_of_servings(n):
    if n < 1 or n > 50 :
        
        raise ValidationError("Number of servings must be in range 1 - 50")


class RecipeSchema(Schema):
    """
    https://github.com/TrainingByPackt/Python-API-Development-Fundamentals/blob/master/Lesson10/Exercise64/schemas/recipe.py
    """
    
    class Meta:
        ordered = True
    
    
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True, 
        validate=[validate.Length(max=100)])
    description = fields.String(
        validate=[validate.Length(max=200)])
    num_of_servings = fields.Integer(
        strict=True,
        validate=validate_num_of_servings)
    cook_time = fields.Int()
    ingredients = fields.String(validate=[validate.Length(max=500)])
    directions = fields.String(validate=[validate.Length(max=1000)])
    cover_url = fields.Method(serialize='dump_image_url')
    is_publish = fields.Boolean(dump_only=True)
    
    author = fields.Nested(
        UserSchema, 
        attribute='user',
        dump_only=True,
        only=('id', 'username', 'email'))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    
    @validates('cook_time')
    def validate_cook_time(self, data, **kwargs):
        if data < 1 or data > 300:
            raise ValidationError("Cook time must be in range 1-300 seconds")
    

    def dump_image_url(self, recipe):
        if recipe.cover_image:
            return url_for('static', filename='images/covers/{}'.
                           format(recipe.cover_image), _external=True)
        return url_for('static', filename='images/assets/default-cover.jpg',
                       _external=True)



class RecipePaginationShema(PaginationSchema):
    
    data = fields.Nested(RecipeSchema, attribute='items', many=True)
