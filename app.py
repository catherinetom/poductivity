import json
from db import db, User, Pod, Task
from flask import Flask, request
import os

# define db filename
app = Flask(__name__)
db_filename = "poductivity.db"

# setup config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

# initialize app
db.init_app(app)
with app.app_context():
    db.create_all()


# ROUTES TO IMPLEMENT BELOW


# BASE ROUTE

@app.route("/")
def hello():
    """
    Endpoint for printing "<netid> was here!"
    """
    return "" + str(os.environ.get("NETID")) + " was here!"


# USERS ROUTES

#@app.route("/api/users/")
#def get_users():
    #"""
    #Endpoint for getting all users
    #"""
    #return json.dumps({"users": DB.get_all_users()}),200

@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting user by id
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return json.dumps({"Error:" "User not found!"}),404
    return json.dumps(user.serialize()),200

@app.route("/api/users/", methods = ["POST"])
def create_user():
    """
    Endpoint for creating new user
    """
    body = json.loads(request.data)
    new_username = body.get("username")
    new_password = body.get("password")
    new_leader = body.get("leader")
    if not new_username or not new_password or not new_leader:
        return json.dumps({"Required field(s) not supplied."}), 400

    new_user = User(username = new_username, password = new_password, leader = new_leader)
    db.session.add(new_user)
    db.session.commit()
    return json.dumps(new_user.serialize()),201


# POD ROUTES

@app.route("/api/pod/<int:user_id>/", methods = ["POST"])
def create_pod(user_id):
    """
    Endpoint for creating a pod
    """
    body = json.loads(request.data)
    if user_id is None:
        return json.dumps({"error": "pod creator not found"}), 404
    if body.get("name") is None:
        return json.dumps({"Pod name is missing."}), 400
    if body.get("description") is None:
        return json.dumps({"Pod description is missing."}), 400
    pod_creator = User.query.filter_by(id=user_id).first()
    new_pod = Pod(name=body.get("name"), description=body.get("description"))
    db.session.add(new_pod)
    db.session.commit()
    if new_pod is None:
        return json.dumps({"error": "new pod is null."}), 400
    return json.dumps(new_pod.serialize()), 201

@app.route("/api/pod/<int:pod_id>/", methods=["DELETE"])
def delete_pod_by_id(pod_id):
    """
    Endpoint for deleting pod by id
    """

    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    #if the user calling method is pod creator
    db.session.delete(pod)
    db.session.commit()
    return json.dumps(pod.serialize()), 200

@app.route("/api/pod/<int:pod_id>/add/",methods = ["POST"])
def add_user_to_pod(pod_id):
    """
    Endpoint for adding a user to a pod by id
    """
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod is not found."}), 404
    #process request body if pod IS found
    body = json.loads(request.data)
    user = User.query.filter_by(id = body.get("user_id")).first()
    if user is None:
        return json.dumps({"error": "user is null"}), 404
    pod_creator = body.get("pod_creator") #find out if user is pod creator
    if pod_creator: #if the user calling method is pod creator
        pod.users.append(user)
    db.session.commit()

    return json.dumps(pod.serialize()), 200

@app.route("/api/pod/<int:user_id>/delete/",methods = ["DELETE"])
def delete_user_from_pod(pod_id):
    """
    Endpoint for deleting a user from pod by id
    """
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod is not found."}), 404
    #process request body if pod IS found
    body = json.loads(request.data)
    user = User.query.filter_by(id = body.get("user_id")).first()
    if user is None:
        return json.dumps({"error": "user is null"}), 404
    pod_creator = body.get("pod_creator") #find out if user is pod creator
    if pod_creator: #if the user calling method is pod creator
        pod.users.delete(user)
    db.session.commit()

    return json.dumps(pod.serialize()), 200


# TASK ROUTES

@app.route("/api/task/<int:pod_id>/", methods = ["POST"])
def create_task(pod_id):
    """
    Endpoint for creating a task
    request:
    description
    """
    pod=Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error":"Pod not found"}), 404
    body=json.loads(request.data)
    description=body.get("description")
    if description is None:
        return json.dumps({"error": "Some task information is missing"}), 400
    new_task=Task(description=description, pod_id=pod_id)
    db.session.add(new_task)
    db.session.commit()
    return json.dumps(new_task.serialize()), 201

@app.route("/api/users/<int:task_id>/")
def get_task_by_id(task_id):
    """
    Endpoing for getting a task by ID
    """
    task=Task.query.filter_by(id=task_id).first()
    if task is None:
        return json.dumps({"error":"Task not found"}), 404
    return json.dumps(task.serialize()), 201

@app.route("/api/update/<int:task_id>/", methods = ["POST"])
def update_task(task_id):
    """
    Endpoint for updating a task's status
    request:
    status
    """
    task=Task.query.filter_by(id=task_id).first()
    if task is None:
        return json.dumps({"error":"Task not found"}), 404
    body=json.loads(request.data)
    status=body.get("status")
    if status is None:
        return json.dumps({"error":"Incomplete request"}), 400
    task.update_task_status(status)
    db.session.commit()
    return json.dumps(task.serialize()), 201



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
