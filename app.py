import streamlit as st
import google.generativeai as genai
import requests
import json
import re
import os
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="BettingGenius - Football Data", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e0e6ed; }
    .coupon-card { background: #161b26; padding: 20px; border-radius: 12px; border: 1px solid #2d3748; margin-bottom: 15px; }
    .stButton>button { width: 100%; background: #00D26A; color: white; border: none; padding: 15px; font-weight: bold; border-radius: 8px; }
    .badge-conf { background-color: #064e3b; color: #6ee7b7; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR & CLÉS ---
with st.sidebar:
    st.title("⚽ BettingGenius FD")
    st.markdown("Source : **Football-Data.org**")
    
    # 1. Clé Google Gemini
    api_key_gemini = os.environ.get("GOOGLE_API_KEY")
    if not api_key_gemini:
        api_key_gemini = st.text_input("Clé Gemini (Google AI)", type="password")
    
    # 2. Clé Football-Data.org
    api_key_foot = os.environ.get("FOOTBALL_DATA_KEY")
    if not api_key_foot:
        api_key_foot = st.text_input("Clé Football-Data.org (Token)", type="password", help="Reçue par mail après inscription")

# --- 3. FONCTIONS API (Football-Data.org) ---

def get_football_data(endpoint, api_key):
    """Appel générique à l'API Football-Data.org"""
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = { "X-Auth-Token": api_key }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return "LIMIT" # Trop de requêtes
        else:
            return None
    except:
        return None

def get_team_analysis_data(team_name, api_key):
    """
    Récupère les infos via Football-Data.org
    Attention : Le plan gratuit limite aux grandes ligues.
    """
    summary = ""
    
    # A. Recherche de l'ID de l'équipe
    # L'API ne permet pas une recherche directe facile en free tier parfois, 
    # mais on peut chercher dans les compétitions. Ici on tente le endpoint 'teams'.
    # Si ça échoue, on demandera à l'utilisateur d'être précis.
    
    # Note : Cette API est stricte sur les noms (ex: "Real Madrid CF" au lieu de "Real").
    # On va faire une recherche large si possible.
    
    # Pour simplifier en Free Tier, on va scanner les matchs à venir d'une compétition majeure
    # Ou utiliser le endpoint 'matches' générique.
    
    # 1. Chercher les matchs à venir qui contiennent le nom de l'équipe
    matches_data = get_football_data("matches", api_key)
    
    if matches_data == "LIMIT":
        return None, "⚠️ Limite d'API atteinte. Attendez 1 minute."
    if not matches_data or 'matches' not in matches_data:
        return None, "Erreur de connexion API ou Clé invalide."

    target_match = None
    
    # On cherche un match où l'équipe joue (Home ou Away) dans les 10 prochains jours
    # (L'endpoint /matches par défaut donne les matchs du jour ou proches)
    for m in matches_data['matches']:
        home = m['homeTeam']['name'].lower()
        away = m['awayTeam']['name'].lower()
        search = team_name.lower()
        
        if search in home or search in away:
            target_match = m
            break
            
    if not target_match:
        return None, f"Aucun match trouvé prochainement pour '{team_name}' (ou équipe mal orthographiée)."
    
    # B. Extraction des données du match trouvé
    home_team = target_match['homeTeam']['name']
    away_team = target_match['awayTeam']['name']
    date = target_match['utcDate']
    competition = target_match['competition']['name']
    
    match_title = f"{home_team} vs {away_team}"
    summary += f"MATCH : {match_title}\n"
    summary += f"Compétition : {competition} | Date : {date}\n\n"
    
    # C. Récupération du Classement (Standings)
    # On a besoin de l'ID de la compétition
    comp_code = target_match['competition']['code'] # ex: PL, PD, CL
    standings = get_football_data(f"competitions/{comp_code}/standings", api_key)
    
    if standings and 'standings' in standings:
        try:
            table = standings['standings'][0]['table']
            home_stats = next((t for t in table if t['team']['id'] == target_match['homeTeam']['id']), None)
            away_stats = next((t for t in table if t['team']['id'] == target_match['awayTeam']['id']), None)
            
            if home_stats:
                summary += f"--- {home_team} (Domicile) ---\n"
                summary += f"Classement: {home_stats['position']}ème | Points: {home_stats['points']}\n"
                summary += f"Buts: {home_stats['goalsFor']} Pour / {home_stats['goalsAgainst']} Contre\n"
                summary += f"Forme (Derniers 5): {home_stats.get('form', 'N/A')}\n\n" # La forme est une string genre "W,L,D,W,W"
            
            if away_stats:
                summary += f"--- {away_team} (Extérieur) ---\n"
                summary += f"Classement: {away_stats['position']}ème | Points: {away_stats['points']}\n"
                summary += f"Buts: {away_stats['goalsFor']} Pour / {away_stats['goalsAgainst']} Contre\n"
                summary += f"Forme (Derniers 5): {away_stats.get('form', 'N/A')}\n"
        except:
            summary += "Données de classement partiel.\n"

    return match_title, summary

def build_api_prompt(title, data):
    return f"""
    Tu es "BettingGenius". Analyse ce match avec les données API fournies.
    
    MATCH : {title}
    DONNÉES : 
    {data}
    
    --- TACHE ---
    1. Analyse la FORME (Regarde la ligne 'Forme': W=Win, L=Loss, D=Draw). C'est crucial.
    2. Compare les Buts Pour/Contre pour estimer le potentiel offensif.
    3. Donne un pronostic JSON.
    
    Format JSON attendu :
    {{
        "match": "{title}",
        "pari_principal": "...",
        "score_exact": "...",
        "confiance": 80,
        "categorie": "SAFE/FUN",
        "analyse_courte": "..."
    }}
    """

# --- 4. INTERFACE ---

st.title("⚽ BettingGenius - Data Directe")
st.caption("Utilise l'API Football-Data.org (Gratuite pour les grandes ligues)")

team_input = st.text_input("Nom de l'équipe (ex: Man City, Real Madrid, Bayern)", placeholder="Tapez le nom...")

if st.button("ANALYSER CE MATCH 🚀"):
    if not api_key_gemini or not api_key_foot:
        st.error("⚠️ Veuillez entrer les 2 clés API dans la barre latérale.")
    elif not team_input:
        st.warning("⚠️ Entrez un nom d'équipe.")
    else:
        with st.spinner("🌍 Connexion à Football-Data.org..."):
            match_title, data_text = get_team_analysis_data(team_input, api_key_foot)
            
            if not match_title:
                st.error(f"Erreur : {data_text}")
                st.info("Note : Le plan gratuit ne couvre que les ligues majeures (PL, Liga, Bundesliga, Serie A, L1, UCL).")
            else:
                st.success(f"Match Trouvé : {match_title}")
                with st.expander("Voir les données brutes"):
                    st.text(data_text)
                
                # IA
                with st.spinner("🧠 Analyse de la forme en cours..."):
                    genai.configure(api_key=api_key_gemini)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(build_api_prompt(match_title, data_text))
                    text = response.text
                    
                    # Extraction JSON
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        try:
                            clean_json = re.sub(r'//.*', '', json_match.group(0))
                            j = json.loads(clean_json)
                            
                            st.markdown(f"""
                            <div class="coupon-card">
                                <h3>{j.get('match')}</h3>
                                <h2 style="color:#00D26A;">👉 {j.get('pari_principal')}</h2>
                                <span class="badge-conf">Confiance {j.get('confiance')}%</span>
                                <p style="margin-top:10px;"><em>"{j.get('analyse_courte')}"</em></p>
                                <hr>
                                <p>Score estimé : {j.get('score_exact')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        except:
                            st.write("Erreur d'affichage.")
                    
                    st.markdown("#### Détails")
                    clean = re.sub(r'```json.*```', '', text, flags=re.DOTALL)
                    st.markdown(clean)