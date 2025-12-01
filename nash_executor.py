import os
import sys
import json
import requests
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    # Si python-dotenv n'est pas installé, on continue sans, on utilisera les variables système
    load_dotenv = None


def load_env():
    """
    Charge les variables d'environnement depuis un fichier .env s'il existe.
    """
    if load_dotenv is not None:
        load_dotenv()

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        print("❌ ERREUR : NOTION_TOKEN ou NOTION_DATABASE_ID manquants.")
        print("  → Crée un fichier .env avec :")
        print("      NOTION_TOKEN=ton_token_secret_notion")
        print("      NOTION_DATABASE_ID=ton_id_de_base")
        sys.exit(1)

    return notion_token, database_id


def build_properties(
    title: str,
    source: Optional[str],
    type_detected: Optional[str],
    categorie: Optional[str],
    statut: Optional[str],
    contenu: Optional[str],
):
    """
    Construit l'objet 'properties' pour l'API Notion en fonction de ta base Nash Inbox.

    Hypothèses sur ta base :
      - Colonne titre :        'Source' (type 'title')
      - Colonne 'Type détecté' : Select
      - Colonne 'Catégorie suggérée' : Select
      - Colonne 'Statut' : Select
      - Colonne 'Contenu' : Texte long / Rich text
    """
    props = {}

    # Titre = Source (titre Notion)
    # On met le "title" dans Source, et on garde éventuellement "source" séparé si tu veux plus tard
    props["Source"] = {
        "title": [
            {
                "text": {
                    "content": title or (source or "Sans titre")
                }
            }
        ]
    }

    # Type détecté (Select)
    if type_detected:
        props["Type détecté"] = {
            "select": {"name": type_detected}
        }

    # Catégorie suggérée (Select)
    if categorie:
        props["Catégorie suggérée"] = {
            "select": {"name": categorie}
        }

    # Statut (Select)
    if statut:
        props["Statut"] = {
            "select": {"name": statut}
        }

    # Contenu (Rich text)
    if contenu:
        props["Contenu"] = {
            "rich_text": [
                {
                    "text": {
                        "content": contenu
                    }
                }
            ]
        }

    return props


def create_nash_page(
    title: str,
    source: Optional[str] = None,
    type_detected: Optional[str] = None,
    categorie: Optional[str] = None,
    statut: Optional[str] = None,
    contenu: Optional[str] = None,
):
    """
    Crée une page dans la base Notion Nash Inbox.
    Les paramètres sont tous des chaînes de caractères simples.
    """
    notion_token, database_id = load_env()

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    properties = build_properties(
        title=title,
        source=source,
        type_detected=type_detected,
        categorie=categorie,
        statut=statut,
        contenu=contenu,
    )

    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    print("📤 Envoi vers Notion...")
    resp = requests.post(url, headers=headers, json=payload)

    if resp.status_code >= 200 and resp.status_code < 300:
        data = resp.json()
        page_id = data.get("id", "inconnu")
        print(f"✅ Page créée avec succès dans Nash Inbox. ID : {page_id}")
        return data
    else:
        print("❌ Erreur lors de la création de la page.")
        print(f"Code HTTP : {resp.status_code}")
        try:
            print("Détails :", resp.json())
        except Exception:
            print("Réponse brute :", resp.text)
        sys.exit(1)


def main():
    """
    Mode ligne de commande très simple pour tester depuis ton PC.

    Deux options :
    1) Appel interactif : python nash_executor.py
       → On te pose des questions une par une.

    2) Appel avec un JSON en argument :
       python nash_executor.py '{"title":"Test","source":"Test","type_detected":"Note","categorie":"Test","statut":"À traiter","contenu":"Texte..."}'
    """
    if len(sys.argv) == 2:
        # Mode JSON en argument
        try:
            data = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print("❌ Argument JSON invalide. Exemple :")
            print('python nash_executor.py \'{"title":"Test","source":"Mail","type_detected":"Email","categorie":"Pro","statut":"À traiter","contenu":"Texte..."}\'')
            sys.exit(1)

        title = data.get("title") or "Sans titre"
        source = data.get("source")
        type_detected = data.get("type_detected")
        categorie = data.get("categorie")
        statut = data.get("statut")
        contenu = data.get("contenu")

    else:
        # Mode interactif
        print("🧠 Création d'une nouvelle entrée Nash Inbox (mode interactif)")
        title = input("Titre (obligatoire) : ").strip() or "Sans titre"
        source = input("Source (optionnel) : ").strip() or None
        type_detected = input("Type détecté (optionnel) : ").strip() or None
        categorie = input("Catégorie suggérée (optionnel) : ").strip() or None
        statut = input("Statut (optionnel, ex : À traiter) : ").strip() or None
        contenu = input("Contenu (texte libre, optionnel) : ").strip() or None

    create_nash_page(
        title=title,
        source=source,
        type_detected=type_detected,
        categorie=categorie,
        statut=statut,
        contenu=contenu,
    )


if __name__ == "__main__":
    main()
