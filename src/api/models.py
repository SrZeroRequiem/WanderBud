import random
from datetime import timezone, datetime
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger
from itsdangerous import URLSafeTimedSerializer as Serializer


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    user_profile = db.relationship('User_Profile', backref='user', lazy=True, cascade='all, delete')
    user_event = db.relationship('Event', backref='owner', lazy=True, cascade='all, delete')
    event_member = db.relationship('Event_Member', backref='user', lazy=True, cascade='all, delete')
    user_private_chats = db.relationship('UsersPrivateChat', backref='user', lazy=True, cascade='all, delete')
    private_chats = db.relationship('PrivateChat', backref='user', lazy=True, cascade='all, delete')
    group_chats = db.relationship('UsersGroupChat', backref='user', lazy=True, cascade='all, delete')
    sender = db.relationship('Message', foreign_keys='Message.sender_id' ,backref='sender', lazy=True, cascade='all, delete')
    receiver = db.relationship('Message', foreign_keys='Message.receiver_id',backref='receiver', lazy=True, cascade='all, delete')
    profile_image = db.relationship('UserProfileImage', backref='user', lazy=True, cascade='all, delete')

    def generate_unique_id(self):
        while True:
            new_id = random.randint(10**9, 10**10 - 1)  # Genera un número aleatorio de 10 dígitos
            if not User.query.filter_by(id=new_id).first():
                return new_id

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        if not self.id:
            self.id = self.generate_unique_id()

    def generate_reset_token(self):
        serializer = Serializer(secret_key=current_app.config['JWT_SECRET_KEY'], salt=current_app.config['SECURITY_PASSWORD_SALT'])
        return serializer.dumps({'id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['JWT_SECRET_KEY'])
        try:
            data = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=84600)
            user_id = data.get('id')
            if user_id:
                user = User.query.get(user_id)
                return user
        except Exception as e:
            print(e)
        return None
    
    def __repr__(self):
        return f'<User ID {self.id} {self.email}>'

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            # do not serialize the password, it's a security breach
        }
        
        
class User_Profile(db.Model):
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    profile_image = db.Column(db.String(250), nullable=False)
    cover_image = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return f'<UserProfile ID {self.user_id} {self.name}>'

    def serialize(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "last_name": self.last_name,
            "birthdate": self.birthdate.strftime("%Y-%m-%d"),
            "location": self.location,
            "description": self.description,
            "profile_image": self.profile_image,
            "cover_image": self.cover_image
        }

class Event_Type(db.Model):
    __tablename__ = 'event_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(250), nullable=False)
    events = db.relationship('Event', primaryjoin='Event.event_type_id==Event_Type.id', backref='event_type')

    def __repr__(self):
        return f'<EventType ID {self.id} {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image
        }

class Event(db.Model):
    __tablename__ = 'event'
     
    id = db.Column(db.BigInteger, primary_key=True)
    owner_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    location_name = db.Column(db.String(250), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    start_datetime = db.Column(db.DateTime(timezone=True), nullable=False)
    end_datetime = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.Enum("Planned","Completed","Canceled","In Progress", name="status"), nullable=False, default="Planned")
    description = db.Column(db.String(250), nullable=True)
    budget_per_person = db.Column(db.Float, nullable=True)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_type.id'), nullable=False)
    members = db.relationship('Event_Member', backref='event', lazy=True, cascade='all, delete')
    private_chats = db.relationship('PrivateChat', backref='event', lazy=True, cascade='all, delete')
    group_chats = db.relationship('GroupChat', backref='event', lazy=True, cascade='all, delete')

    def generate_unique_id(self):
        while True:
            new_id = random.randint(10**9, 10**10 - 1)  # Genera un número aleatorio de 10 dígitos
            if not Event.query.filter_by(id=new_id).first():
                return new_id

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        self.id = self.generate_unique_id()
    
    def actualize_status(self):
        '''This method is used to actualize the status of the event'''
        if self.start_datetime > datetime.now(timezone.utc):
            return "Planned"
        elif self.start_datetime < datetime.now(timezone.utc) and self.end_datetime > datetime.now(timezone.utc):
            return "In Progress"
        elif self.end_datetime < datetime.now(timezone.utc):
            return "Completed"
        else:
            return "Canceled"
    
    def __repr__(self):
        return f'<Event Id {self.id} {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "owner": self.owner_id,
            "name": self.name,
            "location": self.location,
            "location_name": self.location_name,
            "date": self.start_datetime.strftime('%Y-%m-%d %H:%M:%S GMT%z'),
            "status": self.status,
            "description": self.description,
            "budget_per_person": self.budget_per_person,
            "event_type_id": self.event_type_id,
        }

class Event_Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.BigInteger, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    member_status = db.Column(db.Enum("Applied","Owner","Accepted","Rejected", name="member_status"), nullable=False)

    def __repr__(self):
        return f'<EventMember {self.id}>'

    def serialize(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "status": self.member_status
        }
        
class UsersPrivateChat(db.Model):
    '''This table is used to store the users that are part of a private chat'''
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.BigInteger, db.ForeignKey('private_chat.id'), nullable=False)
    
    def __repr__(self):
        return f'<UsersChat {self.id}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_id": self.chat_id
        }
        
class PrivateChat(db.Model):
    '''This table is used to store the private chats between users'''
    id = db.Column(db.BigInteger, primary_key=True)
    event_id = db.Column(db.BigInteger, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    createdAt = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    users_chat = db.relationship('UsersPrivateChat', backref='private_chat', lazy=True, cascade='all, delete')
    messages = db.relationship('Message', backref='private_chat', lazy=True, cascade='all, delete')
    
    def generate_unique_id(self):
        while True:
            new_id = random.randint(10**9, 10**10 - 1)  # Genera un número aleatorio de 10 dígitos
            if not PrivateChat.query.filter_by(id=new_id).first():
                return new_id

    def __init__(self, *args, **kwargs):
        super(PrivateChat, self).__init__(*args, **kwargs)
        self.id = self.generate_unique_id()
    
    def __repr__(self):
        return f'<PrivateChat {self.id}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "createdAt": self.createdAt.strftime('%Y-%m-%d %H:%M:%S GMT%z') # "2021-06-01 12:00:00
        }

class UsersGroupChat(db.Model):
    '''This table is used to store the users that are part of a group chat'''
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.BigInteger, db.ForeignKey('group_chat.id'), nullable=False)
    
    def __repr__(self):
        return f'<UsersGroupChat {self.id}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_id": self.chat_id
        }

class GroupChat(db.Model):
    '''This table is used to store the group chats between users'''
    id = db.Column(db.BigInteger, primary_key=True)
    event_id = db.Column(db.BigInteger, db.ForeignKey('event.id'), nullable=False)
    createdAt = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    users_chat = db.relationship('UsersGroupChat', backref='group_chat', lazy=True, cascade='all, delete')
    messages = db.relationship('Message', backref='group_chat', lazy=True, cascade='all, delete')
    
    def generate_unique_id(self):
        while True:
            new_id = random.randint(10**9, 10**10 - 1)  # Genera un número aleatorio de 10 dígitos
            if not GroupChat.query.filter_by(id=new_id).first():
                return new_id

    def __init__(self, *args, **kwargs):
        super(GroupChat, self).__init__(*args, **kwargs)
        self.id = self.generate_unique_id()
    
    def __repr__(self):
        return f'<GroupChat {self.id}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "createdAt": self.createdAt.strftime('%Y-%m-%d %H:%M:%S GMT%z'), # "2021-06-01 12:00:00 GMT-5"
            "event_id": self.event_id
        }

class Message(db.Model):
    '''This table is used to store the messages between users'''
    id = db.Column(db.Integer, primary_key=True)
    private_chat_id = db.Column(db.BigInteger, db.ForeignKey('private_chat.id'), nullable=True)
    group_chat_id = db.Column(db.BigInteger, db.ForeignKey('group_chat.id'), nullable=True)
    sender_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.String(250), nullable=False)
    group_type = db.Column(db.Enum("Private","Group", name="group_type"), nullable=False)
    sentAt = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deliveredAt = db.Column(db.DateTime(timezone=True), nullable=True)
    readAt = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f'<Message {self.id} Chat {self.sender_id} Type {self.group_type}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "private_chat_id": self.private_chat_id,
            "group_chat_id": self.group_chat_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "sender_img": User_Profile.query.filter_by(user_id=self.sender_id).first().profile_image if User_Profile.query.filter_by(user_id=self.sender_id).first() else None,
            "message": self.message,
            "group_type": self.group_type,
            "sentAt": self.sentAt.strftime('%Y-%m-%d %H:%M:%S GMT%z'),
            "deliveredAt": self.deliveredAt.strftime('%Y-%m-%d %H:%M:%S GMT%z') if self.deliveredAt else None,
            "readAt": self.readAt.strftime('%Y-%m-%d %H:%M:%S GMT%z') if self.readAt else None
        }
    

class UserProfileImage(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<UserProfileImage {self.id} User {self.user_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_path": self.image_path
        }
    
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.BigInteger, db.ForeignKey('event.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('favorite_events', lazy='dynamic'), cascade='all, delete')
    event = db.relationship('Event', backref=db.backref('favorited_by', lazy='dynamic'), cascade='all, delete')

    def __repr__(self):
        return f'<Favorite user_id={self.user_id}, event_id={self.event_id}>'
    
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "user_info": User_Profile.query.filter_by(user_id=self.user_id).first().serialize(), 
            "event_info": Event.query.filter_by(id=self.event_id).first().serialize()
        }
    
    
