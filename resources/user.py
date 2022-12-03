import os, re
from http import HTTPStatus

from flask import (
    request,
    url_for,
    current_app,
    render_template,
    )
from flask_restful import Resource
from flask_jwt_extended import (
    get_jwt_identity, 
    jwt_required,
    )
from mailgun import MailgunAPI
from webargs import fields
from webargs.flaskparser import use_kwargs

from extensions import image_set
from utils import (
    generate_token, 
    verify_token, 
    save_image,
    clear_cache)

from models.user import User
from models.recipe import Recipe

from schemas.user import UserSchema
from schemas.recipe import (
    RecipeSchema, 
    RecipePaginationShema)

user_schema = UserSchema(many=False)
user_schema_public = UserSchema(many=False, exclude=('email',))
user_avatar_schema = UserSchema(only=('avatar_url',))
recipe_list_schema = RecipeSchema(many=True)
recipe_pagination_schema = RecipePaginationShema()

salt_user_activate ='user-activate-salt'


class UserListResource(Resource):
    """
    https://github.com/TrainingByPackt/Python-API-Development-Fundamentals/blob/master/Lesson10/Exercise64/resources/user.py
    """
    
    def __mailgun(self):
        mailgun = MailgunAPI(
            domain = current_app.config['MAILGUN_DOMAIN'],
            api_key = current_app.config['MAILGUN_API_KEY'],
        )

        return mailgun
    
    
    def post(self):
        
        data_in = request.get_json()
        data = user_schema.load(data=data_in)

        if User.get_by_username(data.get('username')):
            return \
                {'message': f"username {data.get('username')} is already used"}, \
                HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return \
                {'message': f"email {data.get('email')} is already registered"}, \
                HTTPStatus.BAD_REQUEST
                
        user = User(**data)
        user.save()
        
        token = generate_token(email=user.email, salt=salt_user_activate)
        subject = 'Hi {}, please verify your Mailgun account'.format(
            user.username)        
        link = url_for(
            'useractivateresource',
            token=token,
            test_key='test_value',
            _external=True)
        
        text = """

Account Verification
        
Hi, Thanks for using our service! Please confirm your registration by clickin on the link: 
        
        {}
        
If you did not sign up for a Mailgun account, you can simply disregard this email. 
        
Happy service!
        
e-Service Team
""".format(link)

        html = render_template(
            'message_verify_email.html',
            company_name='e-Service',
            action_verify_h2 = 'Please verify your email',
            action_verify_text_r1 = 'Thanks for using our service! Please confirm your registration by clickin on the link:',
            action_button_text = 'Verify your email address',
            action_verify_text_r2 = 'If you did not sign up for a e-Service account, you can simply disregard this email. ',
            action_button_href = link,
            footer_about_text ='The best solutions and services from leading experts.',
            footer_contact_info_r1_text = 'Bollwerk 10, 3000, Bern, Switzerland',
            footer_contact_info_r2_text = '+41 800 117 117'
            )
        
        send_email_status = self.__mailgun().send_email(
            to=user.email,
            subject=subject,
            text=text,
            html=html,
        )
        
        return user_schema.dump(user), HTTPStatus.CREATED


class UserActivateResource(Resource):

    
    def get(self, token):
        
        match_object = re.match("[\w\.-]+", token)
        if match_object:
            token = match_object.group(0)
        else:
            return {'message': 'Wrong token'}, HTTPStatus.BAD_REQUEST
        
        email = verify_token(
            token=token, 
            max_age=(30*60), 
            salt=salt_user_activate)
        
        if email is False:
            return {'message': f"Invalid token or token expired"}, \
                HTTPStatus.BAD_REQUEST
        
        user = User.get_by_email(email)
        
        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
        
        if user.is_active:
            return {'message': 'The user account is already activated'}, \
                HTTPStatus.BAD_REQUEST
        
        user.is_active = True
        user.save()
        
        return {}, HTTPStatus.NO_CONTENT


class UserResource(Resource):
    
    @jwt_required(optional=True)
    def get(self, username):
        
        match_object = re.match("[\w\.-]+", username)
        if match_object:
            username = match_object.group(0)
        else:
            
            return {'message': 'Wrong username'}, HTTPStatus.BAD_REQUEST
        
        
        user = User.get_by_username(username)
        
        if User is None:
            
            return {'message': f"user {str(username)} not found"}, \
                HTTPStatus.NOT_FOUND
            
        current_user_id = get_jwt_identity()
        
        if current_user_id == user.id:
            data_out = user_schema.dump(user)

        else:
            data_out = user_schema_public.dump(user)
            
        return data_out, HTTPStatus.OK


class MeResource(Resource):
    
    @jwt_required()
    def get(self):
        
        user = User.get_by_id(id=get_jwt_identity())
        data_out = user_schema.dump(user)
        
        return data_out, HTTPStatus.OK


class UserRecipeListResource(Resource):


    @jwt_required(optional=True)
    @use_kwargs(
        {
            'visibility': fields.Str(),
            'page': fields.Int(missing=1), 
            'per_page': fields.Int(missing=20),
         }, location="querystring")
    def get(self, username, visibility, page, per_page):

        match_username = re.match("[\w\.-]+", username)
        if match_username:
            username = match_username.group(0)
        else:
            
            return {'message': f'Wrong username value'}, \
                HTTPStatus.BAD_REQUEST

        match_visibility = re.match("[\w]+", visibility)
        if match_visibility:
            visibility = match_visibility.group(0)
        else:
            
            return {'message': f'Wrong visibility value'}, \
                HTTPStatus.BAD_REQUEST
        
        recipe_author = User.get_by_username(username=username)
        
        if recipe_author is None:
            
            return {'message': f"user {str(username)} not found"}, \
                HTTPStatus.NOT_FOUND
                
        current_user_id = get_jwt_identity()
        
        if current_user_id != recipe_author.id:
            visibility = 'public'
        
        paginated_recipes = Recipe.get_all_by_user(
            user_id=recipe_author.id, 
            visibility=visibility,
            page=page, 
            per_page=per_page)
        
        return recipe_pagination_schema.dump(paginated_recipes), HTTPStatus.OK
        

class UserAvatarUploadResource(Resource):
    
    @jwt_required()
    def put(self):
        
        file = request.files.get('avatar')
        
        if not file:
            return {'message': "Image with name 'avatar' not found"}, HTTPStatus.BAD_REQUEST
        
        if not image_set.file_allowed(file, file.filename):
            return {'message': "File type not allower"}, HTTPStatus.BAD_REQUEST
        
        current_user = User.get_by_id(id=get_jwt_identity())
        
        if current_user.avatar_image:
            avatar_path = image_set.path(
                folder='avatars', 
                filename=current_user.avatar_image)
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        
        filename = save_image(image=file, folder='avatars')
        current_user.avatar_image = filename
        current_user.save()
        
        clear_cache("/recipes")
        
        return user_avatar_schema.dump(current_user), HTTPStatus.OK
