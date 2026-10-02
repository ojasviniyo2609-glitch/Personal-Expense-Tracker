from flask import Flask, render_template, request, redirect, jsonify, make_response
import os
import firebase_admin
from firebase_admin import credentials, auth, firestore

app = Flask(__name__)

# --------------------------------------------------
# Firebase Admin SDK
# --------------------------------------------------

# Render Secret File path
render_secret_file = "/etc/secrets/firebase-service-account.json"

# Local development file
local_secret_file = "firebase-service-account.json"

if os.path.exists(render_secret_file):
    # Running on Render
    cred = credentials.Certificate(render_secret_file)
else:
    # Running locally
    cred = credentials.Certificate(local_secret_file)

firebase_admin.initialize_app(cred)

db = firestore.client()


# --------------------------------------------------
# Check logged-in user
# --------------------------------------------------

def get_logged_in_user():
    user_id = request.cookies.get("user_id")

    if not user_id:
        return None

    try:
        user = auth.get_user(user_id)
        return user
    except Exception:
        return None


# --------------------------------------------------
# Home / Expense Dashboard
# --------------------------------------------------

@app.route("/")
def home():
    user = get_logged_in_user()

    if not user:
        return redirect("/login")

    return render_template(
        "index.html",
        expenses=[],
        total_expense=0,
        category_expenses=[]
    )


# --------------------------------------------------
# Register
# --------------------------------------------------

@app.route("/register")
def register():
    return render_template("register.html")


# --------------------------------------------------
# Login
# --------------------------------------------------

@app.route("/login")
def login():
    user = get_logged_in_user()

    if user:
        return redirect("/")

    return render_template("login.html")


# --------------------------------------------------
# Firebase Session Login
# --------------------------------------------------

@app.route("/sessionLogin", methods=["POST"])
def session_login():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    id_token = data.get("idToken")

    if not id_token:
        return jsonify({
            "success": False,
            "message": "ID token is missing"
        }), 400

    try:

        decoded_token = auth.verify_id_token(id_token)

        uid = decoded_token["uid"]

        response = make_response(
            jsonify({
                "success": True,
                "message": "Login successful"
            })
        )

        response.set_cookie(
            "user_id",
            uid,
            httponly=True,
            secure=True if os.path.exists(render_secret_file) else False,
            samesite="Lax"
        )

        return response

    except Exception as error:

        print("Firebase login error:")
        print(error)

        return jsonify({
            "success": False,
            "message": "Invalid Firebase token"
        }), 401


# --------------------------------------------------
# Logout
# --------------------------------------------------

@app.route("/logout")
def logout():

    response = make_response(
        redirect("/login")
    )

    response.delete_cookie("user_id")

    return response


# --------------------------------------------------
# Run App
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        use_reloader=False
    )