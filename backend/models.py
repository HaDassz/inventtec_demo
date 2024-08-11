import jwt
from flask import current_app, abort
import time
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer,  index=True, primary_key=True,)
    username = Column(String, index=True)
    password = Column(String)
    email = Column(String, index=True, unique=True)
    registered_date = Column(DateTime)

    def get_jwt(self, expire=3600):
        encoded = jwt.encode(
            {
                'email': self.email,
                'exp': time.time() + expire
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        print(encoded)
        return encoded
    