from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
import os




app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

DATABASE_URL = os.getenv("DATABASE_URL") #or "postgresql://dammietteshoes_user:GJIuYJbYknkoB25LvkKS26Xuu87k4E9V@dpg-ct77r9jtq21c73bkakcg-a.frankfurt-postgres.render.com/dammietteshoes" # Render provides this automatically
if DATABASE_URL.startswith("postgres://"):
    # Render may provide an outdated URI scheme. Update it for compatibility.
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'w5vz1o9vu*rr-mancubpwbh&k6uww&%f3!yr#n^od-zokit#9v'
app.config['COMPRESS_MIMETYPES'] = ['text/html', 'application/json', 'text/css', 'application/javascript']
app.config['COMPRESS_LEVEL'] = 6  # Compression level, from 1 (fastest) to 9 (best compression)
app.config['COMPRESS_MIN_SIZE'] = 500  # Only compress responses larger than this size in bytes
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = os.getenv("CACHE_REDIS_URL")
Compress(app)


login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect unauthorized users to the login page
# Set the database URI
# Configure the database connection

# migrate = Migrate(app, db)


# User model for authentication
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Store hashed passwords in production!

# Form data model
class FormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(10), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # New status field



# class OrderForm(FlaskForm):
#     # Color (Radio Buttons)
#     color = RadioField('اختر اللون', choices=[('bordeau', 'بوردو'), ('beige', 'بيج'), ('black', 'أسود')],
#                        validators=[DataRequired()])

#     # Shoe Size (Radio Buttons)
#     size = RadioField('اختر المقاس', choices=[('36', '36'), ('37', '37'), ('38', '38'), ('39', '39')],
#                       default='36', validators=[DataRequired()])

#     # Name
#     name = StringField('الاسم', validators=[DataRequired(), Length(min=2, max=50)])

#     # Phone Number
#     phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(min=10, max=15)])

#     # State (Dropdown)
#     state = SelectField('اختر ولايتك', choices=[
#         ('', '-- اختر الولاية --'),
#         ('Adrar', 'أدرار'),
#         ('Chlef', 'الشلف'),
#         ('Laghouat', 'الأغواط'),
#         ('Oum El Bouaghi', 'أم البواقي'),
#         ('Batna', 'باتنة'),
#         # Add other states here...
#     ], validators=[DataRequired()])

#     # Address
#     address = StringField('العنوان', validators=[DataRequired(), Length(min=5, max=100)])

#     # Quantity (with default value 1)
#     quantity = IntegerField('الكمية', validators=[DataRequired(), NumberRange(min=1)], default=1)

#     # Submit Button
#     submit = SubmitField('تأكيد الطلبية')
# Load user callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    return user

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  #Replace with hashed password check in production
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('sales'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

# Route to view stored data (restricted to logged-in users)
@app.route('/sales')
@login_required
def sales():
    form_data = FormData.query.all()
    data_with_diff = []

    for data in form_data:
        time_diff = datetime.utcnow() - data.created_at  # Calculate time difference
        data_with_diff.append({
            "id": data.id,
            "name": data.name,
            "phone": data.phone,
            "address": data.address,
            "state": data.state,
            "color": data.color,
            "size": data.size,
            "quantity": data.quantity,
            "created_at": data.created_at,
            "time_diff": time_diff,
            "status" : data.status
        })

    return render_template('sales-table.html', form_data=data_with_diff)

@app.route('/update-status/<int:order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    order = FormData.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status in ['confirmed', 'discarded', 'pending', 'noresponse']:
        order.status = new_status
        db.session.commit()
        flash(f"Order {order_id} status updated to {new_status}.", "success")
    else:
        flash("Invalid status value.", "danger")

    return redirect(url_for('sales'))


# Route for the form
@app.route('/product', methods=['GET', 'POST'])
# @cache.cached(timeout=300)
def product():
    print('iam in the method')
    if request.method == 'POST':
        print('iam in the if')
        # CSRF protection is automatically handled
        # Get form data
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        state = request.form['state']
        color = request.form['color']
        size = request.form['size']
        quantity = request.form['quantity']
        print(name, phone, address, state, color, size, quantity)

        # Save to database
        form_data =FormData(
            name=name,
            phone=phone,
            address=address,
            state=state,
            color=color,
            size=size,
            quantity=quantity,
        )
        db.session.add(form_data)
        db.session.commit()

        flash(f'.شكرا على اختيارنا, سنتواصل معك قريبا ', 'success')
        return redirect(url_for('product'))
    return render_template('product-detail.html')

  


@app.route("/")
def home():
    return render_template('index.html')

# Initialize thedatabase


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)