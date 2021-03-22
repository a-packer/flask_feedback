from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, UserLoginForm, FeedbackForm, DeleteForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route('/')
def root():
    return redirect('/register')

@app.route('/feedback')
def all_feedback():

    if "username" not in session:
        flash("You need to login!", "danger")
        return redirect('/login')

    all_feedback = Feedback.query.all()
    form = DeleteForm()
    return render_template('all_feedback.html', all_feedback=all_feedback, form=form)


@app.route('/register', methods=['GET', 'POST'])
def register_user():

    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another')
            return render_template('register.html', form=form)

        session['username'] = new_user.username
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect(f'/users/{username}')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():

    form = UserLoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "sucess")
            session['username'] = user.username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Delete User."""

    user = User.query.get_or_404(username)
    if "username" not in session or username != session['username']:
        flash('Not Authorized', "danger")
        return redirect(f'users/{current_user}')

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(user)
        db.session.commit()

    session.pop('username')
    flash('Your User Is Deleted along with all Feedback. Thanks for playing!', "info")
    return redirect("/feedback")

@app.route('/users/<username>', methods=['GET'])
def open_user_page(username):

    if "username" not in session:
        flash("You need to login!", "danger")
        return redirect('/register')

    elif session['username'] == username:
        user = User.query.get_or_404(username)

        form = DeleteForm()
        return render_template('user_page.html', user=user, form=form)

    else:
        flash("You can't look at their info", "danger")
        return redirect('/feedback')

@app.route('/logout', methods=['GET'])
def logout_user():
    session.pop('username')
    flash("Goodbye. Come back again soon!", "danger")
    return redirect('/')



@app.route('/feedback/<int:feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show Update Feedback form and process it."""

    feedback = Feedback.query.get_or_404(feedback_id)
    username = feedback.username

    if "username" not in session or username != session['username']:
        flash("Not Authorized to make edit's to other users feeback", "danger")
        current_user = session['username']
        return redirect(f'users/{current_user}')

    form = FeedbackForm(obj=feedback)
    
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("edit_feedback.html", form=form, feedback=feedback)



@app.route('/feedback/<int:feedback_id>/delete', methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get_or_404(feedback_id)
    if "username" not in session:
        flash('Not Authorized. Need to Login', "danger")
        return redirect('/login')

    if feedback.username != session['username']:
        flash("Not Authorized To Delete Another User's Feedback", "danger")
        current_user = session['username']
        return redirect(f'users/{current_user}')

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    """Show add-feedback form and process it."""

    user = User.query.get_or_404(username)

    if "username" not in session or username != session['username']:
        flash('Not Authorized', "danger")
        return redirect(f"/users/{session['username']}")

    form = FeedbackForm()
    
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, username=username)

        db.session.add(feedback)
        db.session.commit()

        all_feedback = Feedback.query.all()
        for feedback in all_feedback:
            print(feedback.title)

        form = DeleteForm()
        return render_template('user_page.html', user=user, form=form)

    else:
        return render_template("add_feedback.html", form=form, username=username)
     

