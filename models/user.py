from extensions import db


class User(db.Model):
    """
    https://github.com/TrainingByPackt/Python-API-Development-Fundamentals/blob/master/Lesson10/Exercise64/models/user.py
    """
    
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200))
    avatar_image = db.Column(db.String(100), default=None) # avatar image_filename
    is_active = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    
    recipes =  db.relationship('Recipe', backref='user')

    
    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    
    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
    
    
    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    