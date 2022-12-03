import os
from flask import (
    request, 
    url_for)
from flask_restful import Resource
from http import HTTPStatus

from flask_jwt_extended import (
    get_jwt_identity, 
    jwt_required)
from webargs import fields
from webargs.flaskparser import use_kwargs

from models.recipe import Recipe
from schemas.recipe import RecipeSchema, RecipePaginationShema

from extensions import (
    image_set, 
    cache,
    limiter)
from utils import (
    save_image,
    clear_cache)

recipe_schema = RecipeSchema(many=False, exclude=('author.email',))
recipe_cover_schema = RecipeSchema(only=('cover_url',))
recipe_list_schema = RecipeSchema(many=True, exclude=('author.email',))
recipe_pagination_schema = RecipePaginationShema()


class RecipeListResource(Resource):
    """
    https://github.com/TrainingByPackt/Python-API-Development-Fundamentals/blob/master/Lesson10/Exercise64/resources/recipe.py
    """
    
    decorators = [limiter.limit(
        '3/minute; 30/hour; 300/day', 
        methods=['GET'], 
        error_message='Too Many Requests')]
    
    @use_kwargs(
        {
            'q': fields.Str(missing=''),
            'page': fields.Int(missing=1), 
            'per_page': fields.Int(missing=20),
            'sort': fields.Str(missing='created_at'),
            'order': fields.Str(missing='desc'),
        }, 
        location='querystring')
    @cache.cached(timeout=60, query_string=True)
    def get(self, q, page, per_page, sort, order):
               
        if sort not in ['created_at', 'cook_time', 'num_of_servings', 'recipies']:
            sort = 'created_at'
        
        if order not in ['asc', 'desc']:
            order = 'desc'
        
        paginated_recipes = Recipe.get_all_published(
            q, page, per_page, sort, order)
        
        return recipe_pagination_schema.dump(paginated_recipes), HTTPStatus.OK
    

    @jwt_required()
    def post(self):
        data_in = request.get_json()
        current_user_id = get_jwt_identity()
        
        data_in  = recipe_schema.load(data=data_in)
        
        new_recipe = Recipe(**data_in)
        new_recipe.user_id = current_user_id        
        new_recipe.save()
        
        clear_cache('/recipes')
        
        return recipe_schema.dump(new_recipe), HTTPStatus.CREATED


class RecipeResource(Resource):
    
    @jwt_required(optional=True)
    def get(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=int(recipe_id))

        if recipe is None:
            return {'message': "recipe {} not found".format(recipe_id)}, \
                HTTPStatus.NOT_FOUND
        
        current_user_id = get_jwt_identity()
        
        if recipe.is_publish == False and recipe.user_id != current_user_id:
            return {'message': "Access is not allowed"}, \
                HTTPStatus.FORBIDDEN
        
        return recipe_schema.dump(recipe), HTTPStatus.OK


    @jwt_required()
    def patch(self, recipe_id):
        
        data_in = recipe_schema.load(
            data=request.get_json(), 
            partial=('name',))
        
        recipe = Recipe.get_by_id(recipe_id=int(recipe_id))

        if recipe is None:
            return {'message': "recipe {} not found".format(recipe_id)}, \
                HTTPStatus.NOT_FOUND
        
        current_user_id = get_jwt_identity()
        
        if current_user_id != recipe.user_id:
            return {'message': "Access is not allowed"}, \
                HTTPStatus.FORBIDDEN
        
        recipe.name = data_in.get('name', recipe.name)
        recipe.ingredients = data_in.get('ingredients', recipe.ingredients)
        recipe.description = data_in.get('description', recipe.description)
        recipe.num_of_servings = data_in.get('num_of_servings', recipe.num_of_servings)
        recipe.cook_time = data_in.get('cook_time', recipe.cook_time)
        recipe.directions = data_in.get('directions', recipe.directions)
        
        recipe.save()
        
        clear_cache('/recipes')
        
        return recipe_schema.dump(recipe), HTTPStatus.OK
    
    
    @jwt_required()
    def delete(self, recipe_id):
        
        recipe = Recipe.get_by_id(recipe_id=int(recipe_id))

        if recipe is None:
            return {'message': "recipe {} not found".format(recipe_id)}, \
                HTTPStatus.NOT_FOUND
        
        current_user_id = get_jwt_identity()
        
        if current_user_id != recipe.user_id:
            return {'message': "Access is not allowed"}, \
                HTTPStatus.FORBIDDEN
        
        recipe.delete()
        
        clear_cache('/recipes')
        
        return {}, HTTPStatus.NO_CONTENT


class RecipePublishResouce(Resource):
    
    @jwt_required()
    def put(self, recipe_id, is_publish=True):
        
        recipe = Recipe.get_by_id(recipe_id=int(recipe_id))
        
        if recipe is None:
            return {'message': "recipe {} not found".format(recipe_id)}, \
                HTTPStatus.NOT_FOUND
        
        current_user_id = get_jwt_identity()
        if current_user_id != recipe.user_id:
            return {'message': "Access is not allowed"}, \
                HTTPStatus.FORBIDDEN
        
        recipe.is_publish = is_publish
        recipe.save()
        
        clear_cache('/recipes')
        
        return {}, HTTPStatus.NO_CONTENT
    
    
    @jwt_required()
    def delete(self, recipe_id):
        
        return self.put(recipe_id, is_publish=False)
        
        # recipe = Recipe.get_by_id(recipe_id=int(recipe_id))

        # if recipe is None:
        #     return {'message': "recipe {} not found".format(recipe_id)}, \
        #         HTTPStatus.NOT_FOUND
        
        # current_user_id = get_jwt_identity()
        
        # if current_user_id != recipe.user_id:
        #     return {'message': "Access is not allowed"}, \
        #         HTTPStatus.FORBIDDEN
        
        # recipe.is_publish = False
        # recipe.save()
        
        # clear_cache('/recipes')
        
        # return {}, HTTPStatus.NO_CONTENT


class RecipeCoverUploadResource(Resource):
    
    @jwt_required()
    def put(self, recipe_id):
        
        file = request.files.get('cover')
        
        if not file:
            return {'message': "Image with name 'cover' not found"}, \
                HTTPStatus.BAD_REQUEST
        
        if not image_set.file_allowed(file, file.filename):
            return {'message': "File type not allower"}, \
                HTTPStatus.BAD_REQUEST
        
        recipe_to_update = Recipe.get_by_id(int(recipe_id))
        
        if recipe_to_update.cover_image:
            cover_path = image_set.path(
                folder='covers', 
                filename=recipe_to_update.cover_image)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        
        filename = save_image(image=file, folder='covers')
        recipe_to_update.cover_image = filename
        recipe_to_update.save()
        
        clear_cache('/recipes')
        
        return recipe_cover_schema.dump(recipe_to_update), HTTPStatus.OK
