from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from slugify import slugify


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://pistonews_wmwh_user:Rlv4RVZvvUZm0bPgI4VdF3f1wHgi2enG@dpg-d3c1lkb7mgec73a57gq0-a.frankfurt-postgres.render.com/pistonews_wmwh'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db = SQLAlchemy(app)

app.secret_key = "pistonews"

name="PistoNews"

class Articolo(db.Model):
    __tablename__ = 'articoli'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(255))
    image_data = db.Column(db.LargeBinary)  
    url = db.Column(db.String(255))

    def __repr__(self):
        return f"<Articolo {self.title}>"
    
class Classifica(db.Model):
    __tablename__ = 'classifica'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    punti = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    
class Utente(db.Model):
    __tablename__ = 'utenti'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String, nullable=False)

class Preferito(db.Model):
    __tablename__ = 'preferiti'
    id = db.Column(db.Integer, primary_key=True)
    utente_id = db.Column(db.Integer, db.ForeignKey('utenti.id'), nullable=False)
    articolo_id = db.Column(db.Integer, db.ForeignKey('articoli.id'), nullable=False)
    utente = db.relationship('Utente', backref='preferiti')
    articolo = db.relationship('Articolo', backref='preferito_da')

@app.route('/')
def index():
    print("Session content:", dict(session))
    articoli = Articolo.query.order_by(Articolo.date_posted.desc()).all()

    breaking = articoli[0] if len(articoli) > 0 else None
    recenti = articoli[1:5] if len(articoli) > 1 else []
    meno_recenti = articoli[5:8] if len(articoli) > 5 else []
    top5_piloti = Classifica.query.filter_by(tipo='pilota').order_by(Classifica.punti.desc()).limit(5).all()
    top5_team = Classifica.query.filter_by(tipo='team').order_by(Classifica.punti.desc()).limit(5).all()


    return render_template('index.html',breaking=breaking,recenti=recenti,meno_recenti=meno_recenti, top5_piloti=top5_piloti, top5_team=top5_team, name=name)

@app.route('/googlefd460ab229d35c1d.html')
def google_verification():
    return send_from_directory('.', 'googlefd460ab229d35c1d.html')

@app.route("/debug-columns")
def debug_columns():
    return {"columns": list(Articolo.__table__.columns.keys())}

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        utente = Utente.query.filter_by(username=username).first()      

        if utente and utente.password == password:
            session['username'] = utente.username
            session['role'] = utente.role
            flash('Accesso effettuato con successo!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenziali errate.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Logout effettuato.', 'info')
    return redirect(url_for('index'))


@app.route("/articoli/add", methods=["GET", "POST"])
def aggiungi_articolo():
    if not session.get('role') == 'admin':
        flash("Devi essere admin per creare un articolo.", "warning")
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        image = request.files.get('image')
        url = slugify(title)

        # Inizializza sempre le variabili
        image_filename = None
        image_data = None

        if image and image.filename != '':
            image_filename = secure_filename(image.filename)  # aggiorno image_filename
            image_data = image.read()  # salvo i dati binari

        nuovo_articolo = Articolo(
            title=title,
            content=content,
            author=author,
            image_filename=image_filename,
            image_data=image_data,
            url=url
        )

        db.session.add(nuovo_articolo)
        db.session.commit()
        flash("Articolo aggiunto con successo!", "success")
        return redirect(url_for("index"))

    return render_template('articoli/add.html')

@app.route('/articolo/<string:articolo_url>')
def dettaglio_articolo(articolo_url):
    articolo = Articolo.query.filter_by(url=articolo_url).first_or_404()
    preferiti_ids = []
    if 'username' in session:
        utente = Utente.query.filter_by(username=session['username']).first()
        if utente:
            preferiti_ids = [p.articolo_id for p in utente.preferiti]
    return render_template('articoli/dettaglio.html', articolo=articolo, name=name, preferiti_ids=preferiti_ids)


@app.route('/articolo/edit/<string:articolo_url>', methods=['GET', 'POST'])
def modifica_articolo(articolo_url):
    if not session.get('role') == 'admin':
        return redirect(url_for('login'))

    articolo = Articolo.query.filter_by(url=articolo_url).first_or_404()

    if request.method == 'POST':
        articolo.title = request.form['title']
        articolo.content = request.form['content']
        articolo.author = request.form['author']
        articolo.url = request.form['url']

        image = request.files.get('image')
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            articolo.image_filename = filename
            articolo.image_data = image.read()

            
        if 'remove_image' in request.form:
            if articolo.image_filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], articolo.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            articolo.image_filename = None

        db.session.commit()
        flash("Articolo modificato con successo!", "success")
        return redirect(url_for('dettaglio_articolo', articolo_url=articolo.url))

    return render_template('articoli/edit.html', articolo=articolo)


@app.route('/articolo/delete/<string:articolo_url>', methods=['POST'])
def elimina_articolo(articolo_url):
    articolo = Articolo.query.filter_by(url=articolo_url).first_or_404()

    db.session.delete(articolo)
    db.session.commit()
    flash("Articolo eliminato con successo!", "success")
    return redirect(url_for('index'))

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/classifiche', methods=['GET', 'POST'])
def classifiche():
    piloti = Classifica.query.filter_by(tipo='pilota').order_by(Classifica.punti.desc()).all()
    team = Classifica.query.filter_by(tipo='team').order_by(Classifica.punti.desc()).all()
    

    admin = session.get('role') == 'admin'

    if request.method == 'POST' and admin:
        for item_id, punti in request.form.items():
            classifica_item = Classifica.query.get(int(item_id))
            if classifica_item:
                try:
                    classifica_item.punti = int(punti)
                except ValueError:
                    pass
        db.session.commit()
        return redirect(url_for('classifiche'))

    return render_template('classifiche.html', piloti=piloti, team=team, admin=admin, name=name)


@app.route('/articoli')
def lista_articoli():
    
    query = request.args.get('query')
    if query:
        listarticoli = Articolo.query.filter(
            or_(
                Articolo.title.ilike(f'%{query}%'),
                Articolo.content.ilike(f'%{query}%')
            )
        ).order_by(Articolo.date_posted.desc()).all()
    else:
        listarticoli = Articolo.query.order_by(Articolo.date_posted.desc()).all()
    
    return render_template('/articoli/list.html', listarticoli=listarticoli, query=query, name=name)


@app.route('/registrati', methods=['GET', 'POST'])
def registrati():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conferma = request.form['conferma_password']
        role = 'user'

        if password != conferma:
            flash("Le password non coincidono.", "danger")
            return redirect(url_for('registrati'))

        if Utente.query.filter_by(username=username).first():
            flash("Username già in uso.", "warning")
            return redirect(url_for('registrati'))

        nuovo_utente = Utente(username=username, password=password, role=role)
        db.session.add(nuovo_utente)
        db.session.commit()
        flash("Registrazione avvenuta con successo! Ora puoi accedere.", "success")
        return redirect(url_for('login'))

    return render_template('registrazione.html')

@app.route('/admin/utenti', methods=['GET', 'POST'])
def gestisci_utenti():
    if not session.get('role') == 'admin':
        flash("Accesso negato.", "danger")
        return redirect(url_for('login'))

    utenti = Utente.query.all()

    if request.method == 'POST':
        for utente in utenti:
            nuovo_valore = request.form.get(f'role_{utente.id}')
            if nuovo_valore:
                utente.role = nuovo_valore
        db.session.commit()
        flash("Ruoli aggiornati correttamente.", "success")
        return redirect(url_for('gestisci_utenti'))

    return render_template('gestioneutenti.html', utenti=utenti)



@app.route('/preferiti/add/<int:articolo_id>', methods=['POST'])
def aggiungi_preferito(articolo_id):
    if session.get('role') not in ['admin', 'user']:
        flash("Effettua il login per salvare preferiti.", "warning")
        return redirect(url_for('login'))

    utente = Utente.query.filter_by(username=session['username']).first()
    esiste = Preferito.query.filter_by(utente_id=utente.id, articolo_id=articolo_id).first()

    if not esiste:
        preferito = Preferito(utente_id=utente.id, articolo_id=articolo_id)
        db.session.add(preferito)
        db.session.commit()
        flash("Articolo aggiunto ai preferiti.", "success")

    return redirect(request.referrer or url_for('index'))


@app.route('/preferiti/remove/<int:articolo_id>', methods=['POST'])
def rimuovi_preferito(articolo_id):
    if session.get('role') not in ['admin', 'user']:
        flash("Effettua il login per gestire i preferiti.", "warning")
        return redirect(url_for('login'))

    utente = Utente.query.filter_by(username=session['username']).first()
    preferito = Preferito.query.filter_by(utente_id=utente.id, articolo_id=articolo_id).first()

    if preferito:
        db.session.delete(preferito)
        db.session.commit()
        flash("Articolo rimosso dai preferiti.", "info")

    return redirect(request.referrer or url_for('index'))



@app.route('/articoli/preferiti')
def lista_preferiti():
    if session.get('role') not in ['admin', 'user']:
        flash("Accedi per vedere i tuoi articoli preferiti.", "warning")
        return redirect(url_for('login'))

    utente = Utente.query.filter_by(username=session['username']).first()
    preferiti = Articolo.query.join(Preferito).filter(Preferito.utente_id == utente.id).all()

    return render_template('/articoli/list.html', articoli=preferiti, name=name)

@app.route('/offline.html')
def offline():
    return render_template('/templates/offline.html')


@app.route('/immagine/<int:articolo_id>')
def get_image(articolo_id):
    articolo = Articolo.query.get_or_404(articolo_id)
    if not articolo.image_data:
        return "Nessuna immagine", 404
    # Puoi impostare il mimetype in base all'estensione salvata in image_filename
    return Response(articolo.image_data, mimetype="image/jpg")


app.run(host="0.0.0.0", port=5432, debug=True)
