import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import folium
from streamlit_folium import folium_static
from geopy.distance import geodesic
import random
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io
import math

# Configuration de la page
st.set_page_config(
    page_title="Gestion Livraisons Automobile",
    page_icon="🚚",
    layout="wide"
)

# Initialisation des données
def load_data():
    if 'magasins_source' not in st.session_state:
        try:
            with open('magasins_source.json', 'r') as f:
                st.session_state.magasins_source = json.load(f)
        except FileNotFoundError:
            st.session_state.magasins_source = {
                "maison": {
                    "nom": "Maison - Départ Automobile",
                    "position": [31.362120, -7.961128],
                    "type": "depart"
                },
                "depot_central": {
                    "nom": "Dépôt Central",
                    "position": [31.609110, -7.968425],
                    "prix_achat": {
                        "poulet": {
                            "ailes": 12, "pilons": 16, "cuisses": 20, 
                            "foies": 8, "blanc": 24, "gorges": 10,
                            "saucisse": 18, "escalopes": 22, "hauts de cuisse": 19
                        },
                        "dinde": {
                            "blanc": 28, "cuisses": 24, "ailes": 14,
                            "escalopes": 30, "rôti": 35
                        },
                        "boeuf": {
                            "steak": 45, "haché": 38, "côte": 50,
                            "rôti": 55, "brochettes": 42
                        },
                        "agneau": {
                            "côte": 60, "gigot": 65, "épaule": 58,
                            "brochettes": 52
                        }
                    },
                    "type": "magasin"
                }
            }
    
    if 'clients' not in st.session_state:
        try:
            with open('clients.json', 'r') as f:
                st.session_state.clients = json.load(f)
        except FileNotFoundError:
            st.session_state.clients = {}
    
    if 'commandes' not in st.session_state:
        try:
            with open('commandes.json', 'r') as f:
                st.session_state.commandes = json.load(f)
        except FileNotFoundError:
            st.session_state.commandes = []
    
    if 'livraisons' not in st.session_state:
        try:
            with open('livraisons.json', 'r') as f:
                st.session_state.livraisons = json.load(f)
        except FileNotFoundError:
            st.session_state.livraisons = []
    
    if 'tresorerie' not in st.session_state:
        try:
            with open('tresorerie.json', 'r') as f:
                st.session_state.tresorerie = json.load(f)
        except FileNotFoundError:
            st.session_state.tresorerie = []
    
    if 'panier' not in st.session_state:
        st.session_state.panier = []
    
    if 'selected_magasin' not in st.session_state:
        st.session_state.selected_magasin = "depot_central"

def gerer_produits_magasin(magasin_id):
    """Gestion dynamique des produits pour un magasin"""
    magasin = st.session_state.magasins_source[magasin_id]
    
    st.subheader("🔄 Gestion Dynamique des Produits")
    
    # Ajouter nouveau type de viande - SÉPARÉ du formulaire principal
    nouveau_type = st.text_input("Nouveau type de viande (ex: veau, canard)", key=f"new_type_{magasin_id}")
    if st.button("➕ Ajouter type", key=f"add_type_{magasin_id}"):
        if nouveau_type and nouveau_type not in magasin["prix_achat"]:
            magasin["prix_achat"][nouveau_type] = {}
            save_data()
            st.success(f"Type {nouveau_type} ajouté!")
            st.rerun()
    
    # Pour chaque type de viande
    for type_viande in list(magasin["prix_achat"].keys()):
        with st.expander(f"{type_viande.capitalize()}"):
            # Ajouter nouveau morceau - SÉPARÉ du formulaire principal
            col1, col2 = st.columns(2)
            with col1:
                nouveau_morceau = st.text_input("Nouveau morceau", key=f"new_morceau_{magasin_id}_{type_viande}")
            with col2:
                nouveau_prix = st.number_input("Prix d'achat (DH)", min_value=0.0, key=f"new_price_{magasin_id}_{type_viande}")
            
            if st.button("➕ Ajouter morceau", key=f"add_morceau_{magasin_id}_{type_viande}"):
                if nouveau_morceau and nouveau_morceau not in magasin["prix_achat"][type_viande]:
                    magasin["prix_achat"][type_viande][nouveau_morceau] = nouveau_prix
                    save_data()
                    st.success(f"Morceau {nouveau_morceau} ajouté!")
                    st.rerun()
            
            # Éditer les morceaux existants
            st.write("**Morceaux existants:**")
            for morceau in list(magasin["prix_achat"][type_viande].keys()):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.text(morceau)
                with col2:
                    nouveau_prix = st.number_input(
                        f"Prix {morceau}",
                        min_value=0.0,
                        value=float(magasin["prix_achat"][type_viande][morceau]),
                        key=f"prix_{magasin_id}_{type_viande}_{morceau}"
                    )
                    # Mettre à jour le prix immédiatement
                    if nouveau_prix != magasin["prix_achat"][type_viande][morceau]:
                        magasin["prix_achat"][type_viande][morceau] = nouveau_prix
                        save_data()
                with col3:
                    if st.button("❌", key=f"del_{magasin_id}_{type_viande}_{morceau}"):
                        del magasin["prix_achat"][type_viande][morceau]
                        save_data()
                        st.rerun()

def save_data():
    with open('magasins_source.json', 'w') as f:
        json.dump(st.session_state.magasins_source, f, indent=4)
    with open('clients.json', 'w') as f:
        json.dump(st.session_state.clients, f, indent=4)
    with open('commandes.json', 'w') as f:
        json.dump(st.session_state.commandes, f, indent=4)
    with open('livraisons.json', 'w') as f:
        json.dump(st.session_state.livraisons, f, indent=4)
    with open('tresorerie.json', 'w') as f:
        json.dump(st.session_state.tresorerie, f, indent=4)

# Fonctions utilitaires
def calculer_distance(pos1, pos2):
    return geodesic(pos1, pos2).km

def trouver_meilleur_itineraire(commandes_du_jour, magasin_id):
    positions = [st.session_state.magasins_source["maison"]["position"]]
    clients_ids = []
    
    # Ajouter le magasin source
    if magasin_id in st.session_state.magasins_source:
        positions.append(st.session_state.magasins_source[magasin_id]["position"])
    
    # Ajouter les clients
    for cmd in commandes_du_jour:
        if cmd['client_id'] in st.session_state.clients and cmd['client_id'] not in clients_ids:
            client = st.session_state.clients[cmd['client_id']]
            if 'position' in client:
                positions.append(tuple(client['position']))
                clients_ids.append(cmd['client_id'])
    
    # Retour à la maison
    positions.append(st.session_state.magasins_source["maison"]["position"])
    
    # Algorithme simple d'optimisation d'itinéraire (plus proche voisin)
    optimized_positions = [positions[0]]  # Départ maison
    remaining_positions = positions[1:]
    
    while remaining_positions:
        last_pos = optimized_positions[-1]
        closest_idx = 0
        closest_dist = float('inf')
        
        for i, pos in enumerate(remaining_positions):
            dist = calculer_distance(last_pos, pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_idx = i
        
        optimized_positions.append(remaining_positions[closest_idx])
        remaining_positions.pop(closest_idx)
    
    return optimized_positions

def creer_carte_itineraire(positions, magasin_nom):
    m = folium.Map(location=positions[0], zoom_start=12)
    
    # Ajouter la maison (départ)
    folium.Marker(
        positions[0],
        popup=st.session_state.magasins_source["maison"]["nom"],
        icon=folium.Icon(color='green', icon='home')
    ).add_to(m)
    
    # Ajouter le magasin source
    folium.Marker(
        positions[1],
        popup=magasin_nom,
        icon=folium.Icon(color='red', icon='warehouse')
    ).add_to(m)
    
    # Ajouter les points de livraison clients
    for i, pos in enumerate(positions[2:-1], 2):
        for client_id, client in st.session_state.clients.items():
            if 'position' in client and client['position'] == list(pos):
                folium.Marker(
                    pos,
                    popup=f"{client['nom']}",
                    icon=folium.Icon(color='blue', icon='user')
                ).add_to(m)
                break
    
    # Ajouter la ligne d'itinéraire
    folium.PolyLine(positions, color="blue", weight=2.5, opacity=1).add_to(m)
    
    # Calculer la distance totale
    distance_totale = 0
    for i in range(len(positions) - 1):
        distance_totale += calculer_distance(positions[i], positions[i + 1])
    
    folium.Marker(
        positions[0],
        popup=f"Distance totale: {distance_totale:.2f} km",
        icon=folium.DivIcon(html=f"""<div style="font-weight: bold; background: white; padding: 5px; border-radius: 5px; border: 2px solid blue;">
            {distance_totale:.2f} km
        </div>""")
    ).add_to(m)
    
    return m, distance_totale

def generer_bon_pdf(commande_id, client_id, details_commande, montant_paye, quantites_livrees):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # En-tête
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "BON DE LIVRAISON DÉTAILLÉ")
    c.drawString(100, 730, f"N°: {commande_id}")
    c.drawString(100, 710, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Informations client
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 680, "CLIENT:")
    c.setFont("Helvetica", 12)
    client = st.session_state.clients[client_id]
    c.drawString(100, 660, f"Nom: {client['nom']}")
    c.drawString(100, 640, f"Téléphone: {client['telephone']}")
    c.drawString(100, 620, f"Adresse: {client['adresse']}")
    
    # Détails commande
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 580, "DÉTAILS DE LA COMMANDE:")
    
    # En-têtes du tableau
    c.drawString(100, 560, "Produit")
    c.drawString(200, 560, "Cmd")
    c.drawString(250, 560, "Livré")
    c.drawString(320, 560, "Prix Unit.")
    c.drawString(400, 560, "Total Cmd")
    c.drawString(480, 560, "Total Livré")
    
    y_position = 540
    total_commande = 0
    total_livre = 0
    c.setFont("Helvetica", 10)
    
    for i, produit in enumerate(details_commande):
        qte_cmd = produit['quantite']
        qte_liv = quantites_livrees[i] if i < len(quantites_livrees) else 0
        prix_unit = produit['prix_vente']
        total_cmd = qte_cmd * prix_unit
        total_liv = qte_liv * prix_unit
        
        c.drawString(100, y_position, f"{produit['type_viande']} {produit['morceau']}")
        c.drawString(200, y_position, str(qte_cmd))
        c.drawString(250, y_position, str(qte_liv))
        c.drawString(320, y_position, f"{prix_unit} DH")
        c.drawString(400, y_position, f"{total_cmd} DH")
        c.drawString(480, y_position, f"{total_liv} DH")
        
        total_commande += total_cmd
        total_livre += total_liv
        y_position -= 20
    
    # Totaux
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y_position - 20, f"TOTAL COMMANDE: {total_commande} DH")
    c.drawString(350, y_position - 40, f"TOTAL LIVRÉ: {total_livre} DH")
    c.drawString(350, y_position - 60, f"MONTANT PAYÉ: {montant_paye} DH")
    c.drawString(350, y_position - 80, f"RESTE À PAYER: {total_livre - montant_paye} DH")
    
    # Signature
    c.drawString(100, y_position - 120, "Signature client: ________________________")
    c.drawString(100, y_position - 140, "Signature livreur: ________________________")
    
    c.save()
    buffer.seek(0)
    return buffer

def get_client_name(client_id):
    """Fonction sécurisée pour obtenir le nom d'un client"""
    if client_id in st.session_state.clients:
        return st.session_state.clients[client_id]['nom']
    else:
        return f"Client inconnu ({client_id})"

def modifier_commande(commande_index):
    """Modifier une commande existante"""
    commande = st.session_state.commandes[commande_index]
    
    with st.form(f"modifier_commande_{commande_index}"):
        st.subheader(f"Modifier la commande #{commande['id']}")
        
        # Sélection du client
        client_id = st.selectbox(
            "Client",
            options=list(st.session_state.clients.keys()),
            format_func=lambda x: f"{st.session_state.clients[x]['nom']} - {st.session_state.clients[x]['telephone']}",
            index=list(st.session_state.clients.keys()).index(commande['client_id']),
            key=f"mod_client_{commande_index}"
        )
        
        # Date de livraison
        date_livraison = st.date_input(
            "Date de livraison prévue",
            value=datetime.strptime(commande['date_livraison_prevue'], '%Y-%m-%d').date(),
            key=f"mod_date_{commande_index}"
        )
        
        # Modification des produits
        st.write("**Produits:**")
        nouveaux_produits = []
        for i, produit in enumerate(commande['produits']):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                type_viande = st.selectbox(
                    "Type viande",
                    options=["poulet", "dinde"],
                    index=0 if produit['type_viande'] == "poulet" else 1,
                    key=f"mod_type_{commande_index}_{i}"
                )
                morceau = st.selectbox(
                    "Morceau",
                    options=list(st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"][type_viande].keys()),
                    index=list(st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"][type_viande].keys()).index(produit['morceau']),
                    key=f"mod_morceau_{commande_index}_{i}"
                )
            with col2:
                quantite = st.number_input(
                    "Quantité",
                    min_value=1,
                    value=produit['quantite'],
                    key=f"mod_quantite_{commande_index}_{i}"
                )
            with col3:
                prix_vente = st.number_input(
                    "Prix vente (DH)",
                    min_value=0.0,
                    value=float(produit['prix_vente']),
                    key=f"mod_prix_{commande_index}_{i}"
                )
            with col4:
                if st.button("❌ Supprimer", key=f"del_prod_{commande_index}_{i}"):
                    continue  # Skip adding this product
            nouveaux_produits.append({
                "type_viande": type_viande,
                "morceau": morceau,
                "quantite": quantite,
                "prix_vente": prix_vente,
                "prix_achat": st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"][type_viande][morceau]
            })
        
        # Ajouter un nouveau produit
        if st.button("➕ Ajouter un produit", key=f"add_prod_{commande_index}"):
            nouveaux_produits.append({
                "type_viande": "poulet",
                "morceau": "ailes",
                "quantite": 1,
                "prix_vente": 15.0,
                "prix_achat": 12.0
            })
        
        # Notes
        notes = st.text_area(
            "Notes spéciales",
            value=commande.get('notes', ''),
            key=f"mod_notes_{commande_index}"
        )
        
        submitted = st.form_submit_button("💾 Enregistrer les modifications")
        
        if submitted:
            st.session_state.commandes[commande_index] = {
                "id": commande['id'],
                "client_id": client_id,
                "date_commande": commande['date_commande'],
                "date_livraison_prevue": date_livraison.strftime('%Y-%m-%d'),
                "produits": nouveaux_produits,
                "statut": commande['statut'],
                "notes": notes,
                "total_commande": sum(p['quantite'] * p['prix_vente'] for p in nouveaux_produits),
                "cout_achat": sum(p['quantite'] * p['prix_achat'] for p in nouveaux_produits)
            }
            save_data()
            st.success("Commande modifiée avec succès!")
            st.rerun()

# Chargement des données
load_data()

# Interface principale
st.title("🚚 Gestion des Livraisons Automobile - Système Complet")
st.sidebar.title("Navigation")

# Menu de navigation
page = st.sidebar.radio("Choisir une section:", 
                        ["Magasins Source", "Clients", "Commandes", "Itinéraire", "Livraisons", "Trésorerie", "Rapports", "Recherche"])

if page == "Magasins Source":
    st.header("🏭 Configuration des Magasins Source")
    
    tab1, tab2 = st.tabs(["Gérer les Magasins", "Sélectionner Magasin"])
    
    with tab1:
        # Liste des magasins
        st.subheader("Magasins disponibles")
        for magasin_id, magasin in st.session_state.magasins_source.items():
            if magasin_id != "maison":  # Ne pas modifier la maison
                with st.expander(f"{magasin['nom']} ({magasin_id})"):
                    # Formulaire principal pour les informations de base du magasin
                    with st.form(f"edit_magasin_{magasin_id}"):
                        nom = st.text_input("Nom", value=magasin["nom"], key=f"nom_{magasin_id}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            lat = st.number_input("Latitude", value=magasin["position"][0], format="%.6f", key=f"lat_{magasin_id}")
                        with col2:
                            lon = st.number_input("Longitude", value=magasin["position"][1], format="%.6f", key=f"lon_{magasin_id}")
                        
                        submitted = st.form_submit_button("💾 Enregistrer les informations de base")
                        if submitted:
                            st.session_state.magasins_source[magasin_id]["nom"] = nom
                            st.session_state.magasins_source[magasin_id]["position"] = [lat, lon]
                            save_data()
                            st.success("Informations de base modifiées!")
                    
                    # Gestion des produits - EN DEHORS du formulaire principal
                    if "prix_achat" in magasin:
                        gerer_produits_magasin(magasin_id)
                        
                        submitted = st.form_submit_button("💾 Enregistrer")
                        if submitted:
                            st.session_state.magasins_source[magasin_id]["nom"] = nom
                            st.session_state.magasins_source[magasin_id]["position"] = [lat, lon]
                            save_data()
                            st.success("Magasin modifié!")
        
        # Ajouter un nouveau magasin
        st.subheader("Ajouter un nouveau magasin")
        with st.form("nouveau_magasin"):
            magasin_id = st.text_input("ID du magasin (unique)")
            nom = st.text_input("Nom du magasin")
            
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitude", value=31.609110, format="%.6f")
            with col2:
                lon = st.number_input("Longitude", value=-7.968425, format="%.6f")
            
            submitted = st.form_submit_button("➕ Ajouter le magasin")
            
            if submitted:
                if magasin_id and magasin_id not in st.session_state.magasins_source:
                    st.session_state.magasins_source[magasin_id] = {
                        "nom": nom,
                        "position": [lat, lon],
                        "prix_achat": {
                            "poulet": {"ailes": 12, "pilons": 16, "cuisses": 20, "foies": 8, "blanc": 24},
                            "dinde": {"blanc": 28, "cuisses": 24, "ailes": 14}
                        },
                        "type": "magasin"
                    }
                    save_data()
                    st.success(f"Magasin {nom} ajouté!")
                else:
                    st.error("ID de magasin déjà existant ou invalide")
    
    with tab2:
        st.subheader("Sélectionner le magasin actuel")
        magasins_disponibles = [mid for mid, mag in st.session_state.magasins_source.items() if mag.get('type') == 'magasin']
        
        selected_mag = st.selectbox(
            "Magasin source pour les commandes",
            options=magasins_disponibles,
            format_func=lambda x: st.session_state.magasins_source[x]['nom'],
            index=magasins_disponibles.index(st.session_state.selected_magasin) if st.session_state.selected_magasin in magasins_disponibles else 0
        )
        
        if st.button("✅ Définir comme magasin actuel"):
            st.session_state.selected_magasin = selected_mag
            st.success(f"Magasin actuel: {st.session_state.magasins_source[selected_mag]['nom']}")

elif page == "Clients":
    st.header("📋 Gestion des Clients")
    
    tab1, tab2 = st.tabs(["Nouveau Client", "Liste des Clients"])
    
    with tab1:
        with st.form("nouveau_client"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom complet*")
                telephone = st.text_input("Téléphone*")
                email = st.text_input("Email")
            with col2:
                adresse = st.text_area("Adresse complète*")
                lat = st.number_input("Latitude*", value=31.609110, format="%.6f")
                lon = st.number_input("Longitude*", value=-7.968425, format="%.6f")
            
            submitted = st.form_submit_button("Enregistrer le client")
            
            if submitted:
                if nom and telephone and adresse:
                    client_id = f"CL{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.session_state.clients[client_id] = {
                        "nom": nom,
                        "telephone": telephone,
                        "email": email,
                        "adresse": adresse,
                        "position": [lat, lon],
                        "solde": 0.0,
                        "date_creation": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    save_data()
                    st.success(f"Client {nom} enregistré avec ID: {client_id}")
                else:
                    st.error("Veuillez remplir les champs obligatoires (*)")
    
    with tab2:
        if st.session_state.clients:
            clients_df = pd.DataFrame.from_dict(st.session_state.clients, orient='index')
            st.dataframe(clients_df[['nom', 'telephone', 'solde', 'adresse']], use_container_width=True)
            
            # Suppression de clients
            client_a_supprimer = st.selectbox(
                "Sélectionner un client à supprimer",
                options=list(st.session_state.clients.keys()),
                format_func=lambda x: f"{st.session_state.clients[x]['nom']} - {st.session_state.clients[x]['telephone']}",
                key="delete_client_select"
            )
            
            if st.button("🗑️ Supprimer le client", key="delete_client_btn"):
                if client_a_supprimer:
                    nom_client = st.session_state.clients[client_a_supprimer]['nom']
                    del st.session_state.clients[client_a_supprimer]
                    
                    # Supprimer aussi les commandes associées à ce client
                    st.session_state.commandes = [cmd for cmd in st.session_state.commandes if cmd['client_id'] != client_a_supprimer]
                    
                    save_data()
                    st.success(f"Client {nom_client} supprimé avec succès!")
                    st.rerun()
        else:
            st.info("Aucun client enregistré")

elif page == "Commandes":
    st.header("📦 Gestion des Commandes")
    
    tab1, tab2 = st.tabs(["Nouvelle Commande", "Commandes Existantes"])
    
    with tab1:
        date_commande = st.date_input("Date de livraison prévue", 
                                     min_value=datetime.now().date(),
                                     value=datetime.now().date() + timedelta(days=1))
        
        # Section pour ajouter des produits au panier
        st.subheader("Ajouter des produits au panier")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Sélection du type de viande
            types_disponibles = list(st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"].keys())
            type_viande = st.selectbox(
                "Type viande", 
                options=types_disponibles, 
                key="type_viande_select"
            )

        with col2:
            # Barre de recherche pour les morceaux
            if type_viande in st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"]:
                tous_morceaux = list(st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"][type_viande].keys())
                recherche_morceau = st.text_input("🔍 Rechercher un morceau", key="recherche_morceau")
                
                if recherche_morceau:
                    morceaux_filtres = [m for m in tous_morceaux if recherche_morceau.lower() in m.lower()]
                else:
                    morceaux_filtres = tous_morceaux
                
                if morceaux_filtres:
                    morceau = st.selectbox(
                        "Morceau", 
                        options=morceaux_filtres,
                        key="morceau_select"
                    )
                else:
                    st.warning("Aucun morceau trouvé")
                    morceau = None
            else:
                st.warning("Aucun morceau disponible")
                morceau = None

        with col3:
            quantite = st.number_input("Quantité", min_value=1, value=1, key="quantite_select")

        with col4:
            if morceau and type_viande in st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"]:
                prix_achat_base = st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"][type_viande][morceau]
                prix_vente = st.number_input(
                    "Prix vente (DH)", 
                    min_value=0.0, 
                    value=float(prix_achat_base * 1.2),  # 20% de marge par défaut
                    key="prix_select"
                )
            else:
                prix_vente = st.number_input(
                    "Prix vente (DH)", 
                    min_value=0.0, 
                    value=0.0,
                    key="prix_select",
                    disabled=True
                )
        
        if st.button("➕ Ajouter au panier", disabled=(morceau is None)):
            if morceau and type_viande in st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"]:
                nouveau_produit = {
                    "type_viande": type_viande,
                    "morceau": morceau,
                    "quantite": quantite,
                    "prix_vente": prix_vente,
                    "prix_achat": st.session_state.magasins_source[st.session_state.selected_magasin]["prix_achat"][type_viande][morceau]
                }
                st.session_state.panier.append(nouveau_produit)
                st.success("Produit ajouté au panier!")
            else:
                st.error("Veuillez sélectionner un morceau valide")
        
        # Affichage du panier
        if st.session_state.panier:
            st.subheader("🛒 Panier actuel")
            for i, prod in enumerate(st.session_state.panier):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{prod['quantite']} x {prod['type_viande']} {prod['morceau']}")
                with col2:
                    st.write(f"{prod['prix_vente']} DH/unité")
                with col3:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.panier.pop(i)
                        st.rerun()
        
        # Formulaire principal pour la commande
        with st.form("nouvelle_commande_form"):
            if not st.session_state.clients:
                st.warning("Aucun client enregistré. Veuillez d'abord ajouter des clients.")
            else:
                client_id = st.selectbox("Client*", 
                                        options=list(st.session_state.clients.keys()),
                                        format_func=lambda x: f"{st.session_state.clients[x]['nom']} - {st.session_state.clients[x]['telephone']}",
                                        key="client_select")
                
                notes = st.text_area("Notes spéciales", key="notes_area")
                
                submitted = st.form_submit_button("✅ Enregistrer la commande")
                
                if submitted:
                    if not client_id:
                        st.error("Veuillez sélectionner un client")
                    elif not st.session_state.panier:
                        st.error("Le panier est vide. Veuillez ajouter des produits.")
                    else:
                        commande_id = f"CMD{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        nouvelle_commande = {
                            "id": commande_id,
                            "client_id": client_id,
                            "date_commande": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "date_livraison_prevue": date_commande.strftime('%Y-%m-%d'),
                            "produits": st.session_state.panier.copy(),
                            "statut": "en_attente",
                            "notes": notes,
                            "total_commande": sum(p['quantite'] * p['prix_vente'] for p in st.session_state.panier),
                            "cout_achat": sum(p['quantite'] * p['prix_achat'] for p in st.session_state.panier),
                            "magasin_source": st.session_state.selected_magasin
                        }
                        
                        st.session_state.commandes.append(nouvelle_commande)
                        st.session_state.panier = []
                        save_data()
                        st.success(f"Commande #{commande_id} enregistrée pour {st.session_state.clients[client_id]['nom']}")
    
    with tab2:
        st.subheader("📋 Commandes existantes")
        if st.session_state.commandes:
            for i, cmd in enumerate(st.session_state.commandes):
                client_name = get_client_name(cmd['client_id'])
                with st.expander(f"Commande #{cmd['id']} - {client_name} - {cmd['statut']}"):
                    st.write(f"**Date livraison:** {cmd['date_livraison_prevue']}")
                    st.write(f"**Magasin:** {st.session_state.magasins_source[cmd.get('magasin_source', 'depot_central')]['nom']}")
                    st.write("**Produits:**")
                    for prod in cmd['produits']:
                        st.write(f"- {prod['quantite']} x {prod['morceau']} ({prod['prix_vente']} DH)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ Modifier", key=f"mod_cmd_{i}"):
                            modifier_commande(i)
                    with col2:
                        if st.button(f"🗑️ Supprimer", key=f"del_cmd_{i}"):
                            st.session_state.commandes.pop(i)
                            save_data()
                            st.success("Commande supprimée!")
                            st.rerun()
        else:
            st.info("Aucune commande enregistrée")

elif page == "Itinéraire":
    st.header("🗺️ Planification de l'Itinéraire")
    
    date_livraison = st.date_input("Date pour l'itinéraire", 
                                  value=datetime.now().date() + timedelta(days=1))
    
    # Sélection du magasin source
    magasins_disponibles = [mid for mid, mag in st.session_state.magasins_source.items() if mag.get('type') == 'magasin']
    
    if not magasins_disponibles:
        st.warning("Aucun magasin source configuré. Veuillez d'abord ajouter des magasins.")
    else:
        magasin_id = st.selectbox(
            "Magasin source",
            options=magasins_disponibles,
            format_func=lambda x: st.session_state.magasins_source[x]['nom'],
            key="itineraire_magasin"
        )
        
        commandes_du_jour = [cmd for cmd in st.session_state.commandes 
                            if cmd['date_livraison_prevue'] == date_livraison.strftime('%Y-%m-%d')
                            and cmd['statut'] in ['en_attente', 'partiellement_livre']
                            and cmd.get('magasin_source', 'depot_central') == magasin_id]
        
        if not commandes_du_jour:
            st.info("Aucune commande à livrer pour cette date depuis ce magasin")
        else:
            try:
                positions = trouver_meilleur_itineraire(commandes_du_jour, magasin_id)
                carte, distance_totale = creer_carte_itineraire(positions, st.session_state.magasins_source[magasin_id]['nom'])
                
                st.subheader("Circuit de livraison optimisé")
                st.metric("Distance totale estimée", f"{distance_totale:.2f} km")
                folium_static(carte, width=1000, height=600)
                
                st.subheader("Détail des livraisons")
                for i, cmd in enumerate(commandes_du_jour, 1):
                    client_name = get_client_name(cmd['client_id'])
                    produits_str = ", ".join([f"{p['quantite']} {p['morceau']}" for p in cmd['produits']])
                    st.write(f"{i}. {client_name} - {produits_str}")
                
                # Option pour marquer comme prêt pour livraison
                if st.button("✅ Préparer pour livraison"):
                    for cmd in commandes_du_jour:
                        cmd['statut'] = 'en_cours'
                    save_data()
                    st.success("Commandes marquées comme prêtes pour livraison!")
                    
            except Exception as e:
                st.error(f"Erreur lors de la génération de l'itinéraire: {str(e)}")
                st.info("Vérifiez que tous les clients ont des coordonnées GPS valides")

elif page == "Livraisons":
    st.header("📦 Livraisons du Jour")
    
    date_livraison = st.date_input("Date de livraison", value=datetime.now().date())
    
    commandes_a_livrer = [cmd for cmd in st.session_state.commandes 
                         if cmd['date_livraison_prevue'] == date_livraison.strftime('%Y-%m-%d')
                         and cmd['statut'] in ['en_cours', 'partiellement_livre']]
    
    if commandes_a_livrer:
        for commande in commandes_a_livrer:
            client_name = get_client_name(commande['client_id'])
            
            with st.expander(f"Commande #{commande['id']} - {client_name}"):
                st.write("**Produits commandés:**")
                for produit in commande['produits']:
                    st.write(f"- {produit['quantite']} x {produit['type_viande']} {produit['morceau']} ({produit['prix_vente']} DH/unité)")
                
                # Variable pour stocker le PDF généré
                pdf_buffer = None
                
                with st.form(f"livraison_form_{commande['id']}"):
                    st.write("**Détails livraison:**")
                    quantites_livrees = []
                    for i, produit in enumerate(commande['produits']):
                        qte_livree = st.number_input(
                            f"Quantité livrée - {produit['morceau']}",
                            min_value=0,
                            max_value=produit['quantite'],
                            value=produit.get('quantite_livree', 0),
                            key=f"liv_{commande['id']}_{i}"
                        )
                        quantites_livrees.append(qte_livree)
                    
                    montant_paye = st.number_input(
                        "Montant payé (DH)",
                        min_value=0.0,
                        max_value=float(commande['total_commande']),
                        value=0.0,
                        key=f"pay_{commande['id']}"
                    )
                    
                    submitted = st.form_submit_button("📦 Enregistrer la livraison")
                    
                    if submitted:
                        for i, produit in enumerate(commande['produits']):
                            produit['quantite_livree'] = quantites_livrees[i]
                        
                        commande['montant_paye'] = montant_paye
                        commande['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        total_livre = sum(quantites_livrees)
                        if total_livre == sum(p['quantite'] for p in commande['produits']):
                            commande['statut'] = 'livree'
                        elif total_livre > 0:
                            commande['statut'] = 'partiellement_livre'
                        else:
                            commande['statut'] = 'annulee'
                        
                        # Enregistrer dans l'historique des livraisons
                        livraison_id = f"LIV{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        st.session_state.livraisons.append({
                            "id": livraison_id,
                            "commande_id": commande['id'],
                            "client_id": commande['client_id'],
                            "date_livraison": commande['date_livraison_reelle'],
                            "quantites_livrees": quantites_livrees,
                            "montant_paye": montant_paye,
                            "statut": commande['statut']
                        })
                        
                        # Mettre à jour le solde client
                        total_a_payer = sum(q * p['prix_vente'] for q, p in zip(quantites_livrees, commande['produits']))
                        reste_a_payer = total_a_payer - montant_paye
                        st.session_state.clients[commande['client_id']]['solde'] += reste_a_payer
                        
                        # Enregistrer dans la trésorerie
                        if montant_paye > 0:
                            st.session_state.tresorerie.append({
                                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "type": "encaissement",
                                "montant": montant_paye,
                                "description": f"Paiement livraison {commande['id']}",
                                "client_id": commande['client_id'],
                                "commande_id": commande['id']
                            })
                        
                        save_data()
                        
                        # Générer le bon de livraison PDF
                        pdf_buffer = generer_bon_pdf(
                            commande['id'], 
                            commande['client_id'], 
                            commande['produits'], 
                            montant_paye, 
                            quantites_livrees
                        )
                        
                        st.success("Livraison enregistrée avec succès!")
                
                # Bouton de téléchargement en dehors du formulaire
                if pdf_buffer:
                    st.download_button(
                        label="📄 Télécharger le bon de livraison",
                        data=pdf_buffer,
                        file_name=f"bon_livraison_{commande['id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_{commande['id']}"
                    )
    else:
        st.info("Aucune livraison prévue pour aujourd'hui")


elif page == "Trésorerie":
    st.header("💰 Gestion de la Trésorerie")
    
    tab1, tab2, tab3 = st.tabs(["Solde Clients", "Mouvements", "Nouvelle Dépense"])
    
    with tab1:
        st.subheader("Soldes Clients")
        if st.session_state.clients:
            clients_solde = []
            for client_id, client in st.session_state.clients.items():
                clients_solde.append({
                    "Client": client['nom'],
                    "Téléphone": client['telephone'],
                    "Solde (DH)": client['solde'],
                    "Dernier contact": client.get('date_creation', 'N/A')
                })
            
            df_solde = pd.DataFrame(clients_solde)
            st.dataframe(df_solde, use_container_width=True)
            
            # Paiement de solde
            st.subheader("Enregistrer un paiement")
            with st.form("paiement_solde"):
                client_id = st.selectbox(
                    "Client",
                    options=list(st.session_state.clients.keys()),
                    format_func=lambda x: f"{st.session_state.clients[x]['nom']} - Solde: {st.session_state.clients[x]['solde']} DH"
                )
                montant = st.number_input("Montant payé (DH)", min_value=0.0, max_value=abs(st.session_state.clients[client_id]['solde']))
                
                submitted = st.form_submit_button("💵 Enregistrer le paiement")
                if submitted:
                    st.session_state.clients[client_id]['solde'] -= montant
                    st.session_state.tresorerie.append({
                        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "type": "encaissement",
                        "montant": montant,
                        "description": f"Règlement solde client",
                        "client_id": client_id
                    })
                    save_data()
                    st.success(f"Paiement de {montant} DH enregistré pour {st.session_state.clients[client_id]['nom']}")
        else:
            st.info("Aucun client enregistré")
    
    with tab2:
        st.subheader("Mouvements de trésorerie")
        if st.session_state.tresorerie:
            df_tresorerie = pd.DataFrame(st.session_state.tresorerie)
            df_tresorerie['date'] = pd.to_datetime(df_tresorerie['date'])
            df_tresorerie = df_tresorerie.sort_values('date', ascending=False)
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                date_debut = st.date_input("Date début", value=datetime.now().date() - timedelta(days=30))
            with col2:
                date_fin = st.date_input("Date fin", value=datetime.now().date())
            
            df_filtre = df_tresorerie[
                (df_tresorerie['date'].dt.date >= date_debut) & 
                (df_tresorerie['date'].dt.date <= date_fin)
            ]
            
            st.dataframe(df_filtre, use_container_width=True)
            
            # Statistiques
            total_entrees = df_filtre[df_filtre['type'] == 'encaissement']['montant'].sum()
            total_sorties = df_filtre[df_filtre['type'] == 'depense']['montant'].sum()
            solde_periode = total_entrees - total_sorties
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Entrées", f"{total_entrees:.2f} DH")
            col2.metric("💸 Sorties", f"{total_sorties:.2f} DH")
            col3.metric("📊 Solde période", f"{solde_periode:.2f} DH")
        else:
            st.info("Aucun mouvement de trésorerie")
    
    with tab3:
        st.subheader("Nouvelle Dépense")
        with st.form("nouvelle_depense"):
            description = st.text_input("Description de la dépense")
            montant = st.number_input("Montant (DH)", min_value=0.0)
            date_depense = st.date_input("Date", value=datetime.now().date())
            
            submitted = st.form_submit_button("💸 Enregistrer la dépense")
            if submitted:
                st.session_state.tresorerie.append({
                    "date": date_depense.strftime('%Y-%m-%d %H:%M:%S'),
                    "type": "depense",
                    "montant": montant,
                    "description": description
                })
                save_data()
                st.success("Dépense enregistrée!")

elif page == "Rapports":
    st.header("📊 Rapports et Statistiques")
    
    tab1, tab2, tab3 = st.tabs(["Ventes", "Performance", "Stocks"])
    
    with tab1:
        st.subheader("Rapport des Ventes")
        
        # Sélection de la période
        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Date début", value=datetime.now().date() - timedelta(days=30))
        with col2:
            date_fin = st.date_input("Date fin", value=datetime.now().date())
        
        # Filtrer les commandes livrées
        commandes_livrees = [cmd for cmd in st.session_state.commandes 
                           if cmd['statut'] in ['livree', 'partiellement_livre']
                           and datetime.strptime(cmd.get('date_livraison_reelle', cmd['date_commande']), '%Y-%m-%d %H:%M:%S').date() >= date_debut
                           and datetime.strptime(cmd.get('date_livraison_reelle', cmd['date_commande']), '%Y-%m-%d %H:%M:%S').date() <= date_fin]
        
        if commandes_livrees:
            # Chiffre d'affaires
            ca_total = sum(cmd.get('montant_paye', 0) for cmd in commandes_livrees)
            cout_total = sum(cmd['cout_achat'] for cmd in commandes_livrees)
            marge_total = ca_total - cout_total
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Chiffre d'affaires", f"{ca_total:.2f} DH")
            col2.metric("📦 Coût d'achat", f"{cout_total:.2f} DH")
            col3.metric("📊 Marge brute", f"{marge_total:.2f} DH")
            
            # Produits les plus vendus
            produits_ventes = {}
            for cmd in commandes_livrees:
                for prod in cmd['produits']:
                    key = f"{prod['type_viande']} {prod['morceau']}"
                    if key not in produits_ventes:
                        produits_ventes[key] = 0
                    produits_ventes[key] += prod.get('quantite_livree', prod['quantite'])
            
            df_produits = pd.DataFrame(list(produits_ventes.items()), columns=['Produit', 'Quantité'])
            df_produits = df_produits.sort_values('Quantité', ascending=False)
            
            st.subheader("📈 Produits les plus vendus")
            st.bar_chart(df_produits.set_index('Produit'))
            
            # Clients les plus actifs
            clients_activite = {}
            for cmd in commandes_livrees:
                client_id = cmd['client_id']
                if client_id not in clients_activite:
                    clients_activite[client_id] = 0
                clients_activite[client_id] += cmd.get('montant_paye', 0)
            
            df_clients = pd.DataFrame([
                {
                    'Client': st.session_state.clients[client_id]['nom'],
                    'CA Total': montant
                }
                for client_id, montant in clients_activite.items()
            ])
            df_clients = df_clients.sort_values('CA Total', ascending=False)
            
            st.subheader("🏆 Top Clients")
            st.dataframe(df_clients, use_container_width=True)
            
        else:
            st.info("Aucune vente sur la période sélectionnée")
    
    with tab2:
        st.subheader("Performance de Livraison")
        
        # Statistiques de livraison
        total_commandes = len(st.session_state.commandes)
        livrees_complet = len([cmd for cmd in st.session_state.commandes if cmd['statut'] == 'livree'])
        livrees_partiel = len([cmd for cmd in st.session_state.commandes if cmd['statut'] == 'partiellement_livre'])
        en_attente = len([cmd for cmd in st.session_state.commandes if cmd['statut'] == 'en_attente'])
        annulees = len([cmd for cmd in st.session_state.commandes if cmd['statut'] == 'annulee'])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Total Commandes", total_commandes)
        col2.metric("✅ Livrées complètement", livrees_complet)
        col3.metric("⚠️ Partiellement livrées", livrees_partiel)
        col4.metric("⏳ En attente", en_attente)
        
        # Taux de satisfaction
        if total_commandes > 0:
            taux_livraison = ((livrees_complet + livrees_partiel) / total_commandes) * 100
            st.metric("📊 Taux de livraison", f"{taux_livraison:.1f}%")
    
    with tab3:
        st.subheader("Gestion des Stocks (Simulation)")
        
        # Simulation de stock basée sur les commandes à venir
        commandes_futures = [cmd for cmd in st.session_state.commandes 
                           if cmd['statut'] in ['en_attente', 'en_cours']
                           and datetime.strptime(cmd['date_livraison_prevue'], '%Y-%m-%d').date() >= datetime.now().date()]
        
        if commandes_futures:
            besoins_stock = {}
            for cmd in commandes_futures:
                for prod in cmd['produits']:
                    key = f"{prod['type_viande']} {prod['morceau']}"
                    if key not in besoins_stock:
                        besoins_stock[key] = 0
                    besoins_stock[key] += prod['quantite']
            
            df_besoins = pd.DataFrame(list(besoins_stock.items()), columns=['Produit', 'Quantité nécessaire'])
            df_besoins = df_besoins.sort_values('Quantité nécessaire', ascending=False)
            
            st.write("**📋 Besoins en stock pour les prochains jours:**")
            st.dataframe(df_besoins, use_container_width=True)
        else:
            st.info("Aucune commande nécessitant du stock")

elif page == "Recherche":
    st.header("🔍 Recherche Avancée")
    
    search_term = st.text_input("Rechercher (nom client, téléphone, produit...)")
    
    if search_term:
        # Recherche dans les clients
        clients_trouves = []
        for client_id, client in st.session_state.clients.items():
            if (search_term.lower() in client['nom'].lower() or 
                search_term in client['telephone'] or
                search_term.lower() in client['adresse'].lower()):
                clients_trouves.append(client_id)
        
        # Recherche dans les commandes
        commandes_trouvees = []
        for cmd in st.session_state.commandes:
            # Par produit
            for prod in cmd['produits']:
                if search_term.lower() in prod['morceau'].lower():
                    commandes_trouvees.append(cmd)
                    break
            
            # Par client
            if cmd['client_id'] in clients_trouves and cmd not in commandes_trouvees:
                commandes_trouvees.append(cmd)
        
        # Affichage des résultats
        if clients_trouves or commandes_trouvees:
            if clients_trouves:
                st.subheader("👥 Clients trouvés")
                for client_id in clients_trouves:
                    client = st.session_state.clients[client_id]
                    st.write(f"**{client['nom']}** - {client['telephone']} - Solde: {client['solde']} DH")
                    st.write(f"Adresse: {client['adresse']}")
                    st.write("---")
            
            if commandes_trouvees:
                st.subheader("📦 Commandes trouvées")
                for cmd in commandes_trouvees:
                    client_name = get_client_name(cmd['client_id'])
                    with st.expander(f"Commande #{cmd['id']} - {client_name} - {cmd['statut']}"):
                        st.write(f"**Date:** {cmd['date_livraison_prevue']}")
                        st.write(f"**Total:** {cmd['total_commande']} DH")
                        st.write("**Produits:**")
                        for prod in cmd['produits']:
                            st.write(f"- {prod['quantite']} x {prod['morceau']} ({prod['prix_vente']} DH)")
        else:
            st.info("Aucun résultat trouvé")

# Pied de page
st.sidebar.markdown("---")
st.sidebar.info("**Système de gestion des livraisons** v2.0\n\nDéveloppé pour optimiser les livraisons automobile")

# Sauvegarde automatique périodique
if 'last_save' not in st.session_state:
    st.session_state.last_save = datetime.now()

if (datetime.now() - st.session_state.last_save).seconds > 300:  # Sauvegarde toutes les 5 minutes
    save_data()
    st.session_state.last_save = datetime.now()