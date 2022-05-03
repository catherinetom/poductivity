import datetime
import hashlib
import os
import random


from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

pods_to_users_association_table = db.Table(
    "pods_to_users_association",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("pod_id", db.Integer, db.ForeignKey("pod.id"))
)

#implement database model classes

class User(db.Model):
    """
    User model
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)
    leader = db.Column(db.Boolean, nullable = False)
    pod = db.Column(db.Integer, db.ForeignKey("pod.id", ondelete="SET NULL"))


    def __init__(self, **kwargs):
        """
        Initializes a User object
        """
        # name, netid, leader
        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password","")
        self.leader = False
    
    def serialize(self):
        """
        Serializes a User object
        """
        pod = None
        if self.pod is not None:
            pod = self.pod.simple_serialize()
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "leader": self.leader,
            "pod": pod
        }

    def simple_serialize(self):
        """
        Serializes a User object without pod
        """
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "leader": self.leader
        }

class Pod(db.Model):
    """
    Pod model
    Has a one-to-many relationship with User model
    Has a one-to-many relationship with Task model
    """
    __tablename__ = "pod"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    join_code = db.Column(db.String, nullable = False)
    total_completed = db.Column(db.Integer, nullable=False)
    tasks = db.relationship("Task", cascade="delete")
    users = db.relationship("User")


    def __init__(self, **kwargs):
        """
        Initialize Pod object
        """
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.join_code = random.randint(1000,9999)
        self.total_completed = 0

    def serialize(self):
        """
        Serialize Pod object
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "total_completed": self.total_completed,
            "join_code": self.join_code,
            "tasks": [t.simple_serialize() for t in self.tasks],
            "users": [u.simple_serialize() for u in self.users],
        }

    def simple_serialize(self):
        """
        Serialize Pod object w/o tasks or users
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "join_code": self.join_code,
            "total_completed": self.total_completed,
        }


class Task(db.Model):
    """
    Task model
    Has a one-to-many relationship with Pod
    """
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    description = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean)
    pod_id=db.Column(db.Integer, db.ForeignKey("pod.id"), nullable=False)

    def __init__(self, **kwargs):
        """
        initialize a Task object
        """
        self.description=kwargs.get("description")
        self.done=kwargs.get("done", False)

    def serialize(self):
        """
        serialize Task object
        """
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "pod_id": self.pod_id
        }

    def update_task_status(self, status):
        """
        updates Task status
        """
        self.done=status
