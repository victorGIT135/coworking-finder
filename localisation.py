import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import os

# Charger le fichier nettoyé Excel
df = pd.read_excel("fichier_nettoye.xlsx")

# Nettoyer les colonnes adresse / code_postal / ville
df = df.dropna(subset=["adresse"])
df["adresse"] = df["adresse"].astype(str).str.strip()
df["code_postal"] = df["code_postal"].astype(str).str.extract(r'(\d{5})')[0]  # Garde les 5 chiffres uniquement
df["ville"] = df["ville"].astype(str).str.strip()

# Initialiser Nominatim avec un user-agent personnalisé
geolocator = Nominatim(user_agent="my_cowork_geocoder")

# Fonction robuste de récupération des coordonnées
def get_coordinates(adresse, retries=3):
    try:
        location = geolocator.geocode(adresse)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        if retries > 0:
            time.sleep(2)
            return get_coordinates(adresse, retries - 1)
        return None, None
    except Exception:
        return None, None

# Appliquer le géocodage ligne par ligne avec respect du quota
latitudes = []
longitudes = []

print("📍 Début du géocodage...")

for i, row in enumerate(df.itertuples(), start=1):
    adresse_complete = f"{row.adresse}, {row.code_postal} {row.ville}"
    lat, lon = get_coordinates(adresse_complete)
    latitudes.append(lat)
    longitudes.append(lon)
    print(f"{i}/{len(df)} - {adresse_complete} ➜ ({lat}, {lon})")
    time.sleep(1)  # Respect de la limite d'utilisation de Nominatim

# Ajouter les colonnes de coordonnées
df["latitude"] = latitudes
df["longitude"] = longitudes

# Sauvegarder le fichier final au format Excel
df.to_excel("../Data/fichier_geocode.xlsx", index=False)

print("✅ Géocodage terminé. Résultats enregistrés dans '../Data/fichier_geocode.xlsx'")
