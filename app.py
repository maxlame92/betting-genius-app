import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import re
import os

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="BettingGenius Ultimate - AI & PsychoEngine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE VISUEL PREMIUM (CSS) ---
st.markdown("""
<style>
    /* Fond sombre professionnel */
    .stApp { background-color: #0b0f19; color: #e0e6ed; }
    
    /* Typographie */
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    h1 { color: #ffffff; font-weight: 800; }
    h2 { color: #e2e8f0; border-bottom: 2px solid #2d3748; padding-bottom: 10px; }
    h3 { color: #10B981; } /* Vert BettingGenius */

    /* CARTES COUPONS */
    .coupon-card {
        background: linear-gradient(145deg, #161b26, #11151e);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3748;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease-in-out;
    }
    .coupon-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px rgba(0,0,0,0.4); }

    /* COULEURS DES CATÉGORIES */
    .border-safe { border-left: 6px solid #10B981; }   /* VERT (Blindé) */
    .border-psycho { border-left: 6px solid #8B5CF6; } /* VIOLET (Psycho) */
    .border-fun { border-left: 6px solid #F59E0B; }    /* ORANGE (Fun) */

    /* BADGES */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .badge-conf { background-color: #064e3b; color: #6ee7b7; border: 1px solid #10B981; }
    .badge-psy { background-color: #4c1d95; color: #c4b5fd; border: 1px solid #8B5CF6; }
    
    /* TEXTES DANS LES CARTES */
    .match-title { font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 10px; }
    .prediction-main { color: #10B981; font-weight: 700; font-size: 1.1rem; margin-bottom: 5px; }
    .prediction-details { color: #94a3b8; font-size: 0.9rem; display: flex; gap: 15px; }
    .analysis-short { color: #cbd5e1; font-style: italic; margin-top: 10px; border-top: 1px solid #2d3748; padding-top: 8px; }

    /* BOUTON D'ACTION */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%);
        color: white; border: none; padding: 16px; font-size: 18px; font-weight: bold; border-radius: 10px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        transition: 0.3s;
    }
    .stButton>button:hover { background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%); transform: scale(1.02); }
    
    /* ZONE ANALYSE TEXTE */
    .full-analysis-box {
        background-color: #1f2937;
        padding: 25px;
        border-radius: 10px;
        border-left: 4px solid #3B82F6;
        color: #d1d5db;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BARRE LATÉRALE (SETUP) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2586/2586885.png", width=70)
    st.title("BettingGenius")
    st.markdown("**Version Ultimate (SaaS)**")
    st.markdown("---")
    
    # GESTION CLÉ API (Compatible Local & Render)
    # 1. On cherche dans l'environnement (Render)
    api_key = os.environ.get("GOOGLE_API_KEY")
    # 2. Sinon on demande à l'utilisateur (Local)
    if not api_key:
        api_key = st.text_input("🔑 Clé API Google Gemini", type="password", help="Obligatoire pour l'analyse")

    st.markdown("### 🧠 Cerveau IA")
    model_version = st.selectbox("Modèle :", ["gemini-1.5-flash", "gemini-2.0-flash-exp"])
    
    st.success("""
    **Moteurs Activés :**
    ✅ Analyse 9 Points
    ✅ PsychoEngine™
    ✅ Anti-Hallucination
    ✅ Trieur de Coupons
    """)
    st.markdown("---")
    st.info("Développé pour les parieurs pro.")

# --- 4. FONCTIONS DU NOYAU ---

def get_besoccer_data(url):
    """Scrape le contenu BeSoccer proprement."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Suppression du bruit
            for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "header"]):
                tag.extract()
            text = ' '.join(soup.get_text(separator=' ').split())
            title = soup.find('title').text if soup.find('title') else "Match Inconnu"
            # On garde 30k caractères pour avoir le contexte complet
            return {"title": title, "content": text[:30000]}
        return None
    except Exception as e:
        return None

def build_ultimate_prompt(match_data):
    """
    LE PROMPT DÉFINITIF : Combine Technique, Psychologie et Structure JSON.
    """
    return f"""
    Tu es "BettingGenius", l'IA ultime d'aide aux paris sportifs.
    
    MATCH À ANALYSER : {match_data['title']}
    DONNÉES BRUTES : "{match_data['content']}"

    --- MISSION 1 : L'ANALYSE DÉTAILLÉE (TEXTE) ---
    Rédige une analyse point par point.
    RÈGLE D'OR : Si une information (ex: Météo, Arbitre) n'est PAS dans le texte, écris "❌ Info non disponible". NE RIEN INVENTER.

    1. **🏆 Prédiction de victoire** : Analyse la forme, mais surtout la DYNAMIQUE MENTALE (Confiance, Crise ?).
    2. **🚩 Corners** : Stratégies de possession, jeu sur les ailes, statistiques si dispos.
    3. **🔢 Score exact** : Compatibilité offensive/défensive.
    4. **⚽ Total Buts** : Momentum, agressivité, moyenne de buts.
    5. **⏱️ Performance par période** : Moments clés (Buts tardifs ? 1ère mi-temps ?).
    6. **🏥 Absences/Retours** : Impact sur la synergie (Seulement si mentionné dans le texte).
    7. **🏟️ Conditions** : Domicile/Extérieur, Météo (Seulement si mentionné).
    8. **⚠️ Facteurs X** : Cartons, Arbitre, Nervosité, Enjeux extra-sportifs.
    9. **🎲 Simulation Monte Carlo** : Le scénario le plus probable vs le scénario surprise.

    --- MISSION 2 : LE PSYCHO-ENGINE (MENTAL) ---
    Détecte l'enjeu caché : Maintien ? Titre ? Derby ? Revanche ?
    
    --- MISSION 3 : LE COUPON (JSON STRICT) ---
    Génère un bloc JSON à la toute fin pour que je classe ce match.
    
    Choix de la catégorie ("categorie") :
    - "SAFE" (Blindé) : Favori forme + Motivation forte + Confiance > 80%.
    - "PSYCHO" (Coup Tactique) : Une équipe joue sa SURVIE, le TITRE ou une REVANCHE (Gros enjeu mental détecté).
    - "FUN" : Match indécis, pari buteur ou grosse cote risquée.

    Format JSON attendu :
    ```json
    {{
        "match": "{match_data['title']}",
        "pari_principal": "Ex: Victoire Marseille",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +8.5 Corners",
        "total_buts": "Ex: +2.5 Buts",
        "confiance": 85,
        "categorie": "SAFE", 
        "facteur_psycho": "Ex: COURSE AU TITRE / MAINTIEN / DERBY / NEUTRE",
        "analyse_courte": "Une phrase percutante qui résume pourquoi on parie ça."
    }}
    ```
    """

# --- 5. INTERFACE UTILISATEUR PRINCIPALE ---

st.title("🧠 BettingGenius Ultimate")
st.markdown("### L'outil d'analyse le plus complet du marché.")
st.markdown("Collez vos liens **BeSoccer** ci-dessous pour générer l'analyse 9 points, le profil psychologique et les coupons.")

# Zone de saisie
urls_input = st.text_area("🔗 Liens des matchs (Un par ligne)", height=150, placeholder="https://fr.besoccer.com/match/...\nhttps://fr.besoccer.com/match/...")

# Gestion de l'état (pour ne pas perdre les résultats si on clique ailleurs)
if "results" not in st.session_state:
    st.session_state.results = []

# --- BOUTON DE LANCEMENT ---
if st.button("LANCER L'ANALYSE COMPLÈTE 🚀"):
    if not api_key:
        st.error("⛔ Veuillez entrer une Clé API Gemini.")
    elif not urls_input:
        st.warning("⛔ Veuillez coller au moins un lien.")
    else:
        # Nettoyage des liens
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state.results = [] # Reset des résultats précédents
        
        # Barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Config IA
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_version)
        
        # BOUCLE D'ANALYSE
        for i, url in enumerate(urls):
            status_text.markdown(f"**🧠 Analyse en cours : Match {i+1}/{len(urls)}...**")
            
            # 1. Scraping
            data = get_besoccer_data(url)
            
            if data:
                try:
                    # 2. Génération IA
                    response = model.generate_content(build_ultimate_prompt(data))
                    full_text = response.text
                    
                    # 3. Extraction JSON (Données Structurées)
                    json_data = {}
                    # Regex pour trouver le JSON entre accolades, même si l'IA parle avant/après
                    json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                    if json_match:
                        clean_json = re.sub(r'//.*', '', json_match.group(0)) # Nettoyage commentaires
                        try:
                            json_data = json.loads(clean_json)
                        except:
                            json_data = {"match": data['title'], "pari_principal": "Erreur format", "categorie": "FUN"}
                        
                        # Sécurité titre
                        if "match" not in json_data: json_data["match"] = data["title"]
                    
                    # 4. Extraction Texte (Analyse Détaillée sans le JSON)
                    clean_analysis_text = re.sub(r'```json.*```', '', full_text, flags=re.DOTALL)
                    
                    # 5. Sauvegarde
                    st.session_state.results.append({
                        "json": json_data,
                        "analysis_text": clean_analysis_text,
                        "title": data['title']
                    })
                    
                except Exception as e:
                    st.error(f"Erreur sur le lien {i+1}: {e}")
            else:
                st.error(f"Impossible de lire le lien : {url}")
            
            # Mise à jour progression
            progress_bar.progress((i + 1) / len(urls))
        
        status_text.empty()
        st.balloons() # Petite animation de succès
        st.success("✅ Analyse terminée ! Découvrez vos coupons ci-dessous.")

# --- 6. AFFICHAGE DES RÉSULTATS (DASHBOARD) ---

if st.session_state.results:
    st.markdown("---")
    
    # Tri des résultats par catégorie
    safes = [r for r in st.session_state.results if r['json'].get('categorie') == 'SAFE']
    psychos = [r for r in st.session_state.results if r['json'].get('categorie') == 'PSYCHO']
    funs = [r for r in st.session_state.results if r['json'].get('categorie') == 'FUN']

    # --- SECTION 1 : LES COUPONS INTELLIGENTS ---
    st.subheader("🎟️ VOS COUPONS PRO")
    
    tab_safe, tab_psycho, tab_fun = st.tabs([
        "🛡️ LE BLINDÉ (Sécurité)", 
        "🧠 LE TACTIQUE (Enjeu Mental)", 
        "💣 LE FUN (Risque)"
    ])

    # Onglet SAFE
    with tab_safe:
        st.caption("Matchs à haute fiabilité. Forme physique + Mentale alignées.")
        if safes:
            for item in safes:
                j = item['json']
                st.markdown(f"""
                <div class="coupon-card border-safe">
                    <div class="match-title">{j.get('match')}</div>
                    <div>
                        <span class="badge badge-conf">CONFIANCE {j.get('confiance')}%</span>
                        <span class="badge" style="background:#1f2937; color:#fff;">{j.get('facteur_psycho', 'SOLIDE')}</span>
                    </div>
                    <div class="prediction-main">🏆 {j.get('pari_principal')}</div>
                    <div class="prediction-details">
                        <span>⚽ {j.get('total_buts')}</span>
                        <span>🔢 {j.get('score_exact')}</span>
                    </div>
                    <div class="analysis-short">"{j.get('analyse_courte')}"</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucun match ne répond aux critères de sécurité maximale (80%+) aujourd'hui.")

    # Onglet PSYCHO
    with tab_psycho:
        st.caption("Matchs détectés par le PsychoEngine™ : Enjeux critiques (Maintien, Titre, Revanche).")
        if psychos:
            for item in psychos:
                j = item['json']
                st.markdown(f"""
                <div class="coupon-card border-psycho">
                    <div class="match-title">{j.get('match')}</div>
                    <div>
                        <span class="badge badge-psy">🧠 {j.get('facteur_psycho', 'ENJEU')}</span>
                        <span class="badge badge-conf">CONFIANCE {j.get('confiance')}%</span>
                    </div>
                    <div class="prediction-main">👉 {j.get('pari_principal')}</div>
                    <div class="prediction-details">
                        <span>🚩 {j.get('corners')}</span>
                        <span>🔢 {j.get('score_exact')}</span>
                    </div>
                    <div class="analysis-short">"{j.get('analyse_courte')}"</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aucun enjeu psychologique majeur détecté dans cette liste.")

    # Onglet FUN
    with tab_fun:
        st.caption("Matchs indécis ou paris alternatifs (Pour le plaisir).")
        if funs:
            for item in funs:
                j = item['json']
                st.markdown(f"""
                <div class="coupon-card border-fun">
                    <div class="match-title">{j.get('match')}</div>
                    <div class="prediction-main">🎲 {j.get('pari_principal')}</div>
                    <div class="prediction-details">
                         <span>⚽ {j.get('total_buts')}</span>
                    </div>
                    <div class="analysis-short">"{j.get('analyse_courte')}"</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("Pas de matchs classés 'Fun'.")

    st.markdown("---")

    # --- SECTION 2 : ANALYSES DÉTAILLÉES (9 POINTS) ---
    st.subheader("📝 ANALYSES DÉTAILLÉES (Les 9 Points Clés)")
    st.caption("Cliquez pour lire l'argumentaire complet de l'IA pour chaque match.")
    
    for item in st.session_state.results:
        with st.expander(f"🔎 Lire l'analyse complète : {item['title']}", expanded=False):
            st.markdown(f"""
            <div class="full-analysis-box">
                {item['analysis_text']}
            </div>
            """, unsafe_allow_html=True)