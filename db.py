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

class Pod(db.Model):
    """
    Pod model
    Has a one-to-many relationship with User model
    Has a one-to-many relationship with Task model
    Has a one-to-many relationship with Invite model
    """
    __tablename__ = "pod"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    pod_creator = db.Column(db.User, nullable=False)
    total_completed = db.Column(db.Integer, nullable=False)
    tasks = db.relationship("Task", cascade="delete")
    users = db.relationship("User", secondary= pods_to_users_association_table, back_populates = "user_pods")
    

    def __init__(self, **kwargs):
        """
        Initialize Pod object
        """
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.pod_creator = ("pod_creator", "")
        self.total_completed = 0

    def serialize(self):
        """
        Serialize Pod object
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pod_creator": self.pod_creator,
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
            "pod_creator": self.pod_creator,
            "total_completed": self.total_completed,       
        }

class Task(db.Model):
    """
    Task model
    """
