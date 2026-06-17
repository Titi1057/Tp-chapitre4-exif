# **************************************************************************** 
# # Nom ......... : mon_app.py  
# Rôle ........ : "" Interface collaborative permettant l'insertion d'une image,  
#                 l'extraction exhaustive de métadonnées EXIF, l'édition de tags  
#                 (Artiste, GPS) via un formulaire dynamique et la visualisation  
#                 cartographique interactive (Localisation & POI)."" 
# 
# Version ..... : V3.0  Version finale optimisée pour le rendu  
# Environnement : Windows - VS Code - Python 3.12+  
# Librairies .. : Streamlit, Pillow (PIL), Piexif, Folium, Streamlit-Folium, base64 
# URL          : https://github.com/Titi1057/Tp-chapitre4-exif 
# ****************************************************************************

import streamlit as st           # Framework pour l'interface web 
from PIL import Image, ExifTags  # PIL pour l'image, ExifTags pour traduire les ID de métadonnées 
import piexif                    # Librairie de manipulation binaire des données EXIF 
import folium                    # Moteur de génération de cartes interactives 
from streamlit_folium import st_folium # Composant d'affichage des cartes dans Streamlit 
import base64  # Pour convertir les données binaires de nos photographies 
               # en une suite de caractères ASCII directement interprétables par le navigateur web. 

# Fonction pour convertir l'image en texte (Base64) 
def get_base64_of_bin_file(bin_file): 
    with open(bin_file, 'rb') as f: 
        data = f.read() 
    return base64.b64encode(data).decode() 

# --- CONFIGURATION DE L'INTERFACE --- 
st.title("Éditeur de Métadonnées EXIF & Cartographie") 

# Widget de téléchargement : permet de charger l'image test_gps.jpg sans erreur de chemin 
uploaded_file = st.file_uploader("Choisissez une photo dans votre répertoire", type=["jpg", "jpeg"]) 

# Vérification : le code ne s'exécute que si un fichier est présent 
if uploaded_file: 
    # Ouverture du flux binaire de l'image via Pillow 
    image = Image.open(uploaded_file) 
    # Affichage de l'image (responsive avec use_container_width) 
    st.image(image, caption="Photographie chargée", use_container_width=True) 

    # --- ÉTAPE 1 : EXTRACTION MAXIMALE DES DONNÉES (VERSION SÉCURISÉE) ---  
    metadata_tree = {}          # Initialisation d'un dictionnaire "propre" vide 
      
    try: 
        exif_data = image._getexif() # Tentative d'extraction du dictionnaire brut 
          
        # LE FILET DE SÉCURITÉ : On vérifie si exif_data contient des données (n'est pas None) 
        if exif_data is not None and len(exif_data) > 0: 
            st.subheader("📊 Métadonnées réelles détectées (Exif-Org)") 
            # La boucle s'exécute uniquement si l'objet possède la méthode .items() 
            for tag_id, value in exif_data.items(): 
                tag_name = ExifTags.TAGS.get(tag_id, tag_id) 
                metadata_tree[tag_name] = value 
              
            # Affichage structuré au format JSON 
            st.json(metadata_tree)   
        else: 
            # AJOUT PROPRE : On affiche un JSON vide pour montrer que le dictionnaire est initialisé
            st.subheader("📊 Métadonnées réelles détectées (Exif-Org)")
            st.json({"Statut": "Aucune métadonnée d'origine trouvée dans ce fichier"})
            
            # FONCTION DE SECOURS 1 : Si l'image n'a pas d'EXIF, on affiche un avertissement propre 
            st.warning("⚠️ Cette image ne contient aucune métadonnée EXIF. Des valeurs par défaut ont été appliquées dans le formulaire ci-dessous.") 
              
    except Exception as e: 
        # FONCTION DE SECOURS 2 : Si un autre problème imprévu survient, on capture l'erreur sans crasher 
        st.error(f"❌ Une erreur critique a été interceptée lors de la lecture : {e}")

    # --- ÉTAPE 2 : FORMULAIRE D'ÉDITION COMPLET (Consigne 2) ---  
    st.header("📝 Modifier les métadonnées") 
    # Utilisation de st.form pour regrouper les entrées et éviter les rechargements inutiles 
    with st.form("exif_form"): 
        # Récupération des valeurs existantes ou définition de valeurs par défaut 
        artist_val = str(metadata_tree.get("Artist", "Anonyme")) 
        desc_val = str(metadata_tree.get("ImageDescription", "Ma description")) 
          
        # Champs de saisie de texte pour l'auteur et la description 
        artist = st.text_input("Artiste / Auteur", value=artist_val) 
        description = st.text_area("Description", value=desc_val) 
          
        st.subheader("📍 Coordonnées GPS (Position actuelle)") 
        # Champs numériques pour la saisie précise des coordonnées GPS 
        lat = st.number_input("Latitude", value=48.8566, format="%.6f") 
        lon = st.number_input("Longitude", value=2.3522, format="%.6f") 
          
        # Bouton d'envoi du formulaire 
        submit = st.form_submit_button("Mettre à jour l'image") 

    # Action déclenchée après clic sur le bouton 
    if submit: 
        # Initialisation d'une structure EXIF standard (0th, Exif, GPS, 1st) 
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None} 
        # Si l'image a déjà des données, on les charge pour ne pas les perdre 
        if 'exif' in image.info: 
            exif_dict = piexif.load(image.info['exif']) 
          
        # Encodage en UTF-8 pour injecter les nouvelles chaînes de caractères 
        exif_dict["0th"][piexif.ImageIFD.Artist] = artist.encode("utf-8") 
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = description.encode("utf-8") 
          
        # Conversion du dictionnaire en binaire (Dump) et sauvegarde physique 
        exif_bytes = piexif.dump(exif_dict) 
        image.save("updated_image.jpg", exif=exif_bytes) 
        st.success("✅ Fichier 'updated_image.jpg' généré avec succès !") 

    # --- ÉTAPE 3 : CARTOGRAPHIE (Consignes 3 & 4) ---  
    # Division de l'interface en deux colonnes pour comparer les cartes 
    col1, col2 = st.columns(2) 
      
    with col1: 
        st.subheader("📍 Position de l'image") 
        # Création de la carte centrée sur les coordonnées saisies 
        m1 = folium.Map(location=[lat, lon], zoom_start=12) 
        # Ajout d'un marqueur rouge pour l'emplacement de la photo 
        folium.Marker([lat, lon], popup="Photo ici", icon=folium.Icon(color='red')).add_to(m1) 
        # Affichage via le pont st_folium 
        st_folium(m1, width=350, height=300, key="map1") 

    with col2: 
        st.subheader("✈️ Itinéraire de rêve (POI)") 
        # Carte mondiale pour l'itinéraire de voyage 
        m2 = folium.Map(location=[20, 0], zoom_start=1) 
        # Liste de coordonnées représentant les Points d'Intérêt (POI) 
        points = [[48.8566, 2.3522], [35.6895, 139.6917], [-22.9068, -43.1729]] 
        # Dessin de la ligne bleue reliant les points (PolyLine) 
        folium.PolyLine(points, color="blue", weight=3).add_to(m2) 
        # Boucle pour ajouter un marqueur sur chaque destination 
        for p in points: 
            folium.Marker(p).add_to(m2) 
        # Affichage de la seconde carte avec une clé unique (key) pour éviter les conflits 
        st_folium(m2, width=350, height=300, key="map2")