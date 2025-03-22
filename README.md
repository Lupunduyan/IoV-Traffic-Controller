# IoV-Traffic-Controller

# Documentation de l'API pour la gestion des capteurs

Cette documentation explique comment interagir avec l'API pour configurer et récupérer les données des capteurs. L'API est construite avec Flask et utilise une base de données MySQL pour stocker les données des capteurs.

## Configuration de l'API

### Prérequis

- Python 3.x
- Flask
- Flask-MySQLdb
- Flask-CORS
- MySQL

### Installation

1. Clonez le dépôt contenant le code de l'API.
2. Installez les dépendances nécessaires :

   ```bash
   pip install Flask Flask-MySQLdb Flask-CORS
   ```

3. Configurez la base de données MySQL en créant une base de données nommée `hx711_data` et en configurant les tables nécessaires (voir les modèles SQLAlchemy dans le code).

4. Modifiez les informations de connexion à la base de données dans le fichier `app.py` :

   ```python
   app.config['MYSQL_HOST'] = 'localhost'
   app.config['MYSQL_USER'] = 'root'
   app.config['MYSQL_PASSWORD'] = 'password'
   app.config['MYSQL_DB'] = 'hx711_data'
   ```

5. Lancez l'API :

   ```bash
   python app.py
   ```

L'API sera accessible à l'adresse `http://localhost:5000`.

## Endpoints de l'API

### 1. Envoyer des données du capteur HX711

**URL:** `/send_hx711_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.
- `status` (obligatoire): Statut du capteur.
- `poids` (obligatoire): Valeur du poids mesuré.
- `limit_` (optionnel): Limite de poids.

**Exemple de requête:**

```bash
GET /send_hx711_data?capteur=123&status=ok&poids=857&limit_=6474
```

**Réponse:**

- Succès: `{"message": "Data inserted successfully"}`
- Erreur: `{"error": "Missing data"}` ou `{"error": "Database error"}`

### 2. Récupérer les dernières données du capteur HX711

**URL:** `/get_last_hx711_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.

**Exemple de requête:**

```bash
GET /get_last_hx711_data?capteur=123
```

**Réponse:**

- Succès: `{"id": 1, "capteur": "123", "status": "ok", "poids": 857, "limit_": 6474, "timestamp": "2023-10-01T12:00:00"}`
- Erreur: `{"error": "No data found"}` ou `{"error": "Database error"}`

### 3. Envoyer des données du capteur FC51

**URL:** `/send_fc51_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.
- `status` (obligatoire): Statut du capteur.
- `obstacle_gauche` (optionnel, par défaut 0): Détection d'obstacle à gauche (0: pas d'obstacle, 1: obstacle).
- `obstacle_droite` (optionnel, par défaut 0): Détection d'obstacle à droite.
- `obstacle_devant` (optionnel, par défaut 0): Détection d'obstacle devant.
- `obstacle_deriere` (optionnel, par défaut 0): Détection d'obstacle derrière.

**Exemple de requête:**

```bash
GET /send_fc51_data?capteur=123&status=ok&obstacle_gauche=0&obstacle_droite=0&obstacle_devant=1&obstacle_deriere=0
```

**Réponse:**

- Succès: `{"message": "Data inserted successfully"}`
- Erreur: `{"error": "Missing data"}` ou `{"error": "Database error"}`

### 4. Récupérer les dernières données du capteur FC51

**URL:** `/get_last_fc51_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.

**Exemple de requête:**

```bash
GET /get_last_fc51_data?capteur=123
```

**Réponse:**

- Succès: `{"id": 1, "capteur": "123", "status": "ok", "obstacle_gauche": 0, "obstacle_droite": 0, "obstacle_devant": 1, "obstacle_deriere": 0, "timestamp": "2023-10-01T12:00:00"}`
- Erreur: `{"error": "No data found"}` ou `{"error": "Database error"}`

### 5. Envoyer des données du capteur LM35

**URL:** `/send_lm35_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.
- `status` (obligatoire): Statut du capteur.
- `temperature` (obligatoire): Température mesurée.

**Exemple de requête:**

```bash
GET /send_lm35_data?capteur=123&status=ok&temperature=16
```

**Réponse:**

- Succès: `{"message": "Temperature data inserted successfully"}`
- Erreur: `{"error": "Missing data"}` ou `{"error": "Database error"}`

### 6. Récupérer les dernières données du capteur LM35

**URL:** `/get_last_lm35_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.

**Exemple de requête:**

```bash
GET /get_last_lm35_data?capteur=123
```

**Réponse:**

- Succès: `{"id": 1, "capteur": "123", "status": "ok", "temperature": 16, "timestamp": "2023-10-01T12:00:00"}`
- Erreur: `{"error": "No data found"}` ou `{"error": "Database error"}`

### 7. Envoyer des données du capteur TCS230

**URL:** `/send_tcs230_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.
- `status` (obligatoire): Statut du capteur.
- `red` (obligatoire): Valeur de la composante rouge.
- `green` (obligatoire): Valeur de la composante verte.
- `blue` (obligatoire): Valeur de la composante bleue.

**Exemple de requête:**

```bash
GET /send_tcs230_data?capteur=123&status=ok&red=1&green=0&blue=0
```

**Réponse:**

- Succès: `{"message": "Data inserted successfully"}`
- Erreur: `{"error": "Missing data"}` ou `{"error": "Database error"}`

### 8. Récupérer les dernières données du capteur TCS230

**URL:** `/get_last_tcs230_data`

**Méthode:** `GET`

**Paramètres:**

- `capteur` (obligatoire): Identifiant du capteur.

**Exemple de requête:**

```bash
GET /get_last_tcs230_data?capteur=123
```

**Réponse:**

- Succès: `{"id": 1, "capteur": "123", "status": "ok", "red": 1, "green": 0, "blue": 0, "timestamp": "2023-10-01T12:00:00"}`
- Erreur: `{"error": "No data found"}` ou `{"error": "Database error"}`

## Gestion des utilisateurs et des véhicules

L'API inclut également des endpoints pour la gestion des utilisateurs et des véhicules, mais ceux-ci ne sont pas détaillés dans cette documentation. Vous pouvez consulter le code source pour plus d'informations sur ces fonctionnalités.

## Conclusion

Cette API permet de configurer et de récupérer les données de différents capteurs (HX711, FC51, LM35, TCS230) en utilisant des requêtes HTTP simples. Assurez-vous que la base de données est correctement configurée et que les tables nécessaires sont créées avant d'utiliser l'API.
