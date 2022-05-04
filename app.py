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
    Endpoint for printing hello
    """
    return "hello"


# USERS ROUTES

#@app.route("/api/users/")
#def get_users():
    #"""
    #Endpoint for getting all users
    #"""
    #return json.dumps({"users": DB.get_all_users()}),200
@app.route("/api/user/")
def get_all_users():
    """
    Endpoint for getting all users
    """
    return json.dumps({"users": [u.serialize() for u in User.query.all()]}),200

@app.route("/api/user/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting user by id
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return json.dumps({"Error:" "User not found!"}),404
    return json.dumps(user.serialize()),200

@app.route("/api/user/", methods = ["POST"])
def create_user():
    """
    Endpoint for creating new user
    """
    body = json.loads(request.data)
    new_username = body.get("username")
    new_password = body.get("password")
    if not new_username:
        return json.dumps({"error": "username field not supplied."}), 400
    if not new_password:
        return json.dumps({"error": "password field not supplied."}), 400

    new_user = User(username = new_username, password = new_password)
    db.session.add(new_user)
    db.session.commit()
    return json.dumps(new_user.serialize()),201

@app.route("/api/user/<int:user_id>/", methods = ["POST"])
def join_pod(user_id):
    """
    Endpoint for a User to join a Pod, using pod id and a join code.

    request:
    user_id
    join_code
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return json.dumps({"error": "user is null"}), 404
    body = json.loads(request.data)
    join_code=body.get("join_code")
    pod = Pod.query.filter_by(join_code=join_code).first()
    if pod is None:
        return json.dumps({"error": "No pod with that join code."}), 404
    user.podID=pod.id
    db.session.commit()

    return json.dumps(user.serialize()), 200

@app.route("/api/user/<int:user_id>/delete/",methods = ["DELETE"])
def delete_user_from_pod(user_id):
    """
    Endpoint for deleting a user from pod by id
    """
    body = json.loads(request.data)
    userDeleting = User.query.filter_by(id = user_id).first()
    if userDeleting is None:
        return json.dumps({"error": "user_id is null"}), 404
    userToDelete = User.query.filter_by(id = body.get("user_to_delete")).first()
    if userToDelete is None:
        return json.dumps({"error": "user_to_delete is null"}), 404
    podOfDeleter = Pod.query.filter_by(id=userDeleting.podID).first()
    podOfDeleting = Pod.query.filter_by(id=userToDelete.podID).first()
    if (podOfDeleting or podOfDeleter) is None:
        return json.dumps({"error": "one of pods is not found."}), 404
    if podOfDeleting.serialize() != podOfDeleter.serialize():
        return json.dumps({"error": "Not allowed!"}), 400
    if userDeleting.leader == True:
        userToDelete.podID=None
        db.session.commit()

    return json.dumps(userToDelete.serialize()), 200

# POD ROUTES

@app.route("/api/pod/")
def get_all_pods():
    """
    Endpoint for getting all pods
    """
    return json.dumps({"pods": [p.serialize() for p in Pod.query.all()]}),200

@app.route("/api/pod/<int:pod_id>/")
def get_pod(pod_id):
    """
    Endpoint for getting a pod by id
    """
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    return json.dumps(pod.serialize()), 200

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
    #in here, add the pod to the User object
    new_pod = Pod(name=body.get("name"), description=body.get("description"))
    db.session.add(new_pod)
    db.session.commit()
    if new_pod is None:
        return json.dumps({"error": "new pod is null."}), 400
    return json.dumps(new_pod.serialize()), 201

@app.route("/api/pod/totaltasks/<int:pod_id>/")
def pod_total_tasks(pod_id):
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    total_tasks = 0
    for t in Task.query.all():
        if t.pod_id == pod_id:
            total_tasks=total_tasks+1
    return json.dumps({"total tasks": total_tasks}), 201

@app.route("/api/pod/taskscompleted/<int:pod_id>/")
def pod_tasks_completed(pod_id):
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    tasks_completed = 0
    for t in Task.query.all():
        if t.pod_id == pod_id:
            if t.status == True:
                tasks_completed=tasks_completed+1
    return json.dumps({"tasks completed": tasks_completed}), 201

@app.route("/api/pod/tasksincomplete/<int:pod_id>/")
def pod_tasks_incompleted(pod_id):
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    tasks_incomplete = 0
    for t in Task.query.all():
        if t.pod_id == pod_id:
            if t.status == False:
                tasks_incomplete=tasks_incomplete+1
    return json.dumps({"tasks incomplete": tasks_incomplete}), 201



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

@app.route("/api/task/<int:task_id>/")
def get_task_by_id(task_id):
    """
    Endpoing for getting a task by ID
    """
    task=Task.query.filter_by(id=task_id).first()
    if task is None:
        return json.dumps({"error":"Task not found"}), 404
    return json.dumps(task.serialize()), 201

@app.route("/api/task/update/<int:task_id>/", methods = ["POST"])
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
    status=body.get("done")
    if status is None:
        return json.dumps({"error":"Incomplete request"}), 400
    task.status=status
    db.session.commit()
    return json.dumps(task.serialize()), 201



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
