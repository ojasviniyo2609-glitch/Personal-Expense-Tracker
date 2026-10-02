from flask import Flask, render_template, request, redirect, jsonify, make_response
import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime

app = Flask(__name__)

# ============================================================
# FIREBASE ADMIN SETUP
# ============================================================

RENDER_FIREBASE_FILE = "/etc/secrets/firebase-service-account.json"
LOCAL_FIREBASE_FILE = "firebase-service-account.json"

if os.path.exists(RENDER_FIREBASE_FILE):
    firebase_file = RENDER_FIREBASE_FILE
else:
    firebase_file = LOCAL_FIREBASE_FILE

cred = credentials.Certificate(firebase_file)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ============================================================
# GET LOGGED-IN USER
# ============================================================

def get_logged_in_user():
    user_id = request.cookies.get("user_id")

    if not user_id:
        return None

    try:
        return auth.get_user(user_id)
    except Exception:
        return None


# ============================================================
# HOME / DASHBOARD
# ============================================================

@app.route("/")
def home():

    user = get_logged_in_user()

    if not user:
        return redirect("/login")

    uid = user.uid

    # -----------------------------
    # Get expenses
    # -----------------------------

    expense_ref = (
        db.collection("users")
        .document(uid)
        .collection("expenses")
    )

    expense_docs = expense_ref.stream()

    expenses = []

    for doc in expense_docs:

        data = doc.to_dict()

        data["id"] = doc.id

        expenses.append(data)

    # -----------------------------
    # Get income
    # -----------------------------

    income_ref = (
        db.collection("users")
        .document(uid)
        .collection("income")
    )

    income_docs = income_ref.stream()

    incomes = []

    for doc in income_docs:

        data = doc.to_dict()

        data["id"] = doc.id

        incomes.append(data)

    # -----------------------------
    # Calculate totals
    # -----------------------------

    total_expense = 0

    for expense in expenses:

        try:
            total_expense += float(expense.get("amount", 0))
        except:
            pass

    total_income = 0

    for income in incomes:

        try:
            total_income += float(income.get("amount", 0))
        except:
            pass

    balance = total_income - total_expense

    # -----------------------------
    # Category-wise expenses
    # -----------------------------

    category_totals = {}

    for expense in expenses:

        category = expense.get("category", "Other")

        try:
            amount = float(expense.get("amount", 0))
        except:
            amount = 0

        if category not in category_totals:
            category_totals[category] = 0

        category_totals[category] += amount

    category_expenses = []

    for category, amount in category_totals.items():

        category_expenses.append({
            "category": category,
            "amount": amount
        })

    # -----------------------------
    # Sort newest first
    # -----------------------------

    expenses.sort(
        key=lambda x: str(x.get("expense_date", "")),
        reverse=True
    )

    incomes.sort(
        key=lambda x: str(x.get("income_date", "")),
        reverse=True
    )

    return render_template(
        "index.html",
        expenses=expenses,
        incomes=incomes,
        total_expense=total_expense,
        total_income=total_income,
        balance=balance,
        category_expenses=category_expenses
    )


# ============================================================
# REGISTER PAGE
# ============================================================

@app.route("/register")
def register():

    user = get_logged_in_user()

    if user:
        return redirect("/")

    return render_template("register.html")


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/login")
def login():

    user = get_logged_in_user()

    if user:
        return redirect("/")

    return render_template("login.html")


# ============================================================
# FIREBASE LOGIN
# ============================================================

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
            secure=os.path.exists(RENDER_FIREBASE_FILE),
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


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    response = make_response(
        redirect("/login")
    )

    response.delete_cookie("user_id")

    return response


# ============================================================
# ADD EXPENSE
# ============================================================

@app.route("/add_expense", methods=["POST"])
@app.route("/add-expense", methods=["POST"])
def add_expense():

    user = get_logged_in_user()

    if not user:
        return redirect("/login")

    uid = user.uid

    expense_name = request.form.get("expense_name", "").strip()
    amount = request.form.get("amount", "0").strip()
    category = request.form.get("category", "Other").strip()
    expense_date = request.form.get("expense_date", "").strip()

    if not expense_name:
        expense_name = "Expense"

    try:
        amount = float(amount)
    except:
        amount = 0

    if not expense_date:
        expense_date = datetime.now().strftime("%Y-%m-%d")

    expense_data = {
        "expense_name": expense_name,
        "amount": amount,
        "category": category,
        "expense_date": expense_date,
        "createdAt": firestore.SERVER_TIMESTAMP
    }

    (
        db.collection("users")
        .document(uid)
        .collection("expenses")
        .add(expense_data)
    )

    return redirect("/")


# ============================================================
# ADD INCOME
# ============================================================

@app.route("/add_income", methods=["POST"])
@app.route("/add-income", methods=["POST"])
def add_income():

    user = get_logged_in_user()

    if not user:
        return redirect("/login")

    uid = user.uid

    income_name = request.form.get("income_name", "").strip()
    amount = request.form.get("amount", "0").strip()
    income_date = request.form.get("income_date", "").strip()

    if not income_name:
        income_name = "Income"

    try:
        amount = float(amount)
    except:
        amount = 0

    if not income_date:
        income_date = datetime.now().strftime("%Y-%m-%d")

    income_data = {
        "income_name": income_name,
        "amount": amount,
        "income_date": income_date,
        "createdAt": firestore.SERVER_TIMESTAMP
    }

    (
        db.collection("users")
        .document(uid)
        .collection("income")
        .add(income_data)
    )

    return redirect("/")


# ============================================================
# DELETE EXPENSE
# ============================================================

@app.route("/delete_expense/<expense_id>", methods=["POST", "GET"])
@app.route("/delete-expense/<expense_id>", methods=["POST", "GET"])
def delete_expense(expense_id):

    user = get_logged_in_user()

    if not user:
        return redirect("/login")

    uid = user.uid
    print("LOGGED IN UID:", uid)

    (
        db.collection("users")
        .document(uid)
        .collection("expenses")
        .document(expense_id)
        .delete()
    )

    return redirect("/")


# ============================================================
# DELETE INCOME
# ============================================================

@app.route("/delete_income/<income_id>", methods=["POST", "GET"])
@app.route("/delete-income/<income_id>", methods=["POST", "GET"])
def delete_income(income_id):

    user = get_logged_in_user()

    if not user:
        return redirect("/login")

    uid = user.uid

    (
        db.collection("users")
        .document(uid)
        .collection("income")
        .document(income_id)
        .delete()
    )

    return redirect("/")


# ============================================================
# API - GET USER FINANCIAL SUMMARY
# ============================================================

@app.route("/api/summary")
def api_summary():

    user = get_logged_in_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Not logged in"
        }), 401

    uid = user.uid

    expense_docs = (
        db.collection("users")
        .document(uid)
        .collection("expenses")
        .stream()
    )

    income_docs = (
        db.collection("users")
        .document(uid)
        .collection("income")
        .stream()
    )

    total_expense = 0
    total_income = 0

    for doc in expense_docs:

        data = doc.to_dict()

        try:
            total_expense += float(data.get("amount", 0))
        except:
            pass

    for doc in income_docs:

        data = doc.to_dict()

        try:
            total_income += float(data.get("amount", 0))
        except:
            pass

    balance = total_income - total_expense

    return jsonify({
        "success": True,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "message": "Personal Expense Tracker is running"
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        use_reloader=False
    )