import pandas as pd
import re
import unicodedata

def nettoyage_excel(fichier):
    df = pd.read_excel(fichier)
    df = df.fillna("NULL").astype(str)  # Remplace les valeurs manquantes et convertit en str

    def nettoyer_texte(texte):
        texte = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii')  # Enlève accents
        texte = texte.strip()
        texte = re.sub(r'\s+', ' ', texte)
        return texte

    # Nettoyage texte de toutes les colonnes
    for col in df.columns:
        df[col] = df[col].apply(nettoyer_texte)

    # Nettoyage spécifique pour les numéros de téléphone
    def nettoyer_numeros_telephone(texte):
        texte = texte.split(',')[0].strip()
        pattern = r'\b(0[1-9](?:[ .-]?\d{2}){4}|0[1-9]\d{8})\b'
        match = re.search(pattern, texte)
        if match:
            numero = re.sub(r'\D', '', match.group(0))
            numero = ' '.join(numero[i:i+2] for i in range(0, len(numero), 2))
            return numero.strip()
        return "NULL"

    # Applique le nettoyage si la colonne "telephone" existe
    if "telephone" in df.columns:
        df["telephone"] = df["telephone"].apply(nettoyer_numeros_telephone)
    else:
        print("Colonne 'telephone' non trouvée dans le fichier.")

    # Sauvegarde du résultat
    df.to_excel("fichier_nettoye.xlsx", index=False)
    print("Fichier nettoyé et sauvegardé dans 'fichier_nettoye.xlsx'")

# Appel de la fonction
nettoyage_excel("informations_coworking_idf.xlsx")
