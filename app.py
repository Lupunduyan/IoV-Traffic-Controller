from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2 import OperationalError, ProgrammingError
import os
import logging
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration de la base de données PostgreSQL
DB_HOST = 'dpg-cvfh71rqf0us73fqu880-a'
DB_PORT = '5432'
DB_NAME = 'iov_traffic_controller_db'
DB_USER = 'iov_traffic_controller_db_user'
DB_PASSWORD = 'opwr5i40CToMjB8Q58j9aQXt3vkv6c1p'
DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING', "postgresql://iov_traffic_controller_db_user:opwr5i40CToMjB8Q58j9aQXt3vkv6c1p@dpg-cvfh71rqf0us73fqu880-a/iov_traffic_controller_db")

# Configuration Flask-Login
app.config['SECRET_KEY'] = 'password'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

# Fonction pour établir une connexion à la base de données
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        logging.debug("Connexion à la base de données établie avec succès.")
        return conn
    except OperationalError as e:
        logging.error(f"Erreur opérationnelle lors de la connexion à la base de données : {e}")
        return jsonify({"error": f"Erreur opérationnelle : {str(e)}"}), 500
    except ProgrammingError as e:
        logging.error(f"Erreur de programmation lors de la connexion à la base de données : {e}")
        return jsonify({"error": f"Erreur de programmation : {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la connexion à la base de données : {e}")
        return jsonify({"error": f"Erreur inattendue : {str(e)}"}), 500

# Créer les tables si elles n'existent pas
def create_tables():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Table installation_count
        cur.execute('''
        CREATE TABLE IF NOT EXISTS installation_count (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            installation_date TIMESTAMP NOT NULL,
            app_version VARCHAR(50),
            platform VARCHAR(50)
        );
        ''')

        # Table operation_count
        cur.execute('''
        CREATE TABLE IF NOT EXISTS operation_count (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            operation_called VARCHAR(100) NOT NULL,
            operation_params JSONB,
            paid BOOLEAN DEFAULT FALSE,
            operation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table hx711_data
        cur.execute('''
        CREATE TABLE IF NOT EXISTS hx711_data (
            id SERIAL PRIMARY KEY,
            capteur VARCHAR(100) NOT NULL,
            status VARCHAR(100) NOT NULL,
            poids FLOAT NOT NULL,
            limit_ FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table fc51_data
        cur.execute('''
        CREATE TABLE IF NOT EXISTS fc51_data (
            id SERIAL PRIMARY KEY,
            capteur VARCHAR(100) NOT NULL,
            status VARCHAR(100) NOT NULL,
            obstacle_gauche VARCHAR(10) NOT NULL,
            obstacle_droite VARCHAR(10) NOT NULL,
            obstacle_devant VARCHAR(10) NOT NULL,
            obstacle_deriere VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table lm35_data
        cur.execute('''
        CREATE TABLE IF NOT EXISTS lm35_data (
            id SERIAL PRIMARY KEY,
            capteur VARCHAR(100) NOT NULL,
            status VARCHAR(100) NOT NULL,
            temperature FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Table tcs230_data
        cur.execute('''
        CREATE TABLE IF NOT EXISTS tcs230_data (
            id SERIAL PRIMARY KEY,
            capteur VARCHAR(100) NOT NULL,
            status VARCHAR(100) NOT NULL,
            red INTEGER NOT NULL,
            green INTEGER NOT NULL,
            blue INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        conn.commit()
        cur.close()
        conn.close()
        logging.debug("Tables créées ou déjà existantes.")
    except Exception as e:
        logging.error(f"Erreur lors de la création des tables : {e}")
        raise

# Modèle pour la table User
class User(UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150))
    post_nom = db.Column(db.String(150))
    prenom = db.Column(db.String(150))
    password = db.Column(db.String(10050))
    vehicule = db.Column(db.String(150))
    role = db.Column(db.String(50))  # Peut être 'admin', 'chauffeur', 'gestionnaire'

# Modèle pour la table Vehicule
class Vehicule:
    id = db.Column(db.Integer, primary_key=True)
    marque = db.Column(db.String(100))
    plaque = db.Column(db.String(100))
    capteur_fc51 = db.Column(db.String(100))
    capteur_tcs230 = db.Column(db.String(100))
    capteur_hx711 = db.Column(db.String(100))
    capteur_lm35 = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Créer les tables si elles n'existent pas déjà
with app.app_context():
    create_tables()

#============================ INDEX ==================================
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

#===========================================================================================

# Route pour recevoir les données du capteur HX711
@app.route('/send_hx711_data', methods=['GET'])
def receive_hx711_data():
    capteur = request.args.get('capteur')
    status = request.args.get('status')
    poids = request.args.get('poids')
    limit_ = request.args.get('limit_')
    
    if not status or not poids or not capteur:
        return jsonify({'error': 'Missing data'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO hx711_data (capteur, status, poids, limit_) VALUES (%s, %s, %s, %s)", (capteur, status, poids, limit_))
        conn.commit()
        cur.close()
        return jsonify({'message': 'Data inserted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour obtenir les dernières données de poids
@app.route('/get_last_hx711_data', methods=['GET'])
def get_last_hx711_data():
    capteur = request.args.get('capteur')

    if not capteur:
        return jsonify({'error': 'Missing data Capteur'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM hx711_data WHERE capteur = %s ORDER BY id DESC LIMIT 1", (capteur,))
        data = cur.fetchone()
        cur.close()
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour recevoir les données du capteur FC51
@app.route('/send_fc51_data', methods=['GET'])
def receive_fc51_data():
    capteur = request.args.get('capteur')
    status = request.args.get('status')
    obstacle_gauche = request.args.get('obstacle_gauche', default="0", type=int)
    obstacle_droite = request.args.get('obstacle_droite', default="0", type=int)
    obstacle_devant = request.args.get('obstacle_devant', default="0", type=int)
    obstacle_deriere = request.args.get('obstacle_deriere', default="0", type=int)

    if not capteur:
        return jsonify({'error': 'Missing data Capteur'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO fc51_data (capteur, status, obstacle_gauche, obstacle_droite, obstacle_devant, obstacle_deriere) VALUES (%s, %s, %s, %s, %s, %s)", (capteur, status, obstacle_gauche, obstacle_droite, obstacle_devant, obstacle_deriere))
        conn.commit()
        cur.close()
        return jsonify({'message': 'Data inserted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour récupérer les dernières données d'un capteur FC51
@app.route('/get_last_fc51_data', methods=['GET'])
def get_last_fc51_data():
    capteur = request.args.get('capteur')

    if not capteur:
        return jsonify({'error': 'Missing data Capteur'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM fc51_data WHERE capteur = %s ORDER BY id DESC LIMIT 1', (capteur,))
        data = cur.fetchone()
        cur.close()
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour recevoir les données du capteur LM35
@app.route('/send_lm35_data', methods=['GET'])
def receive_lm35_data():
    capteur = request.args.get('capteur')
    status = request.args.get('status')
    temperature = request.args.get('temperature')
    
    if not status or not temperature or not capteur:
        return jsonify({'error': 'Missing data'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO lm35_data (capteur, status, temperature) VALUES (%s, %s, %s)", (capteur, status, temperature))
        conn.commit()
        cur.close()
        return jsonify({'message': 'Temperature data inserted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour obtenir les dernières données de température
@app.route('/get_last_lm35_data', methods=['GET'])
def get_last_lm35_data():
    capteur = request.args.get('capteur')

    if not capteur:
        return jsonify({'error': 'Missing data Capteur'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM lm35_data WHERE capteur = %s ORDER BY id DESC LIMIT 1", (capteur,))
        data = cur.fetchone()
        cur.close()
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour recevoir les données du capteur TCS230
@app.route('/send_tcs230_data', methods=['GET'])
def receive_tcs230_data():
    capteur = request.args.get('capteur')
    status = request.args.get('status')
    red = request.args.get('red')
    green = request.args.get('green')
    blue = request.args.get('blue')
    
    if not status or not red or not green or not blue or not capteur:
        return jsonify({'error': 'Missing data'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO tcs230_data (capteur, status, red, green, blue) VALUES (%s, %s, %s, %s, %s)", (capteur, status, red, green, blue))
        conn.commit()
        cur.close()
        return jsonify({'message': 'Data inserted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour obtenir les dernières données du capteur TCS230
@app.route('/get_last_tcs230_data', methods=['GET'])
def get_last_tcs230_data():
    capteur = request.args.get('capteur')

    if not capteur:
        return jsonify({'error': 'Missing data Capteur'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tcs230_data WHERE capteur = %s ORDER BY id DESC LIMIT 1", (capteur,))
        data = cur.fetchone()
        cur.close()
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Simulation d'une alerte en cas d'obstacle
def generate_alert(message):
    print(f"ALERTE: {message}")

#============================================================== MODELS =========================================================

# ===================================================== GESTION UTILISATEURs ===================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nom = request.form.get('nom')
        password = request.form.get('password')
        user = User.query.filter_by(nom=nom).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login ou mot de passe incorrect.')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nom = request.form.get('nom')
        post_nom = request.form.get('post_nom')
        prenom = request.form.get('prenom')
        password = request.form.get('password')
        vehicule = request.form.get('vehicule')
        role = request.form.get('role')
        hashed_password = generate_password_hash(password)
        new_user = User(nom=nom, post_nom=post_nom, prenom=prenom, password=hashed_password, vehicule=vehicule, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Calcul des totaux pour chaque type de capteur
    total_fc51 = Vehicule.query.filter(Vehicule.capteur_fc51 != None, Vehicule.capteur_fc51 != '').count()
    total_manquant_fc51 = Vehicule.query.filter(Vehicule.capteur_fc51 == '').count()

    total_hx711 = Vehicule.query.filter(Vehicule.capteur_hx711 != None, Vehicule.capteur_hx711 != '').count()
    total_manquant_hx711 = Vehicule.query.filter(Vehicule.capteur_hx711 == '').count()

    total_lm35 = Vehicule.query.filter(Vehicule.capteur_lm35 != None, Vehicule.capteur_lm35 != '').count()
    total_manquant_lm35 = Vehicule.query.filter(Vehicule.capteur_lm35 == '').count()

    total_tcs230 = Vehicule.query.filter(Vehicule.capteur_tcs230 != None, Vehicule.capteur_tcs230 != '').count()
    total_manquant_tcs230 = Vehicule.query.filter(Vehicule.capteur_tcs230 == '').count()

    # Total de capteurs (tous types confondus)
    total_capteurs = total_fc51 + total_hx711 + total_lm35 + total_tcs230

    # Total de capteurs manquants
    total_manquant_capteurs = total_manquant_fc51 + total_manquant_hx711 + total_manquant_lm35 + total_manquant_tcs230

    # Total de véhicules
    total_vehicules = Vehicule.query.count()

    # Récupérer le dernier capteur ajouté
    dernier_fc51 = Fc51_data.query.order_by(Fc51_data.id.desc()).first()
    
    if dernier_fc51:
        vehicule = Vehicule.query.filter_by(capteur_fc51=dernier_fc51.capteur).first()
    else:
        vehicule = None
    
    if vehicule:
        # Récupérer les dernières données de chaque capteur pour ce véhicule
        capteurs_data = {
            'fc51': Fc51_data.query.filter_by(capteur=vehicule.capteur_fc51).order_by(Fc51_data.id.desc()).first(),
            'hx711': Hx711_data.query.filter_by(capteur=vehicule.capteur_hx711).order_by(Hx711_data.id.desc()).first(),
            'lm35': Lm35_data.query.filter_by(capteur=vehicule.capteur_lm35).order_by(Lm35_data.id.desc()).first(),
            'tcs230': Tcs230_data.query.filter_by(capteur=vehicule.capteur_tcs230).order_by(Tcs230_data.id.desc()).first()
        }
    else:
        # Si aucun véhicule ou capteur trouvé, on renvoie des données vides
        vehicule = {
            'marque': "Pas de marque",
            'plaque': "Pas de plaque"
        }
        capteurs_data = {
            'fc51': "",
            'hx711': "",
            'lm35': "",
            'tcs230': ""
        }

    # Retourne les données au template
    return render_template('dashboard.html', 
                           total_fc51=total_fc51, 
                           total_manquant_fc51=total_manquant_fc51, 
                           total_hx711=total_hx711, 
                           total_manquant_hx711=total_manquant_hx711, 
                           total_lm35=total_lm35, 
                           total_manquant_lm35=total_manquant_lm35, 
                           total_tcs230=total_tcs230, 
                           total_manquant_tcs230=total_manquant_tcs230, 
                           total_capteurs=total_capteurs, 
                           total_manquant_capteurs=total_manquant_capteurs, 
                           total_vehicules=total_vehicules,
                           vehicule=vehicule, 
                           capteurs_data=capteurs_data)

@app.route('/ajout_user', methods=['POST'])
def ajout_user():
    # Récupération des données du formulaire
    nom = request.form.get('nom')
    post_nom = request.form.get('post_nom')
    prenom = request.form.get('prenom')
    vehicule = request.form.get('vehicule')
    role = request.form.get('role')
    password = request.form.get('password')

    # Validation des champs requis
    if not nom or not post_nom or not prenom or not password:
        flash('Tous les champs obligatoires doivent être remplis', 'error')
        return redirect(url_for('list_user'))

    # Hachage du mot de passe
    hashed_password = generate_password_hash(password)

    # Création d'un nouvel utilisateur
    nouvel_utilisateur = User(
        nom=nom,
        post_nom=post_nom,
        prenom=prenom,
        vehicule=vehicule if vehicule else None,  # Vérification si un véhicule est fourni
        role=role,
        password=hashed_password
    )

    # Ajout à la base de données
    try:
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        flash(f"L'utilisateur {prenom} {nom} a été ajouté avec succès !", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur s'est produite : {str(e)}", 'error')

    # Redirection vers la liste des utilisateurs
    return redirect(url_for('list_user'))

@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    # Rechercher l'utilisateur par son ID
    user_to_delete = User.query.get_or_404(id)

    try:
        # Supprimer l'utilisateur de la base de données
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"L'utilisateur {user_to_delete.prenom} {user_to_delete.nom} a été supprimé avec succès !", 'success')
    except Exception as e:
        db.session.rollback()  # En cas d'erreur, annuler la transaction
        flash(f"Une erreur s'est produite : {str(e)}", 'error')

    # Redirection vers la liste des utilisateurs après suppression
    return redirect(url_for('list_user'))

@app.route('/list_users')
@login_required
def list_user():
    # Récupérer tous les utilisateurs
    users = User.query.all()

    # Renvoyer les informations à la page HTML
    return render_template('list_user.html', users=users)

@app.route('/creer_user')
@login_required
def creer_user():
    return render_template('creer_user.html')

# Route pour afficher la liste des véhicules
@app.route('/list_vehicule')
@login_required
def list_vehicule():
    # Récupérer tous les véhicules depuis la base de données
    vehicules = Vehicule.query.all()
    return render_template('list_vehicule.html', vehicules=vehicules)

@app.route('/vehicule/<int:id>')
@login_required
def vehicule(id):
    # Récupérer les détails du véhicule avec l'ID fourni
    vehicule = Vehicule.query.get_or_404(id)
    
    # Initialiser les informations des capteurs
    capteurs_info = {
        'fc51': {'status': 'Non configuré', 'badge': 'danger', 'data': None},
        'hx711': {'status': 'Non configuré', 'badge': 'danger', 'data': None},
        'lm35': {'status': 'Non configuré', 'badge': 'danger', 'data': None},
        'tcs230': {'status': 'Non configuré', 'badge': 'danger', 'data': None}
    }

    # Vérifier et récupérer les données de chaque capteur
    if vehicule.capteur_fc51:
        fc51_data = Fc51_data.query.filter_by(capteur=vehicule.capteur_fc51).all()
        capteurs_info['fc51'] = {'status': 'Déjà configuré', 'badge': 'success', 'data': fc51_data}

    if vehicule.capteur_hx711:
        hx711_data = Hx711_data.query.filter_by(capteur=vehicule.capteur_hx711).all()
        capteurs_info['hx711'] = {'status': 'Déjà configuré', 'badge': 'success', 'data': hx711_data}

    if vehicule.capteur_lm35:
        lm35_data = Lm35_data.query.filter_by(capteur=vehicule.capteur_lm35).all()
        capteurs_info['lm35'] = {'status': 'Déjà configuré', 'badge': 'success', 'data': lm35_data}

    if vehicule.capteur_tcs230:
        tcs230_data = Tcs230_data.query.filter_by(capteur=vehicule.capteur_tcs230).all()
        capteurs_info['tcs230'] = {'status': 'Déjà configuré', 'badge': 'success', 'data': tcs230_data}

    # Renvoyer les informations à la page "vehicule.html"
    return render_template('vehicule.html', vehicule=vehicule, capteurs_info=capteurs_info)

# Route pour ajouter un véhicule
@app.route('/ajout_vehicule', methods=['GET', 'POST'])
def ajout_vehicule():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        marque = request.form.get('marque')
        plaque = request.form.get('plaque')
        capteur_fc51 = request.form.get('capteur_fc51')
        capteur_tcs230 = request.form.get('capteur_tcs230')
        capteur_hx711 = request.form.get('capteur_hx711')
        capteur_lm35 = request.form.get('capteur_lm35')

        # Créer une nouvelle instance de Vehicule
        nouveau_vehicule = Vehicule(
            marque=marque,
            plaque=plaque,
            capteur_fc51=capteur_fc51,
            capteur_tcs230=capteur_tcs230,
            capteur_hx711=capteur_hx711,
            capteur_lm35=capteur_lm35
        )

        # Ajouter à la base de données
        try:
            db.session.add(nouveau_vehicule)
            db.session.commit()
            flash('Véhicule ajouté avec succès !')
            return redirect(url_for('ajout_vehicule'))
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du véhicule : {e}')
            return redirect(url_for('ajout_vehicule'))

    return redirect(url_for('list_vehicule'))

@app.route('/delete_vehicule/<int:id>', methods=['GET'])
@login_required
def delete_vehicule(id):
    # Récupérer le véhicule avec l'ID donné
    vehicule = Vehicule.query.get_or_404(id)
    
    try:
        # Supprimer le véhicule de la base de données
        db.session.delete(vehicule)
        db.session.commit()
        flash(f'Vehicule {vehicule.marque} avec la plaque {vehicule.plaque} a été supprimé avec succès.', 'success')
    except:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du véhicule.', 'danger')
    
    # Rediriger vers la liste des véhicules après suppression
    return redirect(url_for('list_vehicule'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#===============================================================================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
