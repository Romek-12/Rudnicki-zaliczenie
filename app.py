from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)

# Konfiguracaja

app.config['SECRET_KEY'] = 'unikalny klucz do szyfrowania sesji' # klucz do szyfrowania ciasteczek
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' # ścieżka do pliku bazy danych
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Uruchamianie bazy danych i logowania

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Tu przekierowany użytkownik, który się nie zalogouje, a wejdzie do koszyka
login_manager.login_message = 'Wymagane zalogowanie.'
login_manager.login_message_category = 'warning'

# MODELE BAZY DANYCH

# USER to tabela użytkowników w bazie danych
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    time = db.Column(db.String(5), nullable=False)   # Format: HH:MM
    status = db.Column(db.String(20), default='zaplanowana')  # zaplanowana / odbyta / anulowana
    
    # Relacja do użytkownika
    user = db.relationship('User', backref='visits')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Wymagana funkcja przez Flask-Login
# Mówi systemowi: jak masz ID w ciasteczku, to znajdź tego użytkownika w bazie.

class Product:
    def __init__(self, id, name, price, image_url):
        self.id = id
        self.name = name
        self.price = price
        self.image_url = image_url

class Koszyk:
    def __init__(self):
        # Koszyk przechowuje listę produktów
        self.items = []
    def dodaj_do_koszyka(self, product):
        self.items.append(product)

    def oblicz_total(self):
        # Sumuje ceny produktów w koszyku

        total = sum(item.price for item in self.items)
        return total

    def zapisz_zam_do_json(self, username):
        order_data = {
            "uzytkownik": username,
            "produkty": [item.name for item in self.items],
            "suma": self.oblicz_total()
        }

# Sprawdzamy, czy istnieje plik, żeby dopisać kolejny, a nie nadpisać
        if os.path.exists('orders.json'):
            with open('orders.json', 'r') as f:
                try:
                    orders = json.load(f)
                except json.JSONDecodeError:
                    orders = []
        else:
            orders = []

        orders.append(order_data)

        with open('orders.json', 'w') as f:
            json.dump(orders, f, indent=4)

# baza produktów
produkty_db = [
    Product(1, "E-Book: Zerwij z cukrem", 20.00, "/static/images/ebook_okladka1.jpg" ),
    Product(2, "E-Book: 12 afirmacji", 0.00, "/static/images/ebook_okladka2.jpg"),
    Product(3, "Jadłospis 1200 kcal - Thermomix", 40.00, "/static/images/ebook_okladka3.png"),
    Product(4, "Konsultacja diagnostyczna", 260.00, "/static/images/konsultacja_diagnostyczna.jpg"),
    Product(5, "Konsultacja kolejna", 220.00, "/static/images/konsultacja_kolejna.jpg"),
]

# Dostępne sloty na wizyty

def get_available_slots(selected_date):
    date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    day_of_week = date_obj.weekday()  # 0=Poniedziałek, 6=Niedziela
    
    slots = []
    
    if day_of_week == 6:  # Niedziela - zamknięte
        return []
    elif day_of_week == 5:  # Sobota: 11-13
        hours = [11, 12]
    else:  # Dni robocze: 10-14, 16-19
        hours = [10, 11, 12, 13, 16, 17, 18]
    
    for hour in hours:
        time_str = f"{hour:02d}:00"
        # Sprawdzamy czy slot nie jest już zajęty
        existing = Visit.query.filter_by(date=selected_date, time=time_str).first()
        if not existing:
            slots.append(time_str)
    
    return slots


# Routy

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shop')
def shop():
    return render_template('shop.html', products=produkty_db)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('username')
        user_email = request.form.get('email')
        password = request.form.get('password')
        
        # Sprawdzamy, czy taki użytkownik już istnieje
        user_exists = User.query.filter_by(username=user_name).first()
        if user_exists:
            flash('Ta nazwa jest już zajęta!', 'danger')
        else:
            # Szyfrujemy hasło zanim trafi do bazy!
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=user_name, email=user_email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash('Konto utworzone! Możesz się teraz zalogować.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('username')
        password = request.form.get('password')
        
        # Szukamy użytkownika w bazie
        user = User.query.filter_by(username=user_name).first()
        
        # Sprawdzamy, czy istnieje i czy hasło się zgadza
        if user and check_password_hash(user.password, password):
            login_user(user)  # To "zapamiętuje" użytkownika w sesji
            flash(f'Witaj z powrotem, {user.username}!', 'success')
            return redirect(url_for('shop'))  # Przekierowanie do sklepu
        else:
            flash('Błędna nazwa użytkownika lub hasło.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required  # Tylko zalogowani mogą się wylogować
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>')
@login_required  # Tylko zalogowani mogą dodawać do koszyka
def add_to_cart(product_id):
    # Szukamy produktu po ID
    product = next((p for p in produkty_db if p.id == product_id), None)
    
    if product:
        # Pobieramy koszyk z sesji (albo tworzymy nowy)
        if 'cart' not in session:
            session['cart'] = []
        
        # Dodajemy produkt (zapisujemy jako słownik, bo sesja nie umie przechowywać obiektów)
        session['cart'].append({
            'id': product.id,
            'name': product.name,
            'price': product.price
        })
        session.modified = True  # Ważne! Mówi Flaskowi, że sesja się zmieniła
        
        flash(f'Dodano "{product.name}" do koszyka!', 'success')
    else:
        flash('Produkt nie istnieje.', 'danger')
    
    return redirect(url_for('shop'))

@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:index>')
@login_required
def remove_from_cart(index):
    cart_items = session.get('cart', [])
    
    if 0 <= index < len(cart_items):
        removed_item = cart_items.pop(index)
        session['cart'] = cart_items
        session.modified = True
        flash(f'Usunięto "{removed_item["name"]}" z koszyka.', 'info')
    
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Twój koszyk jest pusty!', 'warning')
        return redirect(url_for('shop'))

    # Używamy Twojej klasy Koszyk do logiki biznesowej
    moj_koszyk = Koszyk()
    for item in cart_items:
        p = Product(item['id'], item['name'], item['price'], "")
        moj_koszyk.dodaj_do_koszyka(p)

    # Zapisujemy do JSON
    moj_koszyk.zapisz_zam_do_json(current_user.username)

    # Czyścimy koszyk
    session.pop('cart', None)
    flash('Zamówienie przekazane do realizacji! Link do płatności i dostawy został wysłany na Twój adres email.', 'success')
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    # Pobieramy historię zamówień z pliku JSON
    orders = []
    if os.path.exists('orders.json'):
        with open('orders.json', 'r') as f:
            try:
                all_orders = json.load(f)
                orders = [o for o in all_orders if o.get('uzytkownik') == current_user.username]
            except json.JSONDecodeError:
                orders = []
    
    return render_template('account.html', orders=orders)

@app.route('/visit', methods=['GET', 'POST'])
def visit():
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_time = request.args.get('time', None)  # Nowy parametr
    available_slots = get_available_slots(selected_date)
    
    return render_template('visit.html', 
                         selected_date=selected_date, 
                         selected_time=selected_time,
                         available_slots=available_slots)

@app.route('/book_visit', methods=['POST'])
@login_required
def book_visit():
    date = request.form.get('date')
    time = request.form.get('time')
    
    existing = Visit.query.filter_by(date=date, time=time).first()
    if existing:
        flash('Ten termin jest już zajęty. Wybierz inny.', 'danger')
    else:
        new_visit = Visit(user_id=current_user.id, date=date, time=time)
        db.session.add(new_visit)
        db.session.commit()
        flash(f'Wizyta zarezerwowana na {date} o godzinie {time}! Link do płatności został wysłany na Twój adres email.', 'success')
    
    return redirect(url_for('account'))

# Blok uruchamiający - ZAWSZE NA SAMYM DOLE PLIKU
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

