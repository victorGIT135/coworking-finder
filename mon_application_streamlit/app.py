import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import numpy as np
import math

# Charger le fichier Excel
fichier = "Data/fichier_geocode.xlsx"
df = pd.read_excel(fichier)

# Nettoyage et transformation
df = df.dropna(subset=["latitude", "longitude"])
df["code_postal"] = df["code_postal"].astype(str).str.extract(r"(\d{5})")[0]

# --- Mise en page ---
st.set_page_config(page_title="Coworking Finder", layout="wide")

# Logo et titre
with st.sidebar:
    st.image("Data/logo.png", width=120)
    st.markdown("# Coworking Finder")
    menu = st.radio("Navigation", ["Carte & statistiques", "Indicateurs", "Calculer un itinéraire"], index=0)
    arrondissements = sorted(df["code_postal"].dropna().unique().tolist())
    arrondissement_selectionne = st.selectbox("Filtrer par arrondissement :", ["Tous"] + arrondissements)

# --- Filtrage global ---
df_filtered = df[df["code_postal"] == arrondissement_selectionne] if arrondissement_selectionne != "Tous" else df
center_lat = df_filtered["latitude"].mean()
center_lon = df_filtered["longitude"].mean()

# --- Style CSS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
        }
        .stMetricValue {
            font-size: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# === Section Carte & Statistiques ===
if menu == "Carte & statistiques":
    st.title("\U0001F5FA️ Carte des espaces de coworking")
    st.markdown("### Statistiques globales")

    col1, col2, col3 = st.columns(3)
    col1.metric("Espaces affichés", len(df_filtered))

    if not df_filtered.empty:
        cp_top = df_filtered["code_postal"].mode()[0]
        nb_cp = df_filtered["code_postal"].value_counts()[cp_top]
        col2.metric("Code postal dominant", cp_top, f"{nb_cp} espaces")

        ville_top = df_filtered["ville"].mode()[0]
        nb_ville = df_filtered["ville"].value_counts()[ville_top]
        col3.metric("Ville dominante", ville_top, f"{nb_ville} espaces")

    noms_dispo = sorted(df_filtered["nom_espace"].dropna().unique().tolist())
    nom_selectionne = st.selectbox("\U0001F50D Rechercher un espace :", [""] + noms_dispo)

    # Carte Folium
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    marker_cluster = MarkerCluster().add_to(m)

    for idx, row in df_filtered.iterrows():
        popup_info = f"""
        <b>{row['nom_espace']}</b><br>
        {row['adresse']}<br>
        {row['ville']}
        """
        icon_color = "red" if nom_selectionne and row["nom_espace"] == nom_selectionne else "blue"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup_info,
            icon=folium.Icon(color=icon_color)
        ).add_to(marker_cluster)

    if nom_selectionne:
        coworking = df[df["nom_espace"] == nom_selectionne].iloc[0]
        st.subheader(f"\U0001F4CB Informations sur {coworking['nom_espace']}")
        st.markdown(f"""
        - **Adresse :** {coworking['adresse']}, {coworking['code_postal']} {coworking['ville']}
        - **Téléphone :** {coworking['telephone']}
        - **Site web :** [{coworking['site_web']}]({coworking['site_web']})
        - **URL :** [{coworking['url']}]({coworking['url']})
        """)
        maps_url = f"https://www.google.com/maps/search/?api=1&query={coworking['latitude']},{coworking['longitude']}"
        st.markdown(f"[\U0001F4CD Voir sur Google Maps]({maps_url})")

    HeatMap(df_filtered[["latitude", "longitude"]].values.tolist()).add_to(m)
    st_folium(m, width=900, height=500)

# === Section Indicateurs ===
elif menu == "Indicateurs":
    st.title("\U0001F4CA Indicateurs complémentaires")

    # Graphique 1 : Position centre
    st.subheader("📍 Espace le plus central")
    centre_lat = df_filtered["latitude"].mean()
    centre_lon = df_filtered["longitude"].mean()
    df_filtered["distance_centre"] = ((df_filtered["latitude"] - centre_lat)**2 + (df_filtered["longitude"] - centre_lon)**2)
    espace_central = df_filtered.sort_values("distance_centre").iloc[0]["nom_espace"]
    st.success(f"Espace le plus proche du centre : {espace_central}")
    maps_url = f"https://www.google.com/maps/search/?api=1&query={centre_lat},{centre_lon}"
    st.markdown(f"[Voir sur Google Maps]({maps_url})")
    df_filtered.drop(columns="distance_centre", inplace=True)

    # Graphique 2 : Répartition par type de téléphone
    st.subheader("📞 Répartition par type de numéro de téléphone")
    tel_series = df_filtered["telephone"].dropna().astype(str)
    nb_mobiles = tel_series.str.startswith("06") | tel_series.str.startswith("07")
    counts = pd.Series({"Mobile (06/07)": nb_mobiles.sum(), "Fixe (autres)": (~nb_mobiles).sum()})

    fig3, ax3 = plt.subplots()
    ax3.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90, colors=["#66c2a5", "#fc8d62"])
    ax3.axis("equal")
    st.pyplot(fig3)

    # Histogramme final
    st.divider()
    st.subheader("\U0001F4CA Répartition des coworkings par code postal")
    repartition_cp = df_filtered["code_postal"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    repartition_cp.sort_index().plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_xlabel("Code postal")
    ax.set_ylabel("Nombre d'espaces")
    ax.set_title("Nombre d'espaces de coworking par code postal")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# === Section Itinéraire ===
elif menu == "Calculer un itinéraire":
    st.title("🧭 Calculer un itinéraire entre deux espaces")
    espaces = sorted(df["nom_espace"].dropna().unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        depart = st.selectbox("Point de départ", espaces, key="depart")

    if depart:
        loc_depart = df[df["nom_espace"] == depart].iloc[0]
        df["distance_from_depart"] = ((df["latitude"] - loc_depart["latitude"])**2 + (df["longitude"] - loc_depart["longitude"])**2)
        proches = df[df["nom_espace"] != depart].sort_values("distance_from_depart").head(5)
        suggestions = proches["nom_espace"].tolist()
    else:
        suggestions = espaces

    with col2:
        arrivee = st.selectbox("Point d'arrivée (plus proches en priorité)", suggestions, key="arrivee")

    if depart and arrivee and depart != arrivee:
        loc_arrivee = df[df["nom_espace"] == arrivee].iloc[0]
        url_gmaps = f"https://www.google.com/maps/dir/?api=1&origin={loc_depart['latitude']},{loc_depart['longitude']}&destination={loc_arrivee['latitude']},{loc_arrivee['longitude']}"
        st.markdown(f"[🚀 Voir l'itinéraire sur Google Maps]({url_gmaps})")

        # Estimation distance et durée à pied (approximations)
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance_km = haversine(loc_depart["latitude"], loc_depart["longitude"], loc_arrivee["latitude"], loc_arrivee["longitude"])
        time_min = round(distance_km / 5 * 60)

        st.info(f"Distance estimée : **{distance_km:.2f} km**")
        st.info(f"Temps estimé à pied : **{time_min} minutes**")
    elif depart == arrivee:
        st.warning("Le point de départ et d'arrivée doivent être différents.")