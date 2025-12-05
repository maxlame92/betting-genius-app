import streamlit as st
import google.generativeai as genai
import requests
import json
import re
import os
from datetime import date

# ==========================================
# 1. CONFIGURATION INITIALE
# ==========================================
st.set_page_config(
    page_title="BettingGenius API - V9",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DESIGN CSS
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    h1 { color: #F8FAFC; text-transform: uppercase; font-weight: 800; }
    
    /* BOUTON CHERCHER */
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%; height: 50px;
    }
    
    /* STYLE DES TICKETS RÉSULTATS */
    .coupon-container {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
    }
    .border-safe { border-left: 6px solid #22C55E; }
    .border-psycho { border-left: 6px solid #A855F7; }
    .border-fun { border-left: 6px solid #F59E0B; }
    
    /* BADGES */
    .badge { padding: 4px 8px; border-radius: 4px; font-weight: 800; text-transform: uppercase; font-size: 0.75rem; }
    .badge-psy { background-color: #581C87; color: #D8B4FE; }
    
    /* LISTE DES MATCHS */
    .match-box {
        background: #1E293B; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #3B82F6;
        display: flex; justify-content: space-between; align-items: center;
    }
    .match-time { font-weight: bold; color: #94A3B8; margin-right: 15px; }
    .match-teams { font-size: 1.1em; font-weight: bold; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.title("⚡ BettingGenius")
    st.caption("API Edition V9")
    st.markdown("---")
    
    gemini_key = os.environ.get("GOOGLE_API_KEY")
    if not gemini_key:
        gemini_key = st.text_input("🔑 Clé Gemini AI", type="password")
    
    rapid_key = st.text_input("🔑 Clé API-Football", type="password")
    
    st.markdown("---")
    model_version = st.selectbox("Modèle IA", ["gemini-1.5-flash", "gemini-2.0-flash-exp"])

# ==========================================
# 4. LOGIQUE API AUTOMATIQUE
# ==========================================

def get_headers(api_key):
    return {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

def get_season(selected_date):
    """
    Calcule automatiquement la saison en fonction de la date.
    Si on est en Aout-Decembre 2025 -> Saison 2025
    Si on est en Janvier-Mai 2026 -> Saison 2025
    """
    year = selected_date.year
    month = selected_date.month
    # Si on est au deuxième semestre (Juillet à Décembre), c'est la saison de l'année en cours
    if month >= 7:
        return year
    # Si on est au premier semestre (Janvier à Juin), c'est la saison de l'année d'avant
    else:
        return year - 1

def get_fixtures(api_key, league_id, date_obj):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    season = get_season(date_obj) # Calcul auto de la saison
    
    querystring = {"league": str(league_id), "season": str(season), "date": str(date_obj)}
    
    try:
        response = requests.get(url, headers=get_headers(api_key), params=querystring)
        return response.json().get('response', [])
    except:
        return []

def get_match_predictions(api_key, fixture_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/predictions"
    try:
        response = requests.get(url, headers=get_headers(api_key), params={"fixture": str(fixture_id)})
        data = response.json().get('response', [])
        return json.dumps(data[0], indent=2) if data else None
    except:
        return None

def build_api_prompt(match_title, json_data):
    return f"""
    Tu es "BettingGenius". Analyse : {match_title}
    Données API (JSON) : {json_data}
    
    --- MISSION ---
    1. Analyse Forme, H2H, Attaque/Défense.
    2. Détecte le facteur Psycho (Domicile fort ? Série noire ?).
    3. Génère le JSON final.

    Catégories: "SAFE" (>75%), "PSYCHO" (Enjeu), "FUN".

    ```json
    {{
        "match": "{match_title}",
        "pari_principal": "Ex: Victoire Real",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +9.5",
        "total_buts": "Ex: +2.5",
        "confiance": 80,
        "categorie": "SAFE",
        "facteur_psycho": "Ex: FORTERESSE A DOMICILE",
        "analyse_courte": "Phrase courte."
    }}
    ```
    """

# ==========================================
# 5. INTERFACE
# ==========================================

st.title("⚡ BettingGenius - Tous Championnats")

if not rapid_key or not gemini_key:
    st.warning("⚠️ Entrez vos clés API à gauche pour activer le système.")
else:
    # --- SÉLECTEURS ---
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        # LISTE ÉLARGIE DES CHAMPIONNATS
        leagues = {
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39,
            "🇪🇸 La Liga": 140,
            "🇫🇷 Ligue 1": 61,
            "🇩🇪 Bundesliga": 78,
            "🇮🇹 Serie A": 135,
            "🇪🇺 Champions League": 2,
            "🇪🇺 Europa League": 3,
            "🇵🇹 Liga Portugal": 94,
            "🇳🇱 Eredivisie (Pays-Bas)": 88,
            "🇹🇷 Süper Lig (Turquie)": 203,
            "🇸🇦 Saudi Pro League": 307,
            "🇧🇷 Brasileirão": 71,
            "🌍 CAN (Afrique)": 29,
            "🇺🇸 MLS (USA)": 253
        }
        league_choice = st.selectbox("Championnat", list(leagues.keys()))
        league_id = leagues[league_choice]
        
    with c2:
        date_choice = st.date_input("Date du match", date.today())
        
    with c3:
        st.write("") # Espace
        st.write("") 
        search_btn = st.button("🔎 CHERCHER")

    # --- LOGIQUE RECHERCHE ---
    if search_btn:
        with st.spinner(f"Recherche des matchs en {league_choice} pour le {date_choice}..."):
            matches = get_fixtures(rapid_key, league_id, date_choice)
            st.session_state['matches'] = matches
            st.session_state['analysis_result'] = None # Reset analyse

    # --- LISTE DES RÉSULTATS ---
    if 'matches' in st.session_state and st.session_state['matches']:
        st.markdown(f"### {len(st.session_state['matches'])} Matchs trouvés")
        
        for m in st.session_state['matches']:
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            fid = m['fixture']['id']
            time_match = m['fixture']['date'][11:16]
            
            # Affichage Match
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                <div class="match-box">
                    <div>
                        <span class="match-time">{time_match}</span>
                        <span class="match-teams">{home} vs {away}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                if st.button(f"Analyser 🧠", key=fid):
                    with st.spinner("L'IA travaille..."):
                        stats = get_match_predictions(rapid_key, fid)
                        if stats:
                            genai.configure(api_key=gemini_key)
                            model = genai.GenerativeModel(model_version)
                            try:
                                res = model.generate_content(build_api_prompt(f"{home}-{away}", stats))
                                full_text = res.text
                                # Parse
                                j_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                                if j_match:
                                    j = json.loads(re.sub(r'//.*', '', j_match.group(0)))
                                    st.session_state['analysis_result'] = {"json": j, "text": full_text}
                            except Exception as e:
                                st.error(f"Erreur IA : {e}")
                        else:
                            st.error("Données indisponibles pour ce match.")
                            
    elif 'matches' in st.session_state:
        st.warning(f"🚫 Aucun match trouvé le {date_choice} pour ce championnat. Essayez une autre date (ex: le week-end).")

    # --- AFFICHAGE TICKET ---
    if 'analysis_result' in st.session_state and st.session_state['analysis_result']:
        res = st.session_state['analysis_result']
        j = res['json']
        cat = j.get('categorie', 'FUN')
        border = "border-safe" if cat=="SAFE" else "border-psycho" if cat=="PSYCHO" else "border-fun"
        
        st.markdown("---")
        st.markdown(f"""
        <div class="coupon-container {border}">
            <div style="display:flex; justify-content:space-between;">
                <h3>{j.get('match')}</h3>
                <div>
                    <span class="badge badge-psy">{j.get('facteur_psycho')}</span>
                    <strong style="color:#4ADE80; font-size:1.2em;">{j.get('confiance')}%</strong>
                </div>
            </div>
            
            <div style="text-align:center; margin:20px 0; background:#0F172A; padding:15px; border-radius:8px; border:1px dashed #334155;">
                <div style="color:#22C55E; font-size:1.5em; font-weight:800;">🏆 {j.get('pari_principal')}</div>
            </div>
            
            <div style="display:flex; gap:10px; text-align:center;">
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:6px;">
                    <div style="color:#94A3B8; font-size:0.8em;">SCORE</div>
                    <div style="font-weight:bold;">{j.get('score_exact')}</div>
                </div>
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:6px;">
                    <div style="color:#94A3B8; font-size:0.8em;">BUTS</div>
                    <div style="font-weight:bold;">{j.get('total_buts')}</div>
                </div>
            </div>
            <br>
            <div style="font-style:italic; color:#CBD5E1;">"{j.get('analyse_courte')}"</div>
        </div>
        """, unsafe_allow_html=True)