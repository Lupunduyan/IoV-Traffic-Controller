from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2 import OperationalError, ProgrammingError
import os
import logging
from datetime import datetime
from flask_cors import CORS  # Import CORS

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

        # Table users
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(150) NOT NULL,
            post_nom VARCHAR(150) NOT NULL,
            prenom VARCHAR(150) NOT NULL,
            password VARCHAR(10050) NOT NULL,
            vehicule VARCHAR(150),
            role VARCHAR(50) NOT NULL
        );
        ''')

        # Table vehicules
        cur.execute('''
        CREATE TABLE IF NOT EXISTS vehicules (
            id SERIAL PRIMARY KEY,
            marque VARCHAR(100) NOT NULL,
            plaque VARCHAR(100) NOT NULL,
            capteur_fc51 VARCHAR(100),
            capteur_tcs230 VARCHAR(100),
            capteur_hx711 VARCHAR(100),
            capteur_lm35 VARCHAR(100)
        );
        ''')

        conn.commit()
        cur.close()
        conn.close()
        logging.debug("Tables créées ou déjà existantes.")
    except Exception as e:
        logging.error(f"Erreur lors de la création des tables : {e}")
        raise

@app.route('/create_user_mike', methods=['POST', 'GET'])
def create_user_mike():
    if request.method == 'POST':
        # Données de l'utilisateur Mike
        nom = "Mike"
        post_nom = "Doe"  # Vous pouvez ajuster ces valeurs selon vos besoins
        prenom = "John"
        password = "1234567890"
        vehicule = "Aucun"  # Vous pouvez ajuster ces valeurs selon vos besoins
        role = "utilisateur"  # Vous pouvez ajuster ces valeurs selon vos besoins

        # Hachage du mot de passe
        hashed_password = generate_password_hash(password)

        try:
            # Connexion à la base de données
            conn = get_db_connection()
            cur = conn.cursor()

            # Vérifier si l'utilisateur Mike existe déjà
            cur.execute("SELECT * FROM users WHERE nom = %s;", (nom,))
            existing_user = cur.fetchone()

            if existing_user:
                return jsonify({"message": "L'utilisateur Mike existe déjà."}), 409  # 409 = Conflict

            # Insérer l'utilisateur Mike dans la base de données
            cur.execute(
                "INSERT INTO users (nom, post_nom, prenom, password, vehicule, role) VALUES (%s, %s, %s, %s, %s, %s)",
                (nom, post_nom, prenom, hashed_password, vehicule, role)
            )
            conn.commit()

            # Fermer la connexion
            cur.close()
            conn.close()

            return jsonify({"message": "Utilisateur Mike créé avec succès."}), 201  # 201 = Created

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'GET':
        # Vérifier si l'utilisateur Mike existe déjà
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE nom = 'Mike';")
            existing_user = cur.fetchone()
            cur.close()
            conn.close()

            if existing_user:
                return jsonify({"message": "L'utilisateur Mike existe déjà.", "user": existing_user}), 200
            else:
                return jsonify({"message": "L'utilisateur Mike n'existe pas."}), 404  # 404 = Not Found

        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Modèle pour la table User (utilisé par Flask-Login)
class User(UserMixin):
    def __init__(self, id, nom, post_nom, prenom, password, vehicule, role):
        self.id = id
        self.nom = nom
        self.post_nom = post_nom
        self.prenom = prenom
        self.password = password
        self.vehicule = vehicule
        self.role = role

# Charger un utilisateur pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6])
    return None

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
        conn.close()
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
        conn.close()
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
        conn.close()
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
        conn.close()
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
        conn.close()
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
        conn.close()
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
        conn.close()
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
        conn.close()
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
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE nom = %s;", (nom,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()
        if user_data and check_password_hash(user_data[4], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6])
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
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (nom, post_nom, prenom, password, vehicule, role) VALUES (%s, %s, %s, %s, %s, %s)", (nom, post_nom, prenom, hashed_password, vehicule, role))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Calcul des totaux pour chaque type de capteur
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_fc51 IS NOT NULL AND capteur_fc51 != '';")
    total_fc51 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_fc51 IS NULL OR capteur_fc51 = '';")
    total_manquant_fc51 = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_hx711 IS NOT NULL AND capteur_hx711 != '';")
    total_hx711 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_hx711 IS NULL OR capteur_hx711 = '';")
    total_manquant_hx711 = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_lm35 IS NOT NULL AND capteur_lm35 != '';")
    total_lm35 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_lm35 IS NULL OR capteur_lm35 = '';")
    total_manquant_lm35 = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_tcs230 IS NOT NULL AND capteur_tcs230 != '';")
    total_tcs230 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vehicules WHERE capteur_tcs230 IS NULL OR capteur_tcs230 = '';")
    total_manquant_tcs230 = cur.fetchone()[0]

    # Total de capteurs (tous types confondus)
    total_capteurs = total_fc51 + total_hx711 + total_lm35 + total_tcs230

    # Total de capteurs manquants
    total_manquant_capteurs = total_manquant_fc51 + total_manquant_hx711 + total_manquant_lm35 + total_manquant_tcs230

    # Total de véhicules
    cur.execute("SELECT COUNT(*) FROM vehicules;")
    total_vehicules = cur.fetchone()[0]

    # Récupérer le dernier capteur ajouté
    cur.execute("SELECT * FROM fc51_data ORDER BY id DESC LIMIT 1;")
    dernier_fc51 = cur.fetchone()
    
    if dernier_fc51:
        cur.execute("SELECT * FROM vehicules WHERE capteur_fc51 = %s;", (dernier_fc51[1],))
        vehicule = cur.fetchone()
    else:
        vehicule = None
    
    if vehicule:
        # Récupérer les dernières données de chaque capteur pour ce véhicule
        capteurs_data = {
            'fc51': dernier_fc51,
            'hx711': None,
            'lm35': None,
            'tcs230': None
        }
        if vehicule[4]:  # capteur_hx711
            cur.execute("SELECT * FROM hx711_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[4],))
            capteurs_data['hx711'] = cur.fetchone()
        if vehicule[5]:  # capteur_lm35
            cur.execute("SELECT * FROM lm35_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[5],))
            capteurs_data['lm35'] = cur.fetchone()
        if vehicule[6]:  # capteur_tcs230
            cur.execute("SELECT * FROM tcs230_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[6],))
            capteurs_data['tcs230'] = cur.fetchone()
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

    cur.close()
    conn.close()

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

    # Ajout à la base de données
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (nom, post_nom, prenom, password, vehicule, role) VALUES (%s, %s, %s, %s, %s, %s)", (nom, post_nom, prenom, hashed_password, vehicule, role))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"L'utilisateur {prenom} {nom} a été ajouté avec succès !", 'success')
    except Exception as e:
        flash(f"Une erreur s'est produite : {str(e)}", 'error')

    # Redirection vers la liste des utilisateurs
    return redirect(url_for('list_user'))

@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    # Rechercher l'utilisateur par son ID
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s;", (id,))
        user_to_delete = cur.fetchone()
        if user_to_delete:
            cur.execute("DELETE FROM users WHERE id = %s;", (id,))
            conn.commit()
            flash(f"L'utilisateur {user_to_delete[3]} {user_to_delete[1]} a été supprimé avec succès !", 'success')
        else:
            flash("Utilisateur non trouvé.", 'error')
    except Exception as e:
        flash(f"Une erreur s'est produite : {str(e)}", 'error')
    finally:
        cur.close()
        conn.close()

    # Redirection vers la liste des utilisateurs après suppression
    return redirect(url_for('list_user'))

@app.route('/list_users')
@login_required
def list_user():
    # Récupérer tous les utilisateurs
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users;")
    users = cur.fetchall()
    cur.close()
    conn.close()

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicules;")
    vehicules = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('list_vehicule.html', vehicules=vehicules)

@app.route('/vehicule/<int:id>')
@login_required
def vehicule(id):
    # Récupérer les détails du véhicule avec l'ID fourni
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicules WHERE id = %s;", (id,))
    vehicule = cur.fetchone()

    # Initialiser les informations des capteurs
    capteurs_info = {
        'fc51': {'status': 'Non configuré', 'badge': 'danger', 'data': None},
        'hx711': {'status': 'Non configuré', 'badge': 'danger', 'data': None},
        'lm35': {'status': 'Non configuré', 'badge': 'danger', 'data': None},
        'tcs230': {'status': 'Non configuré', 'badge': 'danger', 'data': None}
    }

    # Vérifier et récupérer les données de chaque capteur
    if vehicule and vehicule[3]:  # capteur_fc51
        cur.execute("SELECT * FROM fc51_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[3],))
        capteurs_info['fc51']['data'] = cur.fetchone()
        capteurs_info['fc51']['status'] = 'Déjà configuré'
        capteurs_info['fc51']['badge'] = 'success'

    if vehicule and vehicule[4]:  # capteur_hx711
        cur.execute("SELECT * FROM hx711_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[4],))
        capteurs_info['hx711']['data'] = cur.fetchone()
        capteurs_info['hx711']['status'] = 'Déjà configuré'
        capteurs_info['hx711']['badge'] = 'success'

    if vehicule and vehicule[5]:  # capteur_lm35
        cur.execute("SELECT * FROM lm35_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[5],))
        capteurs_info['lm35']['data'] = cur.fetchone()
        capteurs_info['lm35']['status'] = 'Déjà configuré'
        capteurs_info['lm35']['badge'] = 'success'

    if vehicule and vehicule[6]:  # capteur_tcs230
        cur.execute("SELECT * FROM tcs230_data WHERE capteur = %s ORDER BY id DESC LIMIT 1;", (vehicule[6],))
        capteurs_info['tcs230']['data'] = cur.fetchone()
        capteurs_info['tcs230']['status'] = 'Déjà configuré'
        capteurs_info['tcs230']['badge'] = 'success'

    cur.close()
    conn.close()

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

        # Ajouter à la base de données
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO vehicules (marque, plaque, capteur_fc51, capteur_tcs230, capteur_hx711, capteur_lm35) VALUES (%s, %s, %s, %s, %s, %s)", (marque, plaque, capteur_fc51, capteur_tcs230, capteur_hx711, capteur_lm35))
            conn.commit()
            cur.close()
            conn.close()
            flash('Véhicule ajouté avec succès !')
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du véhicule : {e}')

    return redirect(url_for('list_vehicule'))

@app.route('/delete_vehicule/<int:id>', methods=['GET'])
@login_required
def delete_vehicule(id):
    # Récupérer le véhicule avec l'ID donné
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM vehicules WHERE id = %s;", (id,))
        vehicule = cur.fetchone()
        if vehicule:
            cur.execute("DELETE FROM vehicules WHERE id = %s;", (id,))
            conn.commit()
            flash(f'Vehicule {vehicule[1]} avec la plaque {vehicule[2]} a été supprimé avec succès.', 'success')
        else:
            flash('Véhicule non trouvé.', 'error')
    except Exception as e:
        flash(f'Erreur lors de la suppression du véhicule : {e}', 'danger')
    finally:
        cur.close()
        conn.close()

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
