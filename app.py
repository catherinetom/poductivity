import json
from db import db, User, Pod, Task
from flask import Flask, request
import users_dao
import os
import datetime

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

def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    
    if auth_header is None:
        return False, json.dumps({"error": "Missing authorization header"}),404
    
    bearer_token = auth_header.replace("Bearer","").strip()

    return True, bearer_token


# AUTHENTICATION


@app.route("/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    leader = body.get("leader")
    tasks_completed = body.get("tasks_completed")

    if username is None or password is None or leader is None or tasks_completed:
        return json.dumps({"error": "Missing username or password or leader or tasks_completed"}),404
    
    if leader != 0:
        return json.dumps({"error": "Can only be a member upon registration. Join a pod to be a leader!"})
    
    if tasks_completed != 0:
        return json.dumps({"error": "Don't cheat, everyone starts with 0!"})
    
    was_successful, user = users_dao.create_user(username,password,leader)

    if not was_successful:
        return json.dumps({"error": "User already exists"}),404
    
    return json.dumps(
        {
            "session_token": user.session_token, 
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }),201

@app.route("/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")

    if username is None or password is None:
        return json.dumps({"error": "Missing username or password"}),400
    
    was_successful, user = users_dao.verify_credentials(username,password)

    if not was_successful:
        return json.dumps({"error": "Incorrect username or password"}),401
    
    return json.dumps(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token,
            "login": "successful"

        }),201


@app.route("/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    was_successful, update_token = extract_token(request)

    if not was_successful:
        return update_token
    
    try:
        user = users_dao.renew_session(update_token)
    except Exception as e:
        return json.dumps(f"Invalid update token: {str(e)}"),404

    return json.dumps(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }),201

@app.route("/secret/", methods=["GET"])
def secret_message():
    """
    Endpoint for verifying a session token and returning a secret message
    """
    was_successful, session_token = extract_token(request)

    if not was_successful:
        return session_token
    
    user = users_dao.get_user_by_session_token(session_token)
    if not user or not user.verify_session_token(session_token):
        return json.dumps({"error": "Invalid session token"}),404
    
    return json.dumps(
        {"message": "You have sucessfully implemented sessions!"}),201
    

@app.route("/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user 
    """
    was_successful, session_token = extract_token(request)

    if not was_successful:
        return session_token
    
    user = users_dao.get_user_by_session_token(session_token)

    if not user or not user.verify_session_token(session_token):
        return json.dumps({"error": "Invalid session token"}),404
    
    user.session_expiration = datetime.datetime.now()
    db.session.commit()

    return json.dumps({
        "message": "You have successfully logged out"
    }),201

# USERS ROUTES


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
        return json.dumps({"error": "user not found"}),404
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
    new_user = User(username = new_username, password = new_password,leader=0,tasks_completed = 0)
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
    if user.podID != None:
        return json.dumps({"error": "user is already in pod"}), 404
    body = json.loads(request.data)
    join_code=body.get("join_code")
    pod = Pod.query.filter_by(join_code=join_code).first()
    if pod is None:
        return json.dumps({"error": "no pod with that join code."}), 404
    user.podID=pod.id
    db.session.commit()
    return json.dumps(user.serialize()), 200


@app.route("/api/user/taskscompleted/<int:user_id>/")
def user_tasks_completed(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return json.dumps({"error": "user not found"}), 404
    tasks_completed = 0
    for t in Task.query.all():
        if t.completer_id == user_id:
            if t.status == True:
                tasks_completed=tasks_completed+1
    return json.dumps({"tasks completed by user": tasks_completed}), 201


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
        return json.dumps({"error": "not allowed"}), 400
    if userDeleting.leader == True:
        userToDelete.podID=None
        userToDelete.tasks_completed=0
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

@app.route("/api/pod/joincode/<int:pod_id>/")
def get_pod_joincode(pod_id):
    """
    Endpoint for getting a pod's join code
    """
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    return json.dumps(pod.join_code), 200


@app.route("/api/pod/<int:user_id>/", methods = ["POST"])
def create_pod(user_id):
    """
    Endpoint for creating a pod
    """
    user = User.query.filter_by(id = user_id).first()
    if user_id is None:
        return json.dumps({"error": "pod creator not found"}), 404
    if user.podID != None:
        return json.dumps({"error": "user is already in pod"}), 404
    body = json.loads(request.data)
    if body.get("name") is None:
        return json.dumps({"error": "pod name field not supplied"}), 400
    if body.get("description") is None:
        return json.dumps({"error": "pod description field not supplied"}), 400
    new_pod = Pod(name=body.get("name"), description=body.get("description"))
    db.session.add(new_pod)
    db.session.commit()
    if new_pod is None:
        return json.dumps({"error": "new pod is null."}), 400
    user.podID=new_pod.id
    user.leader = True
    db.session.commit()
    return json.dumps(new_pod.serialize()), 201


@app.route("/api/pod/alluser/<int:pod_id>/")
def pod_all_users(pod_id):
    """
    Endpoint for getting all users of a pod
    """
    return json.dumps({"users": [u.serialize() for u in User.query.filter(User.podID == pod_id).all()]}),200


@app.route("/api/pod/leaderboard/<int:pod_id>/")
def pod_leaderboard(pod_id):
    """
    Endpoint for returning all users of a pod by number of tasks completed
    """  
    orderedUsers = User.query.order_by(User.tasks_completed).all()
    users = []
    for user in orderedUsers:
        if user.podID == pod_id:
            users.append(user)
    length = len(users)
    user1st= users[length-1] 
    user2ndString = "second: invite more users!"
    user3rdString = "third: invite more users!"
    user1stString = "first: " + user1st.username + ", tasks done: " + str(user1st.tasks_completed)
    if length > 1:
        user2nd= users[length-2]
        user2ndString = "second: " + user2nd.username + ", tasks done: " + str(user2nd.tasks_completed)
    if length > 2:
        user3rd= users[length-3]
        user3rdString = "third: " + user3rd.username + ", tasks done: " + str(user3rd.tasks_completed)
    userslist = [user1stString, user2ndString, user3rdString]
    return json.dumps({"top users": userslist}),200


@app.route("/api/pod/totaltasks/<int:pod_id>/")
def pod_total_tasks(pod_id):
    """
    Endpoint for getting total number of tasks of a pod
    """
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
    """
    Endpoint for getting total number of completed tasks of a pod
    """
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
    """
    Endpoint for getting total number of incomplete tasks of a pod
    """
    pod = Pod.query.filter_by(id=pod_id).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    tasks_incomplete = 0
    for t in Task.query.all():
        if t.pod_id == pod_id:
            if t.status == False:
                tasks_incomplete=tasks_incomplete+1
    return json.dumps({"tasks incomplete": tasks_incomplete}), 201


@app.route("/api/pod/<int:user_id>/", methods=["DELETE"])
def delete_pod_by_id(user_id):
    """
    Endpoint for deleting pod by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user_id is None:
        return json.dumps({"error": "pod creator not found"}), 404
    body = json.loads(request.data)
    if body.get("pod_id") is None:
        return json.dumps({"error": "pod to delete not specified"}), 400
    pod = Pod.query.filter_by(id=body.get("pod_id")).first()
    if pod is None:
        return json.dumps({"error": "pod not found"}), 404
    if user.leader == False:
        return json.dumps({"error": "not allowed"}), 400
    db.session.delete(pod)
    db.session.commit()
    return json.dumps(pod.serialize()), 200

# TASK ROUTES

@app.route("/api/task/<int:user_id>/", methods = ["POST"])
def create_task(user_id):
    """
    Endpoint for creating a task
    request:
    description
    """
    user=User.query.filter_by(id=user_id).first()
    if user is None:
        return json.dumps({"error": "user not found"}), 404
    body=json.loads(request.data)
    description=body.get("description")
    if description is None:
        return json.dumps({"error": "task description field not supplied"}), 400
    new_task=Task(description=description, pod_id=user.podID, creator_id=user.id)
    print(new_task.creator_id)
    db.session.add(new_task)
    print(new_task.creator_id)
    db.session.commit()
    print(new_task.creator_id)
    if new_task is None:
        return json.dumps({"error": "new task is null."}), 400
    return json.dumps(new_task.serialize()), 201

@app.route("/api/task/<int:task_id>/")
def get_task_by_id(task_id):
    """
    Endpoing for getting a task by ID
    """
    task=Task.query.filter_by(id=task_id).first()
    if task is None:
        return json.dumps({"error": "task not found"}), 404
    return json.dumps(task.serialize()), 201

@app.route("/api/task/update/<int:user_id>/", methods = ["POST"])
def update_task(user_id):
    """
    Endpoint for updating a task's status
    request:
    status
    """
    body=json.loads(request.data)
    if body.get("task_id") is None:
        return json.dumps({"error": "task not specified"}), 400
    task=Task.query.filter_by(id=body.get("task_id")).first()
    if task is None:
        return json.dumps({"error":"task not found"}), 404
    user=User.query.filter_by(id=user_id).first()
    if user is None:
        return json.dumps({"error": "user not found"}), 404
    status=body.get("done")
    if status is None:
        return json.dumps({"error":"incomplete request"}), 400
    task.status = status
    task.completer_id = user.id
    user.tasks_completed = user.tasks_completed+1
    db.session.commit()
    return json.dumps(task.serialize()), 201



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
