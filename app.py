from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


def get_db_connection():
    connection = sqlite3.connect("expenses.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        expense_name = request.form["expense_name"]
        amount = request.form["amount"]
        category = request.form["category"]
        expense_date = request.form["expense_date"]

        connection = get_db_connection()

        connection.execute("""
            INSERT INTO expenses
            (expense_name, amount, category, expense_date)
            VALUES (?, ?, ?, ?)
        """, (expense_name, amount, category, expense_date))

        connection.commit()
        connection.close()

        return redirect("/")


    connection = get_db_connection()


    expenses = connection.execute("""
        SELECT * FROM expenses
        ORDER BY expense_date DESC, id DESC
    """).fetchall()


    total_expense = connection.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """).fetchone()[0]


    category_expenses = connection.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()


    connection.close()


    return render_template(
        "index.html",
        expenses=expenses,
        total_expense=total_expense,
        category_expenses=category_expenses
    )


@app.route("/delete/<int:id>")
def delete_expense(id):

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM expenses WHERE id = ?",
        (id,)
    )

    connection.commit()
    connection.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)