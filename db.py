import datetime
import hashlib
import os
import random
import bcrypt


from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """
    User model
    Has a many-to-one relationship with Pod
    Has a one-to-many relationship with Task 
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)
    leader = db.Column(db.Boolean, nullable = False)
    tasks_completed = db.Column(db.Integer, nullable = False)
    podID = db.Column(db.Integer, db.ForeignKey("pod.id", ondelete="SET NULL"))

    def __init__(self, **kwargs):
        """
        Initializes a User object
        """
        # name, netid, leader
        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password","")
        self.tasks_completed = 0
        self.leader = False
        self.renew_session()
    
    def serialize(self):
        """
        Serializes a User object
        """
        pod = Pod.query.filter_by(id = self.podID).first()
        pod_serialized = None
        if pod is not None:
            pod_serialized = pod.simple_serialize() #pod is the podID, we want the pod that the podID references
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "tasks_completed": self.tasks_completed,
            "leader": self.leader,
            "pod": pod_serialized,
        }

    def simple_serialize(self):
        """
        Serializes a User object without pod or tasks
        """
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "tasks_completed": self.tasks_completed,
            "leader": self.leader
        }
    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        """
        Renews the sessions, i.e.
        1. Creates a new session token
        2. Sets the expiration time of the session to be a day from now
        3. Creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return password == self.password

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token


class Pod(db.Model):
    """
    Pod model
    Has a one-to-many relationship with User 
    Has a one-to-many relationship with Task 
    """
    __tablename__ = "pod"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    join_code = db.Column(db.String, nullable = False)
    tasks = db.relationship("Task", cascade="delete")


    def __init__(self, **kwargs):
        """
        Initialize Pod object
        """
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.join_code = random.randint(1000,9999)

    def serialize(self):
        """
        Serialize Pod object
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "join_code": self.join_code,
            "tasks": [t.serialize() for t in self.tasks],
        }

    def simple_serialize(self):
        """
        Serialize Pod object w/o tasks
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "join_code": self.join_code,
        }


class Task(db.Model):
    """
    Task model
    Has a many-to-one relationship with Pod
    Has a many-to-one relationship with User
    """
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    description = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    pod_id=db.Column(db.Integer, db.ForeignKey("pod.id"), nullable=False)
    creator_id=db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    completer_id=db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __init__(self, **kwargs):
        """
        initialize a Task object
        """
        self.description=kwargs.get("description")
        self.pod_id=kwargs.get("pod_id")
        self.creator_id=kwargs.get("creator_id")
        self.completer_id=kwargs.get("completer_id")
        self.status = False

    def serialize(self):
        """
        serialize Task object
        """
        pod = Pod.query.filter_by(id = self.pod_id).first()
        creator = User.query.filter_by(id = self.creator_id).first().username
        completer = User.query.filter_by(id = self.completer_id).first()
        completer_user = None
        if completer is not None:
            completer_user = completer.username
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "pod": pod.name,
            "created by": creator,
            "completed by": completer_user
        }
