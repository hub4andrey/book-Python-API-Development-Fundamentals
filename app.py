# from http import HTTPStatus
import os
from pathlib import Path as path

from flask import Flask, request
from flask_migrate import Migrate
from flask_restful import Api
from flask_uploads import configure_uploads
from dotenv import dotenv_values

from config import Config
from extensions import (
    db, 
    jwt,
    image_set,
    cache,
    limiter,
    )
from resources.recipe import (
    RecipeListResource,
    RecipeResource,
    RecipePublishResouce,
    RecipeCoverUploadResource)
from resources.user import (
    UserListResource, 
    UserResource, 
    MeResource,
    UserRecipeListResource,
    UserActivateResource,
    UserAvatarUploadResource)
from resources.token import (
    TokenResource, 
    RefreshResource, 
    RevokeResource, 
    black_list)





app = Flask(__name__)

@limiter.request_filter
def ip_whitelist():
    return request.remote_addr == '127.0.0.1'


def create_app():
    env = os.environ.get('ENV', 'Development')
    if env == 'Production':
        config_str = 'config.ProductionConfig'
    elif env == 'Staging':
        config_str = 'config.StagingConfig'
    else:
        config_str = 'config.DevelopmentConfig'
    
    
    app = Flask(__name__)
    app.config.from_object(config_str)
    
    dot_env = {
        # **os.environ,
        **dotenv_values(path(__file__).parent.resolve() / ".env.prod.web.shared"),  # load shared development variables
        **dotenv_values(path(__file__).parent.resolve() / ".env.prod.web.secret"),  # load sensitive variables    
    }

    app.config.from_mapping(dot_env)
    
    configure_uploads(app, image_set)
    
    register_extensions(app)
    register_resources(app)
    
    return app


def register_extensions(app):
    db.init_app(app)
    migrate = Migrate(app, db)
    
    jwt.init_app(app)
    @jwt.token_in_blocklist_loader

    def check_if_token_in_blacklist(jwt_header, jwt_payload: dict):
        jti = jwt_payload['jti']
        
        return jti in black_list
    
    cache.init_app(app)
    
    limiter.init_app(app)

    
def register_resources(app):
    api = Api(app)

    api.add_resource(RecipeListResource, "/recipes")
    api.add_resource(RecipeResource, "/recipes/<int:recipe_id>")
    api.add_resource(RecipePublishResouce, "/recipes/<int:recipe_id>/publish")
    api.add_resource(RecipeCoverUploadResource, "/recipes/<int:recipe_id>/cover")
    
    
    api.add_resource(TokenResource, "/token")
    api.add_resource(RefreshResource, "/refresh")
    api.add_resource(RevokeResource, "/revoke")
    
    api.add_resource(UserListResource, "/users")
    api.add_resource(UserResource, "/users/<string:username>")
    api.add_resource(MeResource, "/me")
    api.add_resource(UserRecipeListResource, "/users/<string:username>/recipes")
    api.add_resource(UserActivateResource, "/users/activate/<string:token>")
    api.add_resource(UserAvatarUploadResource, "/users/avatar")
    
    @app.before_request
    def before_request():
        pass
    
    @app.after_request
    def after_request(response):
        
        return response


if __name__ == "__main__":
    app = create_app()
    app.run(port=8080)
