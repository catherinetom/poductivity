from flask_sqlalchemy import SQLAlchemy
import random

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
    pod = db.relationship("Pod", secondary=pods_to_users_association_table, back_populates="users")


    def __init__(self, **kwargs):
        """
        Initializes a User object
        """
        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password","")
        self.leader = False

    def serialize(self):
        """
        Serializes a User object
        """
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "leader": self.leader,
            "pod": [a.simple_serialize() for a in self.pod]
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
    users = db.relationship("User", secondary= pods_to_users_association_table, back_populates = "user_pods")


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
    done = db.Column(db.Bool)
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
            "pod_id": self.pod_id,
            "description": self.description,
            "status": self.status
        }

    def update_task_status(self, status):
        """
        updates Task status
        """
        self.done=status
