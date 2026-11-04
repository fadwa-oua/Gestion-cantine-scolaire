from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Ajouter les fonctions min et max aux templates Jinja2
app.jinja_env.globals.update(min=min, max=max)

def init_db():
    conn = sqlite3.connect('cantine.db')
    c = conn.cursor()
    
    
    c.execute('''CREATE TABLE IF NOT EXISTS cantine (
        id_cantine INTEGER PRIMARY KEY AUTOINCREMENT,
        nomcantine TEXT,
        capacite_cantine INTEGER,
        heur_d_ouverture TEXT,
        heur_d_cloture TEXT,
        adress_cantine TEXT,
        numero_du_telephone_de_la_cantine TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS produits (
        id_produits INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_du_produit TEXT,
        categories_du_produit TEXT,
        unite_de_mesure TEXT,
        prix_unitaire REAL,
        seuil_alert INTEGER,
        stock REAL DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS menus (
        id_menus INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_de_menu TEXT,
        date_de_menu DATE,
        type_de_menu TEXT,
        calories INTEGER,
        prix_de_menu REAL,
        publie INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS repas (
        id_repas INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_du_repas TEXT,
        type TEXT,
        description TEXT,
        calories INTEGER,
        glucides REAL DEFAULT 0,
        lipides REAL DEFAULT 0,
        proteines REAL DEFAULT 0,
        fibres REAL DEFAULT 0,
        prix REAL,
        disponible_cette_semaine INTEGER DEFAULT 1,
        regimes_compatibles TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS contient (
        id_menus INTEGER,
        id_repas INTEGER,
        PRIMARY KEY (id_menus, id_repas),
        FOREIGN KEY (id_menus) REFERENCES menus(id_menus),
        FOREIGN KEY (id_repas) REFERENCES repas(id_repas)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS eleves (
        id_eleve INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_d_eleve TEXT,
        prenom_d_eleve TEXT,
        date_de_naissance DATE,
        class_d_etude TEXT,
        allergie TEXT,
        num_de_badge TEXT UNIQUE,
        regime_alimentaire TEXT,
        id_cantine INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tuteur (
        id_tuteur TEXT PRIMARY KEY,
        nom_de_tuteur TEXT,
        prenom_du_tuteur TEXT,
        numero_telephone_tuteur TEXT,
        email_tuteur TEXT,
        adress_tuteur TEXT,
        type_de_tuteur TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS responsable (
        id_tuteur TEXT,
        id_eleve INTEGER,
        PRIMARY KEY (id_tuteur, id_eleve),
        FOREIGN KEY (id_tuteur) REFERENCES tuteur(id_tuteur),
        FOREIGN KEY (id_eleve) REFERENCES eleves(id_eleve)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS commande (
        id_commande INTEGER PRIMARY KEY AUTOINCREMENT,
        date_de_commande DATE,
        status_de_commande TEXT,
        montant_du_commande REAL,
        id_eleve INTEGER,
        id_cantine INTEGER,
        FOREIGN KEY (id_eleve) REFERENCES eleves(id_eleve)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS concerne (
        id_repas INTEGER,
        id_commande INTEGER,
        quantite INTEGER,
        PRIMARY KEY (id_repas, id_commande),
        FOREIGN KEY (id_repas) REFERENCES repas(id_repas),
        FOREIGN KEY (id_commande) REFERENCES commande(id_commande)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id_payments INTEGER PRIMARY KEY AUTOINCREMENT,
        date_de_paiement DATE,
        montant_paye REAL,
        mode_paiement TEXT,
        status_paiement TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS effectue_par (
        id_eleve INTEGER,
        id_payments INTEGER,
        PRIMARY KEY (id_eleve, id_payments),
        FOREIGN KEY (id_eleve) REFERENCES eleve(id_eleve),
        FOREIGN KEY (id_payments) REFERENCES payments(id_payments)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS suivi_nutritionnel (
        id_suivi INTEGER PRIMARY KEY AUTOINCREMENT,
        glucide REAL,
        lipide REAL,
        calories REAL,
        fibres REAL,
        proteine REAL,
        date_de_suivi DATE,
        id_eleve INTEGER,
        periode TEXT,
        recommandations TEXT,
        FOREIGN KEY (id_eleve) REFERENCES eleves(id_eleve)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id_user INTEGER PRIMARY KEY AUTOINCREMENT,
        badge_num TEXT UNIQUE,
        user_type TEXT,
        nom TEXT,
        prenom TEXT
    )''')
    
    c.execute("SELECT * FROM users WHERE badge_num = '1300001'")
    if not c.fetchone():
        c.execute('''INSERT INTO users (badge_num, user_type, nom, prenom) 
                     VALUES ('1300001', 'admin', 'Admin', 'Principal')''')
    
    c.execute("SELECT COUNT(*) FROM repas")
    if c.fetchone()[0] == 0:
        repas_test = [
            ('Salade Verte', 'Entrée', 'Salade fraîche de saison', 50, 5, 2, 1, 3, 8.00, 1, 'Végétarien,Diabétique,Hypertendu,Faible en cholestérol'),
            ('Poulet Rôti', 'Plat Principal', 'Poulet mariné aux herbes', 350, 0, 15, 35, 0, 25.00, 1, 'Hypertendu,Faible en cholestérol'),
            ('Riz Basmati', 'Accompagnement', 'Riz parfumé', 200, 45, 1, 4, 1, 5.00, 1, 'Végétarien,Hypertendu,Faible en cholestérol'),
            ('Soupe de Légumes', 'Entrée', 'Soupe maison du jour', 100, 15, 2, 3, 4, 7.00, 1, 'Végétarien,Diabétique,Hypertendu,Faible en cholestérol'),
            ('Couscous aux Légumes', 'Plat Principal', 'Couscous traditionnel', 400, 60, 5, 12, 8, 30.00, 1, 'Végétarien,Hypertendu'),
            ('Yaourt Nature', 'Dessert', 'Yaourt fermier', 80, 12, 2, 5, 0, 4.00, 1, 'Végétarien,Diabétique,Hypertendu,Faible en cholestérol'),
            ('Fruit de Saison', 'Dessert', 'Fruit frais', 70, 18, 0, 1, 3, 3.00, 1, 'Végétarien,Diabétique,Hypertendu,Faible en cholestérol')
        ]
        c.executemany('''INSERT INTO repas (nom_du_repas, type, description, calories, glucides, lipides, proteines, fibres, prix, disponible_cette_semaine, regimes_compatibles) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', repas_test)
    
    c.execute("SELECT COUNT(*) FROM menus")
    if c.fetchone()[0] == 0:
        today = datetime.now()
        menus_test = [
            ('Menu Équilibré', today.strftime('%Y-%m-%d'), 'Menu Complet', 650, 0, 1),
            ('Menu Végétarien', (today + timedelta(days=1)).strftime('%Y-%m-%d'), 'Menu Végétarien', 600, 0, 1)
        ]
        c.executemany('''INSERT INTO menus (nom_de_menu, date_de_menu, type_de_menu, calories, prix_de_menu, publie) 
                         VALUES (?, ?, ?, ?, ?, ?)''', menus_test)
        
        c.execute('INSERT INTO contient (id_menus, id_repas) VALUES (1, 1), (1, 2), (1, 3), (1, 6)')
        c.execute('INSERT INTO contient (id_menus, id_repas) VALUES (2, 4), (2, 5), (2, 7)')
    
    c.execute("SELECT COUNT(*) FROM produits")
    if c.fetchone()[0] == 0:
        produits_test = [
            ('Tomates', 'Légumes', 'kg', 8.50, 20, 50),
            ('Poulet', 'Viandes', 'kg', 65.00, 10, 15),
            ('Riz', 'Céréales', 'kg', 12.00, 30, 100)
        ]
        c.executemany('''INSERT INTO produits (nom_du_produit, categories_du_produit, unite_de_mesure, prix_unitaire, seuil_alert, stock) 
                         VALUES (?, ?, ?, ?, ?, ?)''', produits_test)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('cantine.db')
    conn.row_factory = sqlite3.Row
    return conn
def get_cantine_info():
    """Récupère les informations de la cantine"""
    conn = get_db()
    cantine = conn.execute('SELECT * FROM cantine WHERE id_cantine = 1').fetchone()
    conn.close()
    
    if not cantine:
        # Créer les infos par défaut si elles n'existent pas
        conn = get_db()
        conn.execute('''INSERT INTO cantine (nomcantine, capacite_cantine, heur_d_ouverture, heur_d_cloture, adress_cantine, numero_du_telephone_de_la_cantine)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     ('Cantine Scolaire Excellence', 200, '08:00', '16:00', '123 Avenue Mohammed V, Casablanca', '0522-123-456'))
        conn.commit()
        cantine = conn.execute('SELECT * FROM cantine WHERE id_cantine = 1').fetchone()
        conn.close()
    
    return cantine

@app.context_processor
def inject_cantine_info():
    """Injecte les informations de la cantine dans tous les templates"""
    return dict(cantine_info=get_cantine_info())

def update_db_for_images():
    conn = get_db()
    try:
        cursor = conn.execute("PRAGMA table_info(menus)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'image_menu' not in columns:
            conn.execute('ALTER TABLE menus ADD COLUMN image_menu TEXT')
            conn.commit()
            print("✓ Colonne image_menu ajoutée avec succès")
        else:
            print("✓ Colonne _menu existe déjà")
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
    finally:
        conn.close()
def update_db_for_ingredients():
    """Ajoute une table pour lier les produits aux repas"""
    conn = get_db()
    try:
        # Créer la table des ingrédients (produits utilisés dans les repas)
        conn.execute('''CREATE TABLE IF NOT EXISTS ingredients_repas (
            id_ingredient INTEGER PRIMARY KEY AUTOINCREMENT,
            id_repas INTEGER,
            id_produit INTEGER,
            quantite_necessaire REAL,
            FOREIGN KEY (id_repas) REFERENCES repas(id_repas),
            FOREIGN KEY (id_produit) REFERENCES produits(id_produits),
            UNIQUE(id_repas, id_produit)
        )''')
        
        conn.commit()
        print("✓ Table ingredients_repas créée avec succès")
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
    finally:
        conn.close()
def update_db_for_employees():
    """Ajoute la table des employés"""
    conn = get_db()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS employees (
            id_employees VARCHAR(10) PRIMARY KEY,
            nom_complet VARCHAR(100),
            numero_du_telephone_emplye VARCHAR(20),
            emaile_emplye VARCHAR(100),
            adress_emplye VARCHAR(255),
            date_d_embauchement DATE,
            post VARCHAR(50),
            id_cantine INT,
            FOREIGN KEY (id_cantine) REFERENCES cantine(id_cantine)
        )''')
        
        conn.commit()
        print("✓ Table employees créée avec succès")
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
    finally:
        conn.close()
@app.route('/admin/produits/details/<int:produit_id>')
def admin_produits_details(produit_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    # Récupérer le produit
    produit = conn.execute('SELECT * FROM produits WHERE id_produits = ?', (produit_id,)).fetchone()
    
    # Récupérer tous les repas
    repas = conn.execute('SELECT * FROM repas ORDER BY type, nom_du_repas').fetchall()
    
    # Récupérer les repas qui utilisent ce produit
    ingredients = conn.execute('''
        SELECT ir.*, r.nom_du_repas, r.type 
        FROM ingredients_repas ir
        JOIN repas r ON ir.id_repas = r.id_repas
        WHERE ir.id_produit = ?
    ''', (produit_id,)).fetchall()
    
    conn.close()
    
    return render_template('admin_produits_details.html', 
                          produit=produit, 
                          repas=repas,
                          ingredients=ingredients,
                          nom=session.get('nom'))

@app.route('/admin/produits/<int:produit_id>/ajouter-ingredient', methods=['POST'])
def admin_ajouter_ingredient(produit_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    repas_id = request.form.get('repas_id')
    quantite = request.form.get('quantite')
    
    conn = get_db()
    try:
        conn.execute('''INSERT INTO ingredients_repas (id_repas, id_produit, quantite_necessaire) 
                        VALUES (?, ?, ?)''',
                     (repas_id, produit_id, quantite))
        conn.commit()
        flash('Ingrédient ajouté avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_produits_details', produit_id=produit_id))

@app.route('/admin/produits/supprimer-ingredient/<int:ingredient_id>/<int:produit_id>')
def admin_supprimer_ingredient(ingredient_id, produit_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM ingredients_repas WHERE id_ingredient = ?', (ingredient_id,))
        conn.commit()
        flash('Ingrédient supprimé avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_produits_details', produit_id=produit_id))

# Modifier la route de changement de statut pour déduire le stock automatiquement
@app.route('/admin/commandes/changer-statut/<int:commande_id>', methods=['POST'])
def admin_changer_statut(commande_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    nouveau_statut = request.form.get('statut')
    
    conn = get_db()
    try:
        ancien_statut = conn.execute('SELECT status_de_commande FROM commande WHERE id_commande = ?', 
                                    (commande_id,)).fetchone()['status_de_commande']
        
        # Si le statut passe à "En préparation", déduire le stock des ingrédients
        if nouveau_statut == 'En préparation' and ancien_statut != 'En préparation':
            # Récupérer tous les repas de cette commande
            repas_commande = conn.execute('''
                SELECT co.id_repas, co.quantite 
                FROM concerne co
                WHERE co.id_commande = ?
            ''', (commande_id,)).fetchall()
            
            # Pour chaque repas, déduire les ingrédients nécessaires
            for repas in repas_commande:
                ingredients = conn.execute('''
                    SELECT id_produit, quantite_necessaire 
                    FROM ingredients_repas 
                    WHERE id_repas = ?
                ''', (repas['id_repas'],)).fetchall()
                
                for ingredient in ingredients:
                    quantite_totale = ingredient['quantite_necessaire'] * repas['quantite']
                    
                    # Vérifier si le stock est suffisant
                    produit = conn.execute('SELECT stock FROM produits WHERE id_produits = ?', 
                                          (ingredient['id_produit'],)).fetchone()
                    
                    if produit and produit['stock'] >= quantite_totale:
                        conn.execute('''UPDATE produits 
                                       SET stock = stock - ? 
                                       WHERE id_produits = ?''',
                                    (quantite_totale, ingredient['id_produit']))
                    else:
                        conn.rollback()
                        flash(f'Stock insuffisant pour préparer cette commande !', 'error')
                        return redirect(url_for('admin_commandes'))
        
        conn.execute('UPDATE commande SET status_de_commande = ? WHERE id_commande = ?', 
                    (nouveau_statut, commande_id))
        conn.commit()
        flash(f'Statut mis à jour : {nouveau_statut}', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_commandes'))

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    badge_num = request.form.get('badge_num')
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE badge_num = ?", (badge_num,)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id_user']
        session['user_type'] = user['user_type']
        session['nom'] = user['nom']
        session['prenom'] = user['prenom']
        flash('Connexion réussie !', 'success')
        
        if user['user_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        flash('Numéro de badge invalide !', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('index'))

@app.route('/recuperer-badge')
def recuperer_badge():
    return render_template('recuperer_badge.html')

@app.route('/recuperer-badge', methods=['POST'])
def recuperer_badge_post():
    nom_eleve = request.form.get('nom_eleve')
    prenom_eleve = request.form.get('prenom_eleve')
    date_naissance = request.form.get('date_naissance')
    tel_tuteur = request.form.get('tel_tuteur')
    
    conn = get_db()
    
    try:
        eleve = conn.execute('''
            SELECT e.*, t.numero_telephone_tuteur
            FROM eleves e
            JOIN responsable r ON e.id_eleve = r.id_eleve
            JOIN tuteur t ON r.id_tuteur = t.id_tuteur
            WHERE e.nom_d_eleve = ? 
            AND e.prenom_d_eleve = ? 
            AND e.date_de_naissance = ?
            AND t.numero_telephone_tuteur = ?
        ''', (nom_eleve, prenom_eleve, date_naissance, tel_tuteur)).fetchone()
        
        if eleve:
            badge_num = eleve['num_de_badge']
            conn.close()
            return render_template('badge_recupere.html', 
                                 badge_num=badge_num,
                                 nom=nom_eleve,
                                 prenom=prenom_eleve)
        else:
            conn.close()
            flash('Aucun compte trouvé avec ces informations.', 'error')
            return redirect(url_for('recuperer_badge'))
    
    except Exception as e:
        conn.close()
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('recuperer_badge'))

@app.route('/inscription')
def inscription():
    return render_template('inscription.html')

@app.route('/inscription', methods=['POST'])
def inscription_post():
    nom_eleve = request.form.get('nom_eleve')
    prenom_eleve = request.form.get('prenom_eleve')
    date_naissance = request.form.get('date_naissance')
    classe = request.form.get('classe')
    allergie = request.form.get('allergie', '')
    regime = request.form.get('regime', '')
    
    # IMPORTANT: Récupérer l'ID tuteur saisi par l'utilisateur
    id_tuteur = request.form.get('id_tuteur')
    nom_tuteur = request.form.get('nom_tuteur')
    prenom_tuteur = request.form.get('prenom_tuteur')
    tel_tuteur = request.form.get('tel_tuteur')
    email_tuteur = request.form.get('email_tuteur', '')
    adresse_tuteur = request.form.get('adresse_tuteur', '')
    type_tuteur = request.form.get('type_tuteur')
    
    if len(tel_tuteur) != 10:
        flash('Le numéro de téléphone doit contenir 10 chiffres !', 'error')
        return redirect(url_for('inscription'))
    
    badge_num = str(int(datetime.now().timestamp() * 1000))[-6:]
    
    conn = get_db()
    try:
        # Vérifier si le tuteur existe déjà avec cet ID
        tuteur_existant = conn.execute('SELECT id_tuteur FROM tuteur WHERE id_tuteur = ?', (id_tuteur,)).fetchone()
        
        if not tuteur_existant:
            # Créer un nouveau tuteur avec l'ID saisi par l'utilisateur
            conn.execute('''INSERT INTO tuteur (id_tuteur, nom_de_tuteur, prenom_du_tuteur, numero_telephone_tuteur, email_tuteur, adress_tuteur, type_de_tuteur) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (id_tuteur, nom_tuteur, prenom_tuteur, tel_tuteur, email_tuteur, adresse_tuteur, type_tuteur))
        
        # Créer l'élève
        conn.execute('''INSERT INTO eleves (nom_d_eleve, prenom_d_eleve, date_de_naissance, class_d_etude, allergie, num_de_badge, regime_alimentaire, id_cantine) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
                     (nom_eleve, prenom_eleve, date_naissance, classe, allergie, badge_num, regime))
        
        eleve_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Lier le tuteur (avec l'ID saisi) et l'élève
        conn.execute('INSERT INTO responsable (id_tuteur, id_eleve) VALUES (?, ?)', (id_tuteur, eleve_id))
        
        # Créer l'utilisateur
        conn.execute('''INSERT INTO users (badge_num, user_type, nom, prenom) 
                        VALUES (?, 'user', ?, ?)''', (badge_num, nom_eleve, prenom_eleve))
        
        conn.commit()
        return render_template('badge_success.html', badge_num=badge_num)
    
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('inscription'))
    finally:
        conn.close()
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Veuillez vous connecter', 'error')
        return redirect(url_for('index'))
    
    conn = get_db()
    
    
    today = datetime.now()
    
   
    start_week = today - timedelta(days=today.weekday())
    
    end_week = start_week + timedelta(days=6)
    
    
    menus = conn.execute('''
        SELECT m.*
        FROM menus m
        WHERE m.publie = 1 
        AND DATE(m.date_de_menu) BETWEEN DATE(?) AND DATE(?)
        ORDER BY m.date_de_menu ASC
    ''', (start_week.strftime('%Y-%m-%d'), end_week.strftime('%Y-%m-%d'))).fetchall()
    
    panier = session.get('panier', [])
    total = sum(item['prix'] * item['quantite'] for item in panier)
    
    conn.close()
    
    return render_template('user_dashboard.html', 
                          nom=session.get('nom'),
                          prenom=session.get('prenom'),
                          menus=menus,
                          panier=panier,
                          total=total)

@app.route('/user/menu-details/<int:menu_id>')
def menu_details(menu_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    menu = conn.execute('SELECT * FROM menus WHERE id_menus = ?', (menu_id,)).fetchone()
    
    if not menu:
        conn.close()
        flash('Menu introuvable', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Récupérer le régime alimentaire de l'élève
    user = conn.execute('SELECT * FROM users WHERE id_user = ?', (session['user_id'],)).fetchone()
    eleve = conn.execute('SELECT * FROM eleves WHERE num_de_badge = ?', (user['badge_num'],)).fetchone()
    regime_eleve = eleve['regime_alimentaire'] if eleve and eleve['regime_alimentaire'] else None
    
    # Récupérer tous les repas du menu
    repas_menu = conn.execute('''
        SELECT r.*, c.id_menus
        FROM repas r
        JOIN contient c ON r.id_repas = c.id_repas
        WHERE c.id_menus = ?
        ORDER BY 
            CASE r.type
                WHEN 'Entrée' THEN 1
                WHEN 'Plat Principal' THEN 2
                WHEN 'Accompagnement' THEN 3
                WHEN 'Dessert' THEN 4
                ELSE 5
            END
    ''', (menu_id,)).fetchall()
    
    # Filtrer les repas selon le régime alimentaire de l'élève
    repas_compatibles = []
    repas_non_compatibles = []
    
    for repas in repas_menu:
        regimes_compatibles = repas['regimes_compatibles'].split(',') if repas['regimes_compatibles'] else []
        
        # Si l'élève a un régime alimentaire spécifique
        if regime_eleve:
            # Vérifier si le repas est compatible avec le régime
            if regime_eleve in regimes_compatibles:
                repas_compatibles.append(repas)
            else:
                repas_non_compatibles.append(repas)
        else:
            # Si l'élève n'a pas de régime spécifique, tous les repas sont disponibles
            repas_compatibles.append(repas)
    
    panier = session.get('panier', [])
    total = sum(item['prix'] * item['quantite'] for item in panier)
    
    conn.close()
    
    return render_template('menu_details.html',
                          menu=menu,
                          repas_menu=repas_compatibles,
                          repas_non_compatibles=repas_non_compatibles,
                          regime_eleve=regime_eleve,
                          panier=panier,
                          total=total,
                          nom=session.get('nom'),
                          prenom=session.get('prenom'))
@app.route('/user/ajouter-repas-panier/<int:repas_id>/<int:quantite>')
def ajouter_repas_panier(repas_id, quantite):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if quantite < 1:
        flash('Quantité invalide', 'error')
        return redirect(request.referrer or url_for('user_dashboard'))
    
    conn = get_db()
    
    # Récupérer le repas
    repas = conn.execute('SELECT * FROM repas WHERE id_repas = ?', (repas_id,)).fetchone()
    
    if not repas:
        conn.close()
        flash('Repas introuvable', 'error')
        return redirect(request.referrer or url_for('user_dashboard'))
    
    # Vérifier le régime alimentaire de l'élève
    user = conn.execute('SELECT * FROM users WHERE id_user = ?', (session['user_id'],)).fetchone()
    eleve = conn.execute('SELECT * FROM eleves WHERE num_de_badge = ?', (user['badge_num'],)).fetchone()
    regime_eleve = eleve['regime_alimentaire'] if eleve and eleve['regime_alimentaire'] else None
    
    # Vérifier la compatibilité du repas avec le régime
    if regime_eleve:
        regimes_compatibles = repas['regimes_compatibles'].split(',') if repas['regimes_compatibles'] else []
        
        if regime_eleve not in regimes_compatibles:
            conn.close()
            flash(f'⚠️ Ce repas n\'est pas compatible avec votre régime alimentaire ({regime_eleve})', 'error')
            return redirect(request.referrer or url_for('user_dashboard'))
    
    conn.close()
    
    # Ajouter au panier
    panier = session.get('panier', [])
    
    existe = False
    for item in panier:
        if item.get('type') == 'repas' and item.get('id') == repas_id:
            item['quantite'] += quantite
            existe = True
            break
    
    if not existe:
        panier.append({
            'id': repas['id_repas'],
            'nom': repas['nom_du_repas'],
            'prix': repas['prix'],
            'type': 'repas',
            'quantite': quantite
        })
    
    session['panier'] = panier
    flash(f'✅ {quantite}x {repas["nom_du_repas"]} ajouté(s) au panier !', 'success')
    
    return redirect(request.referrer or url_for('user_dashboard'))

@app.route('/user/retirer-panier/<int:index>')
def retirer_panier(index):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    panier = session.get('panier', [])
    if 0 <= index < len(panier):
        panier.pop(index)
        session['panier'] = panier
        flash('Article retiré du panier', 'success')
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/commander', methods=['POST'])
def commander():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    panier = session.get('panier', [])
    if not panier:
        flash('Votre panier est vide !', 'error')
        return redirect(url_for('user_dashboard'))
    
    montant_total = sum(item['prix'] * item['quantite'] for item in panier)
    
    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id_user = ?', (session['user_id'],)).fetchone()
        eleve = conn.execute('SELECT * FROM eleves WHERE num_de_badge = ?', (user['badge_num'],)).fetchone()
        
        conn.execute('''INSERT INTO commande (date_de_commande, status_de_commande, montant_du_commande, id_eleve, id_cantine) 
                        VALUES (?, 'En attente', ?, ?, 1)''',
                     (datetime.now().strftime('%Y-%m-%d'), montant_total, eleve['id_eleve']))
        
        commande_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        for item in panier:
            if item.get('type') == 'repas':
                conn.execute('INSERT INTO concerne (id_repas, id_commande, quantite) VALUES (?, ?, ?)',
                            (item['id'], commande_id, item['quantite']))
        
        conn.commit()
        session['panier'] = []
        flash('Commande passée avec succès !', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/status-commandes')
def status_commandes():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    user = conn.execute('SELECT * FROM users WHERE id_user = ?', (session['user_id'],)).fetchone()
    eleve = conn.execute('SELECT * FROM eleves WHERE num_de_badge = ?', (user['badge_num'],)).fetchone()
    
    commandes = []
    if eleve:
        commandes = conn.execute('''
            SELECT c.*, GROUP_CONCAT(r.nom_du_repas, ', ') as repas_list
            FROM commande c
            LEFT JOIN concerne co ON c.id_commande = co.id_commande
            LEFT JOIN repas r ON co.id_repas = r.id_repas
            WHERE c.id_eleve = ?
            GROUP BY c.id_commande
            ORDER BY c.date_de_commande DESC
        ''', (eleve['id_eleve'],)).fetchall()
    
    conn.close()
    
    return render_template('status_commandes.html',
                          commandes=commandes,
                          nom=session.get('nom'),
                          prenom=session.get('prenom'))

@app.route('/user/menu-personnalise')
def menu_personnalise():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    user = conn.execute('SELECT * FROM users WHERE id_user = ?', (session['user_id'],)).fetchone()
    eleve = conn.execute('SELECT * FROM eleves WHERE num_de_badge = ?', (user['badge_num'],)).fetchone()
    
    regime = eleve['regime_alimentaire'] if eleve and eleve['regime_alimentaire'] else ''
    
    repas = conn.execute('SELECT * FROM repas WHERE disponible_cette_semaine = 1').fetchall()
    
    repas_compatibles = []
    repas_incompatibles = []
    repas_alternatifs = []
    
    for r in repas:
        try:
            regimes_compatibles_str = r['regimes_compatibles']
        except (KeyError, IndexError):
            regimes_compatibles_str = None
        
        regimes_ok = regimes_compatibles_str.split(',') if regimes_compatibles_str else []
        
        if regime and regimes_ok:
            if regime in regimes_ok:
                repas_compatibles.append(r)
            else:
                repas_incompatibles.append(r)
                alternative = conn.execute('''SELECT * FROM repas 
                                             WHERE type = ? AND id_repas != ? 
                                             AND disponible_cette_semaine = 1 
                                             AND regimes_compatibles LIKE ?
                                             LIMIT 1''', 
                                           (r['type'], r['id_repas'], f'%{regime}%')).fetchone()
                if alternative:
                    repas_alternatifs.append({'incompatible': r, 'alternative': alternative})
        else:
            repas_compatibles.append(r)
    
    conn.close()
    
    return render_template('menu_personnalise.html', 
                          repas=repas_compatibles, 
                          repas_incompatibles=repas_incompatibles,
                          repas_alternatifs=repas_alternatifs,
                          regime=regime,
                          nom=session.get('nom'),
                          prenom=session.get('prenom'))

@app.route('/user/rapport-nutritionnel')
def rapport_nutritionnel():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    user = conn.execute('SELECT * FROM users WHERE id_user = ?', (session['user_id'],)).fetchone()
    eleve = conn.execute('SELECT * FROM eleves WHERE num_de_badge = ?', (user['badge_num'],)).fetchone()
    
    if not eleve:
        conn.close()
        return redirect(url_for('user_dashboard'))
    
    date_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    commandes = conn.execute('''SELECT c.*, GROUP_CONCAT(r.id_repas) as repas_ids
                                FROM commande c
                                LEFT JOIN concerne co ON c.id_commande = co.id_commande
                                LEFT JOIN repas r ON co.id_repas = r.id_repas
                                WHERE c.id_eleve = ? 
                                AND c.date_de_commande >= ?
                                AND c.status_de_commande = 'Validée'
                                GROUP BY c.id_commande''', 
                            (eleve['id_eleve'], date_limite)).fetchall()
    
    total_calories = 0
    total_glucides = 0
    total_lipides = 0
    total_proteines = 0
    total_fibres = 0
    nb_repas = 0
    
    for cmd in commandes:
        if cmd['repas_ids']:
            repas_ids = cmd['repas_ids'].split(',')
            for repas_id in repas_ids:
                repas = conn.execute('SELECT * FROM repas WHERE id_repas = ?', (repas_id,)).fetchone()
                if repas:
                    total_calories += repas['calories'] or 0
                    total_glucides += repas['glucides'] or 0
                    total_lipides += repas['lipides'] or 0
                    total_proteines += repas['proteines'] or 0
                    total_fibres += repas['fibres'] or 0
                    nb_repas += 1
    
    moy_calories = total_calories / nb_repas if nb_repas > 0 else 0
    moy_glucides = total_glucides / nb_repas if nb_repas > 0 else 0
    moy_lipides = total_lipides / nb_repas if nb_repas > 0 else 0
    moy_proteines = total_proteines / nb_repas if nb_repas > 0 else 0
    moy_fibres = total_fibres / nb_repas if nb_repas > 0 else 0
    
    recommandations = []
    statut = 'positive'
    
    regime = eleve['regime_alimentaire']
    
    if regime == 'Diabétique':
        if moy_glucides > 50:
            recommandations.append('⚠️ Votre consommation de glucides est élevée. Privilégiez les légumes et protéines.')
            statut = 'negative'
        else:
            recommandations.append('✓ Votre consommation de glucides est bien contrôlée.')
    
    if regime == 'Hypertendu':
        recommandations.append('✓ Continuez à éviter les aliments trop salés.')
    
    if regime == 'Faible en cholestérol':
        if moy_lipides > 15:
            recommandations.append('⚠️ Attention à votre consommation de lipides. Privilégiez le poisson.')
            statut = 'negative'
        else:
            recommandations.append('✓ Votre consommation de lipides est adaptée.')
    
    if moy_calories < 500:
        recommandations.append('⚠️ Vos apports caloriques sont faibles. Assurez-vous de manger suffisamment.')
        statut = 'negative'
    elif moy_calories > 800:
        recommandations.append('⚠️ Vos apports caloriques sont élevés. Variez avec des repas plus légers.')
        statut = 'negative'
    else:
        recommandations.append('✓ Vos apports caloriques sont équilibrés.')
    
    if moy_fibres < 3:
        recommandations.append('💡 Augmentez votre consommation de fibres.')
    
    if moy_proteines < 15:
        recommandations.append('💡 Pensez à augmenter vos apports en protéines.')
    
    if not recommandations:
        recommandations.append('✓ Votre alimentation est équilibrée.')
    
    conn.execute('''INSERT INTO suivi_nutritionnel 
                    (glucide, lipide, calories, fibres, proteine, date_de_suivi, id_eleve, periode, recommandations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (moy_glucides, moy_lipides, moy_calories, moy_fibres, moy_proteines, 
                 datetime.now().strftime('%Y-%m-%d'), eleve['id_eleve'], '30 derniers jours', 
                 ' | '.join(recommandations)))
    
    conn.commit()
    conn.close()
    
    return render_template('rapport_nutritionnel.html',
                          eleve=eleve,
                          regime=regime,
                          nb_repas=nb_repas,
                          moy_calories=moy_calories,
                          moy_glucides=moy_glucides,
                          moy_lipides=moy_lipides,
                          moy_proteines=moy_proteines,
                          moy_fibres=moy_fibres,
                          recommandations=recommandations,
                          statut=statut,
                          nom=session.get('nom'),
                          prenom=session.get('prenom'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('index'))
    
    conn = get_db()
    
    total_eleves = conn.execute('SELECT COUNT(*) as count FROM eleves').fetchone()['count']
    total_commandes = conn.execute('SELECT COUNT(*) as count FROM commande').fetchone()['count']
    commandes_jour = conn.execute("SELECT COUNT(*) as count FROM commande WHERE date_de_commande = date('now')").fetchone()['count']
    total_employees = conn.execute('SELECT COUNT(*) as count FROM employees').fetchone()['count']
    # Nouvelle statistique : Montant total des commandes validées
    revenus_valides = conn.execute('''
        SELECT COALESCE(SUM(montant_du_commande), 0) as total 
        FROM commande 
        WHERE status_de_commande = 'Validée'
    ''').fetchone()['total']
    
    # Revenus du jour (commandes validées aujourd'hui)
    revenus_jour = conn.execute('''
        SELECT COALESCE(SUM(montant_du_commande), 0) as total 
        FROM commande 
        WHERE status_de_commande = 'Validée' 
        AND date_de_commande = date('now')
    ''').fetchone()['total']
    
    # Revenus du mois en cours
    revenus_mois = conn.execute('''
        SELECT COALESCE(SUM(montant_du_commande), 0) as total 
        FROM commande 
        WHERE status_de_commande = 'Validée' 
        AND strftime('%Y-%m', date_de_commande) = strftime('%Y-%m', 'now')
    ''').fetchone()['total']
    
    produits_alerte = conn.execute('SELECT * FROM produits WHERE stock <= seuil_alert ORDER BY stock ASC').fetchall()
    commandes_recentes = conn.execute('''SELECT c.*, e.nom_d_eleve, e.prenom_d_eleve FROM commande c
        LEFT JOIN eleves e ON c.id_eleve = e.id_eleve ORDER BY c.date_de_commande DESC LIMIT 5''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                          nom=session.get('nom'), 
                          total_eleves=total_eleves,
                          total_commandes=total_commandes, 
                          commandes_jour=commandes_jour,
                          total_employees=total_employees,
                          revenus_valides=revenus_valides,
                          revenus_jour=revenus_jour,
                          revenus_mois=revenus_mois,
                          produits_alerte=produits_alerte, 
                          commandes_recentes=commandes_recentes)
# Routes pour la gestion des employés

@app.route('/admin/employees')
def admin_employees():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    employees_rows = conn.execute('''
        SELECT * FROM employees 
        ORDER BY nom_complet ASC
    ''').fetchall()
    conn.close()
    
    # Convertir les Row en dictionnaires pour permettre la sérialisation JSON
    employees = []
    for e in employees_rows:
        employees.append({
            'id_employees': e['id_employees'],
            'nom_complet': e['nom_complet'],
            'numero_du_telephone_emplye': e['numero_du_telephone_emplye'],
            'emaile_emplye': e['emaile_emplye'],
            'adress_emplye': e['adress_emplye'],
            'date_d_embauchement': e['date_d_embauchement'],
            'post': e['post']
        })
    
    return render_template('admin_employees.html', 
                          employees=employees, 
                          nom=session.get('nom'))

@app.route('/admin/employees/recherche')
def admin_employees_recherche():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return {'employees': []}, 403
    
    query = request.args.get('q', '').strip().lower()
    post_filter = request.args.get('post', '').strip()
    
    conn = get_db()
    
    sql = 'SELECT * FROM employees WHERE 1=1'
    params = []
    
    if query:
        sql += ' AND (LOWER(nom_complet) LIKE ? OR LOWER(id_employees) LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])
    
    if post_filter and post_filter != 'Tous':
        sql += ' AND post = ?'
        params.append(post_filter)
    
    sql += ' ORDER BY nom_complet ASC'
    
    employees_rows = conn.execute(sql, params).fetchall()
    conn.close()
    
    employees_list = [{
        'id_employees': e['id_employees'],
        'nom_complet': e['nom_complet'],
        'numero_du_telephone_emplye': e['numero_du_telephone_emplye'],
        'emaile_emplye': e['emaile_emplye'],
        'adress_emplye': e['adress_emplye'],
        'date_d_embauchement': e['date_d_embauchement'],
        'post': e['post']
    } for e in employees_rows]
    
    return {'employees': employees_list}

@app.route('/admin/employees/stats')
def admin_employees_stats():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return {'posts': []}, 403
    
    conn = get_db()
    
    posts_data = conn.execute('''
        SELECT post, COUNT(*) as count 
        FROM employees 
        GROUP BY post 
        ORDER BY count DESC
    ''').fetchall()
    
    posts_list = [{'nom': p['post'], 'count': p['count']} for p in posts_data]
    
    conn.close()
    
    return {'posts': posts_list}

@app.route('/admin/employees/ajouter', methods=['GET', 'POST'])
def admin_employees_ajouter():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('admin_employees_ajouter.html', nom=session.get('nom'))
    
    id_employee = request.form.get('id_employee')
    nom_complet = request.form.get('nom_complet')
    telephone = request.form.get('telephone')
    email = request.form.get('email')
    adresse = request.form.get('adresse')
    date_embauchement = request.form.get('date_embauchement')
    post = request.form.get('post')
    
    conn = get_db()
    try:
        existing = conn.execute('SELECT id_employees FROM employees WHERE id_employees = ?', 
                               (id_employee,)).fetchone()
        
        if existing:
            flash('Un employé avec cet ID existe déjà !', 'error')
            return redirect(url_for('admin_employees_ajouter'))
        
        conn.execute('''INSERT INTO employees 
                       (id_employees, nom_complet, numero_du_telephone_emplye, 
                        emaile_emplye, adress_emplye, date_d_embauchement, post, id_cantine) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
                     (id_employee, nom_complet, telephone, email, adresse, date_embauchement, post))
        conn.commit()
        flash('Employé ajouté avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_employees'))

@app.route('/admin/employees/modifier/<string:employee_id>', methods=['GET', 'POST'])
def admin_employees_modifier(employee_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    if request.method == 'GET':
        employee = conn.execute('SELECT * FROM employees WHERE id_employees = ?', 
                               (employee_id,)).fetchone()
        conn.close()
        
        if not employee:
            flash('Employé introuvable', 'error')
            return redirect(url_for('admin_employees'))
        
        return render_template('admin_employees_modifier.html', 
                             employee=employee, 
                             nom=session.get('nom'))
    
    nom_complet = request.form.get('nom_complet')
    telephone = request.form.get('telephone')
    email = request.form.get('email')
    adresse = request.form.get('adresse')
    date_embauchement = request.form.get('date_embauchement')
    post = request.form.get('post')
    
    try:
        conn.execute('''UPDATE employees 
                       SET nom_complet = ?, 
                           numero_du_telephone_emplye = ?, 
                           emaile_emplye = ?, 
                           adress_emplye = ?, 
                           date_d_embauchement = ?, 
                           post = ? 
                       WHERE id_employees = ?''',
                     (nom_complet, telephone, email, adresse, date_embauchement, post, employee_id))
        conn.commit()
        flash('Employé modifié avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_employees'))

@app.route('/admin/employees/supprimer/<string:employee_id>')
def admin_employees_supprimer(employee_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM employees WHERE id_employees = ?', (employee_id,))
        conn.commit()
        flash('Employé supprimé avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_employees'))

@app.route('/admin/menus')
def admin_menus():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    menus = conn.execute('''SELECT m.*, COUNT(c.id_repas) as nb_repas FROM menus m
        LEFT JOIN contient c ON m.id_menus = c.id_menus GROUP BY m.id_menus ORDER BY m.date_de_menu DESC''').fetchall()
    conn.close()
    
    return render_template('admin_menus.html', menus=menus, nom=session.get('nom'))

@app.route('/admin/menus/ajouter', methods=['GET', 'POST'])
def admin_menus_ajouter():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        conn = get_db()
        repas = conn.execute('SELECT * FROM repas ORDER BY type, nom_du_repas').fetchall()
        conn.close()
        return render_template('admin_menus_ajouter.html', repas=repas, nom=session.get('nom'))
    
    conn = get_db()
    try:
        conn.execute('''INSERT INTO menus (nom_de_menu, date_de_menu, type_de_menu, calories, prix_de_menu, publie) 
                        VALUES (?, ?, ?, ?, 0, ?)''',
                     (request.form.get('nom'), request.form.get('date'), request.form.get('type'),
                      request.form.get('calories', 0), request.form.get('publie', '0')))
        
        menu_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        for repas_id in request.form.getlist('repas_ids'):
            conn.execute('INSERT INTO contient (id_menus, id_repas) VALUES (?, ?)', (menu_id, repas_id))
        
        conn.commit()
        flash('Menu ajouté avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_menus'))

@app.route('/admin/menus/modifier/<int:menu_id>', methods=['GET', 'POST'])
def admin_menus_modifier(menu_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    if request.method == 'GET':
        menu = conn.execute('SELECT * FROM menus WHERE id_menus = ?', (menu_id,)).fetchone()
        repas = conn.execute('SELECT * FROM repas ORDER BY type, nom_du_repas').fetchall()
        repas_menu = conn.execute('SELECT id_repas FROM contient WHERE id_menus = ?', (menu_id,)).fetchall()
        repas_menu_ids = [r['id_repas'] for r in repas_menu]
        conn.close()
        return render_template('admin_menus_modifier.html', 
                             menu=menu, 
                             repas=repas, 
                             repas_menu_ids=repas_menu_ids,
                             nom=session.get('nom'))
    
    try:
        conn.execute('''UPDATE menus SET nom_de_menu = ?, date_de_menu = ?, 
                       type_de_menu = ?, calories = ?, publie = ? 
                       WHERE id_menus = ?''',
                     (request.form.get('nom'), request.form.get('date'), request.form.get('type'),
                      request.form.get('calories', 0), request.form.get('publie', '0'), menu_id))
        
        conn.execute('DELETE FROM contient WHERE id_menus = ?', (menu_id,))
        
        for repas_id in request.form.getlist('repas_ids'):
            conn.execute('INSERT INTO contient (id_menus, id_repas) VALUES (?, ?)', (menu_id, repas_id))
        
        conn.commit()
        flash('Menu modifié avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_menus'))

@app.route('/admin/menus/supprimer/<int:menu_id>')
def admin_menus_supprimer(menu_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM contient WHERE id_menus = ?', (menu_id,))
        conn.execute('DELETE FROM menus WHERE id_menus = ?', (menu_id,))
        conn.commit()
        flash('Menu supprimé avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_menus'))

@app.route('/admin/menus/publier/<int:menu_id>')
def admin_menus_publier(menu_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('UPDATE menus SET publie = 1 WHERE id_menus = ?', (menu_id,))
        conn.commit()
        flash('Menu publié avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_menus'))

@app.route('/admin/menus/depublier/<int:menu_id>')
def admin_menus_depublier(menu_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('UPDATE menus SET publie = 0 WHERE id_menus = ?', (menu_id,))
        conn.commit()
        flash('Menu dépublié avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_menus'))

@app.route('/admin/repas')
def admin_repas():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    repas = conn.execute('SELECT * FROM repas ORDER BY type, nom_du_repas').fetchall()
    conn.close()
    
    return render_template('admin_repas.html', repas=repas, nom=session.get('nom'))

@app.route('/admin/repas/ajouter', methods=['GET', 'POST'])
def admin_repas_ajouter():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('admin_repas_ajouter.html', nom=session.get('nom'))
    
    conn = get_db()
    try:
        regimes = request.form.getlist('regimes')
        regimes_str = ','.join(regimes) if regimes else ''
        
        conn.execute('''INSERT INTO repas (nom_du_repas, type, description, calories, glucides, lipides, proteines, fibres, prix, disponible_cette_semaine, regimes_compatibles) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (request.form.get('nom'), request.form.get('type'), request.form.get('description'),
                      request.form.get('calories', 0), request.form.get('glucides', 0), request.form.get('lipides', 0),
                      request.form.get('proteines', 0), request.form.get('fibres', 0), request.form.get('prix'),
                      request.form.get('disponible', '1'), regimes_str))
        conn.commit()
        flash('Repas ajouté avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_repas'))

@app.route('/admin/repas/modifier/<int:repas_id>', methods=['GET', 'POST'])
def admin_repas_modifier(repas_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    
    if request.method == 'GET':
        repas = conn.execute('SELECT * FROM repas WHERE id_repas = ?', (repas_id,)).fetchone()
        conn.close()
        return render_template('admin_repas_modifier.html', repas=repas, nom=session.get('nom'))
    
    nom = request.form.get('nom')
    type_repas = request.form.get('type')
    description = request.form.get('description')
    calories = request.form.get('calories', 0)
    glucides = request.form.get('glucides', 0)
    lipides = request.form.get('lipides', 0)
    proteines = request.form.get('proteines', 0)
    fibres = request.form.get('fibres', 0)
    prix = request.form.get('prix')
    disponible = request.form.get('disponible', '1')
    regimes = request.form.getlist('regimes')
    regimes_str = ','.join(regimes) if regimes else ''
    
    try:
        conn.execute('''UPDATE repas SET nom_du_repas = ?, type = ?, description = ?, 
                       calories = ?, glucides = ?, lipides = ?, proteines = ?, fibres = ?,
                       prix = ?, disponible_cette_semaine = ?, regimes_compatibles = ?
                       WHERE id_repas = ?''',
                     (nom, type_repas, description, calories, glucides, lipides, proteines,
                      fibres, prix, disponible, regimes_str, repas_id))
        conn.commit()
        flash('Repas modifié avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_repas'))

@app.route('/admin/repas/supprimer/<int:repas_id>')
def admin_repas_supprimer(repas_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM contient WHERE id_repas = ?', (repas_id,))
        conn.execute('DELETE FROM concerne WHERE id_repas = ?', (repas_id,))
        conn.execute('DELETE FROM repas WHERE id_repas = ?', (repas_id,))
        conn.commit()
        flash('Repas supprimé avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_repas'))

@app.route('/admin/eleves')
def admin_eleves():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    eleves = conn.execute('''SELECT e.*, t.nom_de_tuteur, t.prenom_du_tuteur, t.numero_telephone_tuteur
        FROM eleves e LEFT JOIN responsable r ON e.id_eleve = r.id_eleve
        LEFT JOIN tuteur t ON r.id_tuteur = t.id_tuteur
        ORDER BY e.nom_d_eleve ASC, e.prenom_d_eleve ASC''').fetchall()
    conn.close()
    
    return render_template('admin_eleves.html', eleves=eleves, nom=session.get('nom'))

@app.route('/admin/eleves/recherche')
def admin_eleves_recherche():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return {'eleves': []}, 403
    
    query = request.args.get('q', '').strip().lower()
    allergie_filter = request.args.get('allergie', '').strip()
    regime_filter = request.args.get('regime', '').strip()
    
    conn = get_db()
    
    # Construction de la requête SQL avec filtres
    sql = '''SELECT e.*, t.nom_de_tuteur, t.prenom_du_tuteur, t.numero_telephone_tuteur
        FROM eleves e LEFT JOIN responsable r ON e.id_eleve = r.id_eleve
        LEFT JOIN tuteur t ON r.id_tuteur = t.id_tuteur
        WHERE 1=1'''
    
    params = []
    
    # Filtre par nom/prénom
    if query:
        sql += ' AND (LOWER(e.nom_d_eleve) LIKE ? OR LOWER(e.prenom_d_eleve) LIKE ?)'
        params.extend([f'{query}%', f'{query}%'])
    
    # Filtre par allergie
    if allergie_filter and allergie_filter != 'Toutes':
        if allergie_filter == 'Aucun':
            sql += ' AND (e.allergie IS NULL OR e.allergie = "")'
        else:
            sql += ' AND e.allergie LIKE ?'
            params.append(f'%{allergie_filter}%')
    
    # Filtre par régime
    if regime_filter and regime_filter != 'Tous':
        if regime_filter == 'Standard':
            sql += ' AND (e.regime_alimentaire IS NULL OR e.regime_alimentaire = "")'
        else:
            sql += ' AND e.regime_alimentaire = ?'
            params.append(regime_filter)
    
    sql += ' ORDER BY e.nom_d_eleve ASC, e.prenom_d_eleve ASC'
    
    eleves_rows = conn.execute(sql, params).fetchall()
    conn.close()
    
    eleves_list = [{
        'id_eleve': e['id_eleve'], 'nom_d_eleve': e['nom_d_eleve'], 'prenom_d_eleve': e['prenom_d_eleve'],
        'date_de_naissance': e['date_de_naissance'], 'class_d_etude': e['class_d_etude'],
        'allergie': e['allergie'], 'regime_alimentaire': e['regime_alimentaire'],
        'num_de_badge': e['num_de_badge'], 'nom_de_tuteur': e['nom_de_tuteur'],
        'prenom_du_tuteur': e['prenom_du_tuteur'], 'numero_telephone_tuteur': e['numero_telephone_tuteur']
    } for e in eleves_rows]
    
    return {'eleves': eleves_list}

@app.route('/admin/eleves/stats')
def admin_eleves_stats():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return {'allergies': [], 'regimes': []}, 403
    
    conn = get_db()
    
    # Statistiques des allergies
    allergies_data = conn.execute('''
        SELECT allergie, COUNT(*) as count 
        FROM eleves 
        WHERE allergie IS NOT NULL AND allergie != ""
        GROUP BY allergie 
        ORDER BY count DESC
    ''').fetchall()
    
    # Compter les élèves sans allergie
    sans_allergie = conn.execute('''
        SELECT COUNT(*) as count 
        FROM eleves 
        WHERE allergie IS NULL OR allergie = ""
    ''').fetchone()['count']
    
    allergies_list = [{'nom': 'Aucun', 'count': sans_allergie}]
    allergies_list.extend([{'nom': a['allergie'], 'count': a['count']} for a in allergies_data])
    
    # Statistiques des régimes
    regimes_data = conn.execute('''
        SELECT regime_alimentaire, COUNT(*) as count 
        FROM eleves 
        WHERE regime_alimentaire IS NOT NULL AND regime_alimentaire != ""
        GROUP BY regime_alimentaire 
        ORDER BY count DESC
    ''').fetchall()
    
    # Compter les élèves avec régime standard
    regime_standard = conn.execute('''
        SELECT COUNT(*) as count 
        FROM eleves 
        WHERE regime_alimentaire IS NULL OR regime_alimentaire = ""
    ''').fetchone()['count']
    
    regimes_list = [{'nom': 'Standard', 'count': regime_standard}]
    regimes_list.extend([{'nom': r['regime_alimentaire'], 'count': r['count']} for r in regimes_data])
    
    conn.close()
    
    return {'allergies': allergies_list, 'regimes': regimes_list}

@app.route('/admin/eleves/supprimer/<int:eleve_id>')
def admin_eleves_supprimer(eleve_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM concerne WHERE id_commande IN (SELECT id_commande FROM commande WHERE id_eleve = ?)', (eleve_id,))
        conn.execute('DELETE FROM commande WHERE id_eleve = ?', (eleve_id,))
        conn.execute('DELETE FROM suivi_nutritionnel WHERE id_eleve = ?', (eleve_id,))
        eleve = conn.execute('SELECT num_de_badge FROM eleves WHERE id_eleve = ?', (eleve_id,)).fetchone()
        if eleve:
            conn.execute('DELETE FROM users WHERE badge_num = ?', (eleve['num_de_badge'],))
        conn.execute('DELETE FROM responsable WHERE id_eleve = ?', (eleve_id,))
        conn.execute('DELETE FROM eleves WHERE id_eleve = ?', (eleve_id,))
        conn.commit()
        flash('Élève supprimé avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_eleves'))

@app.route('/admin/commandes')
def admin_commandes():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    commandes = conn.execute('''SELECT c.*, e.nom_d_eleve, e.prenom_d_eleve, e.num_de_badge
        FROM commande c LEFT JOIN eleves e ON c.id_eleve = e.id_eleve
        ORDER BY c.date_de_commande DESC''').fetchall()
    conn.close()
    
    return render_template('admin_commandes.html', commandes=commandes, nom=session.get('nom'))

@app.route('/admin/commandes/recherche')
def admin_commandes_recherche():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return {'commandes': []}, 403
    
    query = request.args.get('q', '').strip()
    
    if not query:
        return {'commandes': []}
    
    conn = get_db()
    
    if query.isdigit():
        commandes_rows = conn.execute('''SELECT c.*, e.nom_d_eleve, e.prenom_d_eleve, e.num_de_badge
            FROM commande c LEFT JOIN eleves e ON c.id_eleve = e.id_eleve
            WHERE c.id_commande = ?''', (int(query),)).fetchall()
    else:
        commandes_rows = conn.execute('''SELECT c.*, e.nom_d_eleve, e.prenom_d_eleve, e.num_de_badge
            FROM commande c LEFT JOIN eleves e ON c.id_eleve = e.id_eleve
            WHERE LOWER(e.nom_d_eleve) LIKE ? OR LOWER(e.prenom_d_eleve) LIKE ?''',
            (f'{query.lower()}%', f'{query.lower()}%')).fetchall()
    
    conn.close()
    
    commandes_list = [{
        'id_commande': c['id_commande'], 'date_de_commande': c['date_de_commande'],
        'status_de_commande': c['status_de_commande'], 'montant_du_commande': c['montant_du_commande'],
        'nom_d_eleve': c['nom_d_eleve'], 'prenom_d_eleve': c['prenom_d_eleve'],
        'num_de_badge': c['num_de_badge']
    } for c in commandes_rows]
    
    return {'commandes': commandes_list}



@app.route('/admin/stock')
def admin_stock():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    produits = conn.execute('SELECT * FROM produits ORDER BY nom_du_produit').fetchall()
    conn.close()
    
    return render_template('admin_stock.html', produits=produits, nom=session.get('nom'))

@app.route('/admin/produits/ajouter', methods=['GET', 'POST'])
def admin_produits_ajouter():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('admin_produits_ajouter.html', nom=session.get('nom'))
    
    nom = request.form.get('nom')
    categorie = request.form.get('categorie')
    unite = request.form.get('unite')
    prix = request.form.get('prix')
    seuil = request.form.get('seuil')
    stock = request.form.get('stock')
    
    conn = get_db()
    try:
        conn.execute('''INSERT INTO produits (nom_du_produit, categories_du_produit, unite_de_mesure, prix_unitaire, seuil_alert, stock) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (nom, categorie, unite, prix, seuil, stock))
        conn.commit()
        flash('Produit ajouté avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_stock'))

@app.route('/admin/produits/modifier/<int:produit_id>', methods=['POST'])
def admin_produits_modifier(produit_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    stock = request.form.get('stock')
    
    conn = get_db()
    try:
        conn.execute('UPDATE produits SET stock = ? WHERE id_produits = ?', (stock, produit_id))
        conn.commit()
        flash('Stock mis à jour avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_stock'))

@app.route('/admin/produits/supprimer/<int:produit_id>')
def admin_produits_supprimer(produit_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM produits WHERE id_produits = ?', (produit_id,))
        conn.commit()
        flash('Produit supprimé avec succès !', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_stock'))

@app.route('/admin/paiements')
def admin_paiements():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    commandes = conn.execute('''SELECT c.*, e.nom_d_eleve, e.prenom_d_eleve, e.num_de_badge
        FROM commande c LEFT JOIN eleves e ON c.id_eleve = e.id_eleve
        WHERE c.status_de_commande = 'Préparée'
        ORDER BY c.date_de_commande DESC''').fetchall()
    conn.close()
    
    return render_template('admin_paiements.html', commandes=commandes, nom=session.get('nom'))

@app.route('/admin/paiements/encaisser/<int:commande_id>', methods=['POST'])
def admin_paiements_encaisser(commande_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('index'))
    
    montant_recu = request.form.get('montant_recu', type=float)
    
    conn = get_db()
    try:
        commande = conn.execute('SELECT * FROM commande WHERE id_commande = ?', (commande_id,)).fetchone()
        montant_du = commande['montant_du_commande']
        
        if montant_recu < montant_du:
            flash('Montant insuffisant !', 'error')
            return redirect(url_for('admin_paiements'))
        
        monnaie = montant_recu - montant_du
        
        conn.execute('''INSERT INTO payments (date_de_paiement, montant_paye, mode_paiement, status_paiement) 
                        VALUES (?, ?, 'CASH', 'Payé')''', (datetime.now().strftime('%Y-%m-%d'), montant_du))
        
        payment_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        tuteur = conn.execute('SELECT id_eleve FROM eleves WHERE id_eleve = ?', (commande['id_eleve'],)).fetchone()
        if tuteur:
            conn.execute('INSERT INTO effectue_par (id_eleve, id_payments) VALUES (?, ?)', (tuteur['id_eleve'], payment_id))
        
        conn.execute('UPDATE commande SET status_de_commande = ? WHERE id_commande = ?', ('Validée', commande_id))
        
        conn.commit()
        
        if monnaie > 0:
            flash(f'Paiement encaissé ! Monnaie à rendre : {monnaie:.2f} DH', 'success')
        else:
            flash('Paiement encaissé avec succès !', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_paiements'))

if __name__ == '__main__':
    init_db()
    update_db_for_images()
    update_db_for_ingredients()
    update_db_for_employees()
    app.run(debug=True, port=5000)