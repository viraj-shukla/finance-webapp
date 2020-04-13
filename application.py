import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
# API_KEY=pk_872ed2a293824a41be8dba0384402532


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    print(str(session["user_id"]))

    # Finds current cash
    cash = float(db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"])

    # Finds value of stocks
    purchases = db.execute("SELECT symbol, shares FROM purchases WHERE id=:id", id=session["user_id"])

    stock_value = 0
    # Removes purchases for the same stock, & adds current share price and total stock value
    for purchase in purchases:
        for p in purchases[purchases.index(purchase)+1:]:
            if purchase["symbol"] == p["symbol"]:
                purchase["shares"] = purchase["shares"] + p["shares"]
                purchases.remove(p)
        purchase["current_price"] = lookup(purchase["symbol"])["price"]
        purchase["total_value"] = purchase["shares"] * purchase["current_price"]
        stock_value = stock_value + purchase["total_value"]

    net_value = cash + stock_value

    return render_template("index.html", cash=cash, net_value=net_value, purchases=purchases)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Get symbol
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("symbol is blank", 403)

        # Get number of shares
        shares = request.form.get("shares")
        try:
            shares = int(shares)
            if shares < 0:
                return apology("invalid shares", 403)
        except:
            return apology("invalid shares", 403)

        # Find share price
        try:
            share_price = lookup(symbol)["price"]
        except:
            return apology("invalid symbol", 403)

        # Get user's cash
        cash = float(db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"])

        # Find total cost of purchase
        total_purchase = float(shares) * share_price

        # Aborts if user doesn't have enough cash, else updates databases
        if total_purchase > cash:
            return apology("not enough money", 403)
        else:
            db.execute("INSERT INTO purchases (id, symbol, shares, share_price) VALUES (:id, :symbol, :shares, :share_price)",
                        id=session["user_id"], symbol=symbol.upper(), shares=shares, share_price=share_price)
            db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash-total_purchase, id=session["user_id"])

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    #return jsonify('hey bb')

    valid = True

    username = request.args.get("username")
    if len(username) < 1:
        valid = False

    existing_names = db.execute("SELECT username FROM users")
    for name in existing_names:
        if name["username"] == username:
            valid = False

    return jsonify(valid)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    purchases = db.execute("SELECT date, symbol, shares, share_price FROM purchases WHERE id=:id", id=session["user_id"])

    for purchase in purchases:
        if purchase["shares"] < 0:
            purchase["type"] = "Sold"
            purchase["shares"] = -1 * purchase["shares"]
        else:
            purchase["type"] = "Bought"
            purchase["share_price"] = -1 * purchase["share_price"]

    return render_template("history.html", purchases=purchases)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)["price"]

        return render_template("quoted.html", symbol=symbol.upper(), quote=quote)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks username field
        if not username:
            return apology("username blank", 403)
        elif len(db.execute("SELECT * FROM users WHERE username = :username",
                            username=username)) != 0:
            return apology("username already exists", 403)

        # Checks password fields
        if not password or not confirmation:
            return apology("password and/or confirmation is blank", 403)
        elif password != confirmation:
            return apology("passwords do not match", 403)

        # Inserts user into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=generate_password_hash(password))

        # Remember which user has logged in
        session["user_id"] = db.execute("SELECT id FROM users WHERE username=:username", username=username)[0]["id"]
        print(str(session["user_id"]))

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        # Checks symbol & shares
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("invalid symbol", 403)

        shares = request.form.get("shares")
        try:
            shares = int(shares)
            if shares < 0:
                return apology("invalid shares", 403)
        except:
            return apology("invalid shares", 403)

        # Get user's number of shares for that stock
        current_shares = db.execute("SELECT shares FROM purchases WHERE id=:id AND symbol=:symbol", id=session["user_id"], symbol=symbol)
        if len(current_shares) > 1:
            for share in current_shares[1:]:
                current_shares[0]["shares"] = current_shares[0]["shares"] + share["shares"]
        current_shares = current_shares[0]["shares"]

        # Aborts if user doesn'y have enough (or any) shares
        if current_shares <= 0 or current_shares < shares:
            return apology("not enough shares", 403)

        share_price = lookup(symbol)["price"]
        total_profit = shares * share_price
        cash = float(db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"])

        # Update databases
        db.execute("INSERT INTO purchases (id, symbol, shares, share_price) VALUES (:id, :symbol, :shares, :share_price)",
                        id=session["user_id"], symbol=symbol.upper(), shares=-1*shares, share_price=share_price)
        db.execute("UPDATE users SET cash=:cash WHERE id=:id", cash=cash+total_profit, id=session["user_id"])

        return redirect("/")
    else:
        symbols = db.execute("SELECT symbol FROM purchases WHERE id=:id", id=session["user_id"])
        for i in range(0, len(symbols)):
            symbols[i] = symbols[i]["symbol"]
        symbols = list(set(symbols))
        return render_template("sell.html", symbols=symbols)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
