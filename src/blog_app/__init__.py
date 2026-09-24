from flask import Flask, request, jsonify
from pymongo import MongoClient
from uuid import uuid4
import bcrypt
import datetime
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
database_url = "mongodb+srv://rohittkori16_db_user:P5mKz3DN3ab4R3rN@cluster0.bzrbwlz.mongodb.net/?appName=Cluster0"


mongo_client = MongoClient(database_url)
mongo_cluster = mongo_client["Blog"]
mongo_database = mongo_cluster["user"]


@app.post("/register")
def handle_register():
    body = request.json
    name = body.get("name")
    email = body.get("email")
    password = body.get("password")

    if not name or not email or not password:
        return {"success": False, "message": "name,email,password are required"}
    if mongo_database.find_one({"email": email}):
        return {"success": False, "message": "email already exists"}
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(14))
    mongo_database.insert_one(
        {"name": name, "email": email, "password": hashed, "blogs": []}
    )
    return jsonify(
        {
            "success": True,
            "message": "succesfully inserted",
        }
    )


@app.post("/login")
def handle_login():
    body = request.json
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        return {"success": False, "message": "email,password are required"}
    user = mongo_database.find_one({"email": email})
    if not user:
        return {"success": False, "message": "email doesnt exists"}
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return {"message": "Invalid email or password"}, 401
    access_token = create_access_token(identity=email)
    return {"message": "Login successful", "access_token": access_token}


@app.post("/add_blog")
@jwt_required()
def handle_add_blog():
    body = request.json
    title = body.get("title")
    content = body.get("content")
    current_user = get_jwt_identity()
    if not title or not content:
        return {"success": False, "message": "title,content are required"}
    print(mongo_database.find_one())
    user = mongo_database.find_one({"email": current_user})
    mongo_database.find_one_and_update(
        {"email": current_user},
        {
            "$push": {
                "blogs": {
                    "id": str(uuid4()),
                    "author": user["name"],
                    "title": title,
                    "content": content,
                    "updated_at": datetime.now(),
                    "status":"drift"
                }
            }
        },
    )
    return {"success": True, "message": "Blog added successfully"}


@app.patch("/edit_blog")
@jwt_required()
def handle_edit_blog():
    body = request.json
    blog_id = body.get("id")
    title = body.get("title")
    content = body.get("content")
    current_user = get_jwt_identity()
    if not blog_id:
        return {"success": False, "message": "blog id is required"}, 400

    if not title or not content:
        return {"success": False, "message": "title, content are required"}, 400

    result = mongo_database.find_one_and_update(
        {"email": current_user, "blogs.id": blog_id},
        {
            "$set": {
                "blogs.$.title": title,
                "blogs.$.content": content,
                "blogs.$.updated_at": datetime.now(),
            }
        },
    )

    if not result:
        return {"success": False, "message": "Blog not found"}, 404

    return {"success": True, "message": "Blog updated successfully"}


if __name__ == "__main__":
    app.run(debug=True)
