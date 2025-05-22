from pyquery import PyQuery as pq
import pandas as pd
import openpyxl
import requests
import re

# liste des URL récupérées avec l'UL : Ile de France
liste_IDF = [75, 78, 92, 95, 77, 94]

# Requête pour récupérer le contenu de la page + charger le HTML en contenu PyQuery
response = requests.get("https://www.leportagesalarial.com/coworking/")
contenu_html = pq(response.text)

# Liste des URL contenant un élément de la liste_IDF
url_IDF = []
liens = contenu_html('a')
for lien in liens:
    href = pq(lien).attr('href')
    if href:
        for code in liste_IDF:
            if f'-{code}' in href:
                url_IDF.append(href)
                break

# Fonction pour requêter tous les URL de la liste
def requeter_url_IDF(urls):
    responses = []
    for url in urls:
        try:
            response = requests.get(url)
            responses.append((url, response.text))
            print(f"Contenu récupéré pour l'URL {url}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête vers {url} : {e}")
    return responses

responses = requeter_url_IDF(url_IDF)

# Fonction pour extraire les informations
def extraire_informations(url, page_html):
    doc = pq(page_html)

    info = {
        "nom_espace": None,
        "adresse": None,
        "code_postal": None,
        "ville": None,
        "telephone": None,
        "site_web": None,
    }

    nom_espace = doc('h1, h2').text().strip()
    if nom_espace:
        info["nom_espace"] = nom_espace

    adresse_li = doc('ul li:contains("Adresse :")').text()
    if adresse_li:
        adresse = adresse_li.replace("Adresse : ", "").strip()
        match = re.match(r"([0-9]+\s[\w\s]+),\s([0-9]{5})\s([a-zA-Z\s]+)", adresse)
        if match:
            info["adresse"] = match.group(1).strip()
            info["code_postal"] = match.group(2).strip()
            info["ville"] = match.group(3).strip()

    telephone_li = doc('ul li:contains("Téléphone :")').text()
    if telephone_li:
        info["telephone"] = telephone_li.replace("Téléphone : ", "").strip()

    site_li = doc('ul li:contains("Site :") a').attr('href')
    if site_li:
        info["site_web"] = site_li.strip()

    return info

# Extraire les informations
infos_extraites = []
for url, content in responses:
    if content:
        print(f"Extraction des informations pour l'URL : {url}")
        informations = extraire_informations(url, content)
        informations["url"] = url
        infos_extraites.append(informations)

# Export Excel
df = pd.DataFrame(infos_extraites)
df.to_excel("../Data/informations_coworking_idf.xlsx", index=False)
print("Données exportées vers informations_coworking_idf.xlsx")
