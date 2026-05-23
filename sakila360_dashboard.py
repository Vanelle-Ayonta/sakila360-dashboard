import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Sakila 360", page_icon="🎬", layout="wide",
                   initial_sidebar_state="expanded")

BG="#f8fafc"; CARD="#ffffff"; TEXT="#0f172a"; MUTED="#64748b"
NAVY="#003F7F"; GOLD="#C9A84C"; BORDER="#e2e8f0"
SUCCESS="#10b981"; DANGER="#ef4444"
COLORS=[GOLD,"#4fc3f7","#a78bfa","#34d399","#f87171","#fb923c","#38bdf8","#e879f9"]

PAGES = {
    "Vue d'ensemble":     ("📊", "Lecture rapide des revenus, locations, retards et segments clients."),
    "Analyse temporelle": ("📈", "Évolution mensuelle et tendances du chiffre d'affaires."),
    "Performances":       ("🎬", "Films, catégories, ratings et taux d'occupation."),
    "Clients":            ("👥", "Segmentation, fidélité et comportement d'achat."),
    "Géographie":         ("🌍", "Distribution mondiale des locations et revenus."),
    "Données brutes":     ("📋", "Accès direct aux transactions filtrées."),
}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "page"           not in st.session_state: st.session_state["page"]           = "Vue d'ensemble"
if "sidebar_reduite" not in st.session_state: st.session_state["sidebar_reduite"] = False
if "sel_cats"       not in st.session_state: st.session_state["sel_cats"]       = ["Tous"]
if "sel_pays"       not in st.session_state: st.session_state["sel_pays"]       = "Tous"
if "sel_mag"        not in st.session_state: st.session_state["sel_mag"]        = "Tous"
if "sel_seg"        not in st.session_state: st.session_state["sel_seg"]        = "Tous"
if "sel_annee"      not in st.session_state: st.session_state["sel_annee"]      = "Toutes"

_sidebar_w = "62px" if st.session_state["sidebar_reduite"] else "220px"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{{font-family:'Inter',sans-serif!important;box-sizing:border-box}}
html,body{{background:{BG}!important;color:{TEXT}}}
.stApp{{background:{BG}!important}}
.block-container{{padding:1.5rem 2rem 3rem!important;max-width:100%!important}}

/* ── SIDEBAR ── */
[data-testid="collapsedControl"]{{display:none!important}}
section[data-testid="stSidebar"]{{
    background:{CARD}!important;
    border-right:1px solid {BORDER}!important;
    min-width:{_sidebar_w}!important;max-width:{_sidebar_w}!important;
}}
section[data-testid="stSidebar"]>div:first-child{{padding:1.2rem 0.8rem!important}}
section[data-testid="stSidebar"] .stButton>button{{
    width:100%!important;text-align:left!important;border:none!important;
    border-radius:8px!important;padding:0.5rem 0.75rem!important;
    font-size:0.855rem!important;font-weight:400!important;
    color:{MUTED}!important;background:transparent!important;
    box-shadow:none!important;transition:all 0.15s!important;
    justify-content:flex-start!important;
}}
section[data-testid="stSidebar"] .stButton>button:hover{{
    background:{BG}!important;color:{TEXT}!important;
}}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{{
    background:#fef3c7!important;color:#92400e!important;font-weight:600!important;
    border-left:3px solid {GOLD}!important;padding-left:calc(0.75rem - 1px)!important;
}}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{{
    background:#fef3c7!important;
}}
section[data-testid="stSidebar"] .stButton>button[disabled]{{
    opacity:0.5!important;cursor:default!important;
}}

/* ── MAIN INPUTS ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label{{display:none!important}}
div[data-testid="stSelectbox"]>div>div,
div[data-testid="stMultiSelect"]>div>div{{
    background:{CARD}!important;border:1px solid {BORDER}!important;
    border-radius:8px!important;font-size:0.83rem!important;
}}
div[data-testid="stMultiSelect"] span[data-baseweb="tag"]{{
    background:{NAVY}!important;color:#fff!important;
}}

/* ── APPLY BUTTON ── */
.stButton>button[kind="primary"]{{
    background:{NAVY}!important;color:#fff!important;border:none!important;
    border-radius:8px!important;font-weight:600!important;font-size:0.83rem!important;
}}
.stButton>button[kind="primary"]:hover{{background:#002d5c!important}}

/* ── METRIC OVERRIDE ── */
div[data-testid="metric-container"]{{
    background:{CARD}!important;border:1px solid {BORDER}!important;
    border-radius:10px!important;padding:0.8rem 1rem!important;
    box-shadow:0 1px 3px rgba(0,0,0,0.06)!important;
}}
div[data-testid="metric-container"] label{{color:{NAVY}!important;font-size:0.68rem!important;
    text-transform:uppercase!important;letter-spacing:0.08em!important}}

/* ── MISC ── */
div[data-testid="stDownloadButton"] button{{
    background:{GOLD}!important;color:{NAVY}!important;font-weight:700!important;
    border:none!important;border-radius:8px!important;
}}
::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-track{{background:{BG}}}
::-webkit-scrollbar-thumb{{background:rgba(0,63,127,0.2);border-radius:3px}}
footer{{display:none!important}}
#MainMenu{{display:none!important}}
</style>""", unsafe_allow_html=True)

# ── DB ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sakila_dwh.db")
    return create_engine(f"sqlite:///{db}", connect_args={"check_same_thread": False})

@st.cache_data(ttl=300)
def q(sql):
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)

# ── STATIC LOADERS ────────────────────────────────────────────────────────────
def load_cats():
    return q("SELECT DISTINCT categorie FROM dim_film ORDER BY categorie")['categorie'].tolist()
def load_pays():
    return q("SELECT DISTINCT pays FROM dim_customer ORDER BY pays")['pays'].tolist()
def load_stores():
    return q("SELECT store_key, ville || ' — ' || adresse AS label FROM dim_store")
def load_segs():
    return q("SELECT DISTINCT segment FROM dim_customer ORDER BY segment")['segment'].tolist()
def load_years():
    return [int(y) for y in q("SELECT DISTINCT annee FROM dim_date ORDER BY annee")['annee'].tolist()]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def safe(v, typ=float, default=0):
    if v is None: return default
    try: return typ(v)
    except: return default

PL = dict(plot_bgcolor=CARD, paper_bgcolor=CARD, font_color=MUTED, font_size=11,
          margin=dict(l=0, r=0, t=10, b=0))

def lay(fig, h=300, legend=None, **kw):
    leg = legend or dict(bgcolor="rgba(0,0,0,0)", font_color=TEXT)
    fig.update_layout(**PL, height=h, legend=leg, **kw)
    fig.update_xaxes(showgrid=False, color="#94a3b8", tickfont_color=MUTED)
    fig.update_yaxes(gridcolor="#f1f5f9", color="#94a3b8", tickfont_color=MUTED)
    return fig

def kpi(col, label, value, sub="", color=NAVY):
    with col:
        st.markdown(f"""<div style="background:{CARD};border-radius:12px;
            padding:1.1rem 1.3rem;border-left:4px solid {color};
            box-shadow:0 1px 3px rgba(0,0,0,0.08);height:100%">
            <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.1em;color:{MUTED};margin-bottom:0.5rem">{label}</div>
            <div style="font-size:1.65rem;font-weight:700;color:{TEXT};line-height:1.1;
                margin-bottom:0.3rem">{value}</div>
            <div style="font-size:0.73rem;color:{MUTED}">{sub}</div>
        </div>""", unsafe_allow_html=True)

def section(title, sub=""):
    st.markdown(f"""<div style="margin:1.5rem 0 0.8rem">
        <div style="font-size:0.9rem;font-weight:600;color:{TEXT}">{title}</div>
        {"<div style='font-size:0.68rem;color:"+GOLD+";text-transform:uppercase;letter-spacing:0.08em;margin-top:2px'>"+sub+"</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)

def page_header(title, subtitle):
    st.markdown(f"""<div style="margin-bottom:1.2rem">
        <div style="font-size:0.65rem;font-weight:600;color:{MUTED};text-transform:uppercase;
            letter-spacing:0.1em;margin-bottom:0.4rem">DASHBOARD ANALYTIQUE</div>
        <h1 style="font-size:1.8rem;font-weight:700;color:{TEXT};margin:0 0 0.3rem">{title}</h1>
        <p style="font-size:0.85rem;color:{MUTED};margin:0 0 1rem">{subtitle}</p>
        <div style="height:1px;background:{BORDER}"></div>
    </div>""", unsafe_allow_html=True)

# ── FILTER STATE ──────────────────────────────────────────────────────────────
def get_flt():
    stores_df = load_stores()

    sel_cats = st.session_state.get("sel_cats", ["Tous"])
    cats = [c for c in sel_cats if c != "Tous"]

    pays_raw = st.session_state.get("sel_pays", "Tous")
    pays = [] if pays_raw == "Tous" else [pays_raw]

    mag_raw = st.session_state.get("sel_mag", "Tous")
    sk = [] if mag_raw == "Tous" else stores_df[stores_df["label"] == mag_raw]["store_key"].tolist()

    seg_raw = st.session_state.get("sel_seg", "Tous")
    segs = [] if seg_raw == "Tous" else [seg_raw]

    yr_raw = st.session_state.get("sel_annee", "Toutes")
    return {
        "cats":  cats,
        "pays":  pays,
        "sk":    sk,
        "segs":  segs,
        "year":  None if yr_raw == "Toutes" else int(yr_raw),
    }

def W(f, fn="f", cn="c", rn="fr", dn="d",
      cat=True, pays=False, store=True, seg=False, yr=True):
    cl = []
    if cat   and f["cats"]: cl.append("{}.categorie IN ({})".format(fn, ",".join(f"'{x}'" for x in f["cats"])))
    if pays  and f["pays"]: cl.append("{}.pays IN ({})".format(cn, ",".join(f"'{x}'" for x in f["pays"])))
    if store and f["sk"]:   cl.append("{}.store_key IN ({})".format(rn, ",".join(str(x) for x in f["sk"])))
    if seg   and f["segs"]: cl.append("{}.segment IN ({})".format(cn, ",".join(f"'{x}'" for x in f["segs"])))
    if yr    and f["year"]: cl.append(f"{dn}.annee = {f['year']}")
    return " AND ".join(cl) if cl else "1=1"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
_rapport_pdf  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rapport.pdf")
_rapport_docx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rapport.docx")

with st.sidebar:
    if st.session_state["sidebar_reduite"]:
        for pname, (icon, _) in PAGES.items():
            is_active = st.session_state.page == pname
            if st.button(icon, key=f"icon_{pname}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                st.session_state.page = pname
                st.rerun()
        st.markdown(f"<div style='height:1px;background:{BORDER};margin:1rem 0'></div>",
                    unsafe_allow_html=True)
        if st.button("→", key="btn_expand", use_container_width=True):
            st.session_state["sidebar_reduite"] = False
            st.rerun()
    else:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;padding:0.2rem 0 1rem">
            <div style="background:{NAVY};color:#fff;font-size:0.82rem;font-weight:800;
                border-radius:9px;padding:0.38rem 0.45rem;letter-spacing:-0.5px;flex-shrink:0">S360</div>
            <div>
                <div style="font-weight:700;color:{TEXT};font-size:0.9rem;line-height:1.2">Sakila 360</div>
                <div style="font-size:0.58rem;color:{MUTED};text-transform:uppercase;
                    letter-spacing:0.1em">Data Warehouse</div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"<div style='height:1px;background:{BORDER};margin:0 0 0.6rem'></div>",
                    unsafe_allow_html=True)

        for pname, (icon, _) in PAGES.items():
            is_active = st.session_state.page == pname
            if st.button(f"{icon}  {pname}", key=f"nav_{pname}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                st.session_state.page = pname
                st.rerun()

        st.markdown(f"<div style='height:1px;background:{BORDER};margin:1rem 0'></div>",
                    unsafe_allow_html=True)

        if os.path.exists(_rapport_pdf):
            with open(_rapport_pdf, "rb") as _rf:
                st.download_button("⬇ Rapport PDF", data=_rf.read(),
                    file_name="Rapport_Sakila360_DWH.pdf", mime="application/pdf",
                    use_container_width=True, key="btn_rapport")
        elif os.path.exists(_rapport_docx):
            with open(_rapport_docx, "rb") as _rf:
                st.download_button("⬇ Rapport", data=_rf.read(),
                    file_name="Rapport_Sakila360_DWH.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True, key="btn_rapport")
        else:
            st.caption("Rapport non trouvé")

        st.markdown(f"""<div style="padding:0.6rem 0.2rem 0.4rem">
            <div style="font-size:0.58rem;color:{MUTED};text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.3rem">MODÈLE</div>
            <div style="font-size:0.83rem;color:{TEXT};font-weight:500">Schéma étoile</div>
        </div>""", unsafe_allow_html=True)

        if st.button("← Réduire", key="btn_reduce", use_container_width=True):
            st.session_state["sidebar_reduite"] = True
            st.rerun()

# ── FILTER BAR ────────────────────────────────────────────────────────────────
def render_filter_bar():
    cats_all  = load_cats()
    pays_all  = load_pays()
    stores_df = load_stores()
    segs_all  = load_segs()
    years_all = load_years()

    st.markdown(f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
        padding:1rem 1.4rem 0.7rem;margin-bottom:1.4rem;
        box-shadow:0 1px 3px rgba(0,0,0,0.07)">
        <span style="font-size:0.62rem;font-weight:700;color:{NAVY};text-transform:uppercase;
        letter-spacing:0.1em">⚙ Options d'analyse croisée</span></div>""",
        unsafe_allow_html=True)

    c0, c1, c2, c3, c4, c5, c6 = st.columns([2.2, 2, 2, 2, 2, 1.3, 1.3])

    with c0:
        st.markdown(f"""<div style="padding-top:0.15rem">
            <div style="font-weight:700;color:{TEXT};font-size:0.82rem">
                Options d'analyse croisée</div>
            <div style="font-size:0.66rem;color:{MUTED};line-height:1.5;margin-top:2px">
                Sélectionne une ou plusieurs valeurs.<br>Vide = Tous.</div>
        </div>""", unsafe_allow_html=True)

    FLB = f"font-size:0.63rem;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:{MUTED};margin-bottom:3px"
    with c1:
        st.markdown(f'<p style="{FLB}">CATÉGORIE</p>', unsafe_allow_html=True)
        st.multiselect("cat", ["Tous"] + cats_all, label_visibility="collapsed", key="sel_cats")
    with c2:
        st.markdown(f'<p style="{FLB}">PAYS</p>', unsafe_allow_html=True)
        st.selectbox("pays", ["Tous"] + pays_all, label_visibility="collapsed", key="sel_pays")
    with c3:
        st.markdown(f'<p style="{FLB}">MAGASIN</p>', unsafe_allow_html=True)
        st.selectbox("mag", ["Tous"] + stores_df["label"].tolist(), label_visibility="collapsed",
                     key="sel_mag")
    with c4:
        st.markdown(f'<p style="{FLB}">SEGMENT CLIENT</p>', unsafe_allow_html=True)
        st.selectbox("seg", ["Tous"] + segs_all, label_visibility="collapsed", key="sel_seg")
    with c5:
        st.markdown(f'<p style="{FLB}">ANNÉE</p>', unsafe_allow_html=True)
        st.selectbox("yr", ["Toutes"] + [str(y) for y in years_all],
                     label_visibility="collapsed", key="sel_annee")
    with c6:
        st.markdown(f'<p style="{FLB}">&nbsp;</p>', unsafe_allow_html=True)
        if st.button("Appliquer", type="primary", use_container_width=True, key="fl_apply"):
            st.cache_data.clear()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — VUE D'ENSEMBLE
# ══════════════════════════════════════════════════════════════════════════════
def page_overview(f):
    # ── KPIs
    kpi_df = q(f"""
        SELECT COUNT(fr.rental_id) AS nb, COALESCE(SUM(fr.amount),0) AS ca,
               COALESCE(AVG(fr.amount),0) AS ca_moy, COALESCE(AVG(fr.rental_duration),0) AS dur,
               SUM(CASE WHEN fr.rental_duration > f.duree_autorisee THEN 1 ELSE 0 END) AS retards,
               COALESCE(SUM(CASE WHEN fr.rental_duration > f.duree_autorisee
                   THEN fr.rental_duration - f.duree_autorisee ELSE 0 END)*fr.amount/NULLIF(fr.rental_duration,0),0) AS penalites,
               COUNT(DISTINCT fr.customer_key) AS clients, COUNT(DISTINCT fr.film_key) AS films
        FROM fact_rental fr
        JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_date d ON fr.date_key=d.date_key
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
    """)
    r = kpi_df.iloc[0]
    nb     = safe(r['nb'], int)
    ca     = safe(r['ca'])
    ca_moy = safe(r['ca_moy'])
    dur    = safe(r['dur'])
    retards= safe(r['retards'], int)
    clients= safe(r['clients'], int)
    films  = safe(r['films'], int)
    taux_r = round(retards*100/max(nb,1), 1)

    # Simple penalty estimate: total amount from late rentals
    pen_df = q(f"""
        SELECT COALESCE(SUM(fr.amount),0) AS pen, COUNT(*) AS cnt
        FROM fact_rental fr JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_date d ON fr.date_key=d.date_key
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        WHERE fr.rental_duration > f.duree_autorisee AND {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
    """)
    pen_total = safe(pen_df['pen'].iloc[0])
    pen_cnt   = safe(pen_df['cnt'].iloc[0], int)

    # Q4 occupancy
    yr_q4 = f.get('year') or load_years()[-1]
    occ_df = q(f"""
        SELECT COUNT(DISTINCT f2.film_key) AS tot, COUNT(DISTINCT fr2.film_key) AS lou
        FROM dim_film f2
        LEFT JOIN fact_rental fr2 ON f2.film_key=fr2.film_key
        LEFT JOIN dim_date d2 ON fr2.date_key=d2.date_key AND d2.trimestre=4 AND d2.annee={yr_q4}
    """)
    tot_films = safe(occ_df['tot'].iloc[0], int, 1000)
    lou_films = safe(occ_df['lou'].iloc[0], int)
    taux_occ  = round(lou_films*100/max(tot_films,1), 1)

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
    kpi(c1, "Chiffre d'affaires",   f"${ca:,.2f}",     f"Panier moy. ${ca_moy:.2f}", "#10b981")
    kpi(c2, "Nb locations",         f"{nb:,}",          f"Films rendus",              NAVY)
    kpi(c3, "Durée moyenne",        f"{dur:.1f} j",     f"Par transaction",           "#8b5cf6")
    kpi(c4, "Pénalités (retards)",  f"${pen_total:,.0f}", f"{pen_cnt:,} retards",     DANGER)
    kpi(c5, "Taux retard",          f"{taux_r}%",       f"{retards:,} locations",     "#f97316")
    kpi(c6, "Clients actifs",       f"{clients:,}",     f"Sur 599 total",             "#06b6d4")
    kpi(c7, "Films loués",          f"{films:,}",       f"Sur 1 000 inventaire",      GOLD)
    kpi(c8, "Occupation Q4",        f"{taux_occ}%",     f"{yr_q4} — T4",             "#64748b")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Row 1 : Revenus mensuels + Segments clients
    c_left, c_right = st.columns([3, 1])

    with c_left:
        section("Revenus mensuels", "CA & pénalités mois par mois")
        df_rev = q(f"""
            SELECT d.mois, d.libelle_mois,
                   COALESCE(SUM(fr.amount),0) AS ca,
                   COALESCE(SUM(CASE WHEN fr.rental_duration>f.duree_autorisee THEN fr.amount ELSE 0 END),0) AS pen
            FROM fact_rental fr
            JOIN dim_film f ON fr.film_key=f.film_key
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
            GROUP BY d.mois, d.libelle_mois ORDER BY d.mois
        """)
        if not df_rev.empty:
            df_rev['ca']  = pd.to_numeric(df_rev['ca'],  errors='coerce').fillna(0)
            df_rev['pen'] = pd.to_numeric(df_rev['pen'], errors='coerce').fillna(0)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_rev['libelle_mois'], y=df_rev['ca'],
                name='CA', line=dict(color=NAVY, width=2.5),
                mode='lines+markers', marker=dict(size=7, color=NAVY)))
            fig.add_trace(go.Scatter(x=df_rev['libelle_mois'], y=df_rev['pen'],
                name='Pénalités', line=dict(color=DANGER, width=2, dash='dot'),
                mode='lines+markers', marker=dict(size=6, color=DANGER)))
            lay(fig, 280, legend=dict(orientation='h', y=1.05, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
            st.plotly_chart(fig, use_container_width=True)

    with c_right:
        section("Segments clients", "Répartition fidélité")
        df_seg = q("SELECT segment, COUNT(*) AS nb FROM dim_customer GROUP BY segment ORDER BY nb DESC")
        if not df_seg.empty:
            df_seg['nb'] = pd.to_numeric(df_seg['nb'], errors='coerce').fillna(0)
            fig_s = px.pie(df_seg, values='nb', names='segment', hole=0.6,
                color_discrete_sequence=[NAVY, GOLD, SUCCESS])
            fig_s.update_traces(textfont_color="#fff", textinfo="label+value")
            lay(fig_s, 280, legend=dict(orientation='h', y=-0.1, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
            st.plotly_chart(fig_s, use_container_width=True)

    # ── Row 2 : Durées + CA trimestriel
    c_d, c_t = st.columns(2)

    with c_d:
        section("Distribution des durées de location")
        df_dur = q(f"""
            SELECT fr.rental_duration AS dur, COUNT(*) AS nb
            FROM fact_rental fr
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE fr.rental_duration IS NOT NULL AND fr.rental_duration>0
              AND fr.rental_duration<=30 AND {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
            GROUP BY fr.rental_duration ORDER BY fr.rental_duration
        """)
        if not df_dur.empty:
            df_dur['dur'] = pd.to_numeric(df_dur['dur'], errors='coerce')
            fig_d = px.bar(df_dur, x='dur', y='nb',
                color='nb', color_continuous_scale=[BORDER, NAVY],
                labels={'dur':'Durée (j)', 'nb':'Nb locations'})
            lay(fig_d, 250, coloraxis_showscale=False)
            st.plotly_chart(fig_d, use_container_width=True)

    with c_t:
        section("CA par trimestre", "Agrégation trimestrielle")
        df_trim = q(f"""
            SELECT d.trimestre, COALESCE(SUM(fr.amount),0) AS ca
            FROM fact_rental fr
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
            GROUP BY d.trimestre ORDER BY d.trimestre
        """)
        if not df_trim.empty:
            df_trim['ca'] = pd.to_numeric(df_trim['ca'], errors='coerce').fillna(0)
            df_trim['lbl'] = df_trim['trimestre'].apply(lambda x: f"T{x}")
            fig_t = px.bar(df_trim, x='lbl', y='ca', color_discrete_sequence=[GOLD],
                text=df_trim['ca'].apply(lambda x: f"${float(x):,.0f}"),
                labels={'lbl':'', 'ca':'CA ($)'})
            fig_t.update_traces(textposition='outside', textfont_color=NAVY, marker_color=GOLD)
            lay(fig_t, 250)
            st.plotly_chart(fig_t, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — ANALYSE TEMPORELLE
# ══════════════════════════════════════════════════════════════════════════════
def page_temporal(f):
    # CA mensuel top 5 catégories
    section("Évolution mensuelle du CA — Top 5 catégories", "Analyse 1 — Roll-up mensuel × catégories")
    df_ca = q(f"""
        SELECT d.mois, d.libelle_mois, f.categorie,
               COALESCE(SUM(fr.amount),0) AS ca
        FROM fact_rental fr
        JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_date d ON fr.date_key=d.date_key
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
        GROUP BY d.mois, d.libelle_mois, f.categorie ORDER BY d.mois
    """)
    if not df_ca.empty:
        df_ca['ca'] = pd.to_numeric(df_ca['ca'], errors='coerce').fillna(0)
        top5 = df_ca.groupby('categorie')['ca'].sum().sort_values(ascending=False).head(5).index.tolist()
        fig = px.bar(df_ca[df_ca['categorie'].isin(top5)], x='libelle_mois', y='ca',
            color='categorie', barmode='group', color_discrete_sequence=COLORS,
            labels={'libelle_mois':'Mois','ca':'CA ($)','categorie':'Catégorie'})
        lay(fig, 300, legend=dict(orientation='h', y=1.05, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
        st.plotly_chart(fig, use_container_width=True)

    # Courbe cumulative
    section("Courbe cumulative du CA", "Progression mensuelle et cumul annuel")
    df_cum = q(f"""
        SELECT d.mois, d.libelle_mois, COALESCE(SUM(fr.amount),0) AS ca
        FROM fact_rental fr
        JOIN dim_date d ON fr.date_key=d.date_key
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
        GROUP BY d.mois, d.libelle_mois ORDER BY d.mois
    """)
    if not df_cum.empty:
        df_cum['ca'] = pd.to_numeric(df_cum['ca'], errors='coerce').fillna(0)
        df_cum['cumul'] = df_cum['ca'].cumsum()
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Bar(x=df_cum['libelle_mois'], y=df_cum['ca'],
            name='CA mensuel', marker_color=f"rgba(0,63,127,0.2)",
            marker_line_color=NAVY, marker_line_width=1), secondary_y=False)
        fig3.add_trace(go.Scatter(x=df_cum['libelle_mois'], y=df_cum['cumul'],
            name='Cumul', line=dict(color=GOLD, width=3),
            mode='lines+markers', marker=dict(size=8, color=GOLD, line=dict(color=CARD, width=2))),
            secondary_y=True)
        fig3.update_layout(**PL, height=280,
            legend=dict(orientation='h', y=1.05, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
        fig3.update_xaxes(showgrid=False, color="#94a3b8")
        fig3.update_yaxes(gridcolor="#f1f5f9", color="#94a3b8", secondary_y=False)
        fig3.update_yaxes(showgrid=False, color=GOLD, secondary_y=True)
        st.plotly_chart(fig3, use_container_width=True)

    # Heatmap mois × catégorie
    c_h, c_tab = st.columns([3, 2])
    with c_h:
        section("Heatmap mois × catégorie", "Volume de locations")
        df_hm = q(f"""
            SELECT d.libelle_mois, d.mois, f.categorie, COUNT(*) AS nb
            FROM fact_rental fr
            JOIN dim_film f ON fr.film_key=f.film_key
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
            GROUP BY d.mois, d.libelle_mois, f.categorie ORDER BY d.mois
        """)
        if not df_hm.empty:
            df_hm['nb'] = pd.to_numeric(df_hm['nb'], errors='coerce').fillna(0)
            piv = df_hm.pivot_table(index='libelle_mois', columns='categorie', values='nb', fill_value=0)
            fig_h = px.imshow(piv, color_continuous_scale=[BORDER, NAVY], aspect='auto',
                labels=dict(x='Catégorie', y='Mois', color='Locations'))
            fig_h.update_layout(**PL, height=350,
                coloraxis_colorbar=dict(tickfont_color=MUTED, title_font_color=NAVY))
            fig_h.update_xaxes(color=TEXT, tickfont_color=MUTED)
            fig_h.update_yaxes(color=TEXT, tickfont_color=MUTED, showgrid=False)
            st.plotly_chart(fig_h, use_container_width=True)

    with c_tab:
        section("Récapitulatif mensuel")
        df_tab = q(f"""
            SELECT d.libelle_mois AS Mois, COUNT(*) AS Locations,
                   ROUND(COALESCE(SUM(fr.amount),0),2) AS CA,
                   ROUND(COALESCE(AVG(fr.amount),0),2) AS "CA moy."
            FROM fact_rental fr
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
            GROUP BY d.mois, d.libelle_mois ORDER BY d.mois
        """)
        if not df_tab.empty:
            for col in ['Locations','CA','CA moy.']:
                df_tab[col] = pd.to_numeric(df_tab[col], errors='coerce').fillna(0)
        st.dataframe(df_tab, use_container_width=True, height=360)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PERFORMANCES
# ══════════════════════════════════════════════════════════════════════════════
def page_performances(f):
    c_a, c_b = st.columns(2)

    with c_a:
        section("Top 15 films — CA total")
        df_films = q(f"""
            SELECT f.titre, f.categorie, COALESCE(SUM(fr.amount),0) AS ca
            FROM fact_rental fr
            JOIN dim_film f ON fr.film_key=f.film_key
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
            GROUP BY f.titre, f.categorie ORDER BY ca DESC LIMIT 15
        """)
        if not df_films.empty:
            df_films['ca'] = pd.to_numeric(df_films['ca'], errors='coerce').fillna(0)
            fig = px.bar(df_films, x='ca', y='titre', orientation='h',
                color='categorie', color_discrete_sequence=COLORS,
                labels={'ca':'CA ($)','titre':''})
            lay(fig, 400, legend=dict(orientation='h', y=1.05, bgcolor="rgba(0,0,0,0)", font_color=TEXT),
                yaxis=dict(categoryorder='total ascending', color=TEXT, tickfont_color=TEXT, showgrid=False))
            st.plotly_chart(fig, use_container_width=True)

    with c_b:
        section("Top 15 films — Jours de retard", "Analyse 2")
        df_ret = q(f"""
            SELECT f.titre, f.categorie,
                   SUM(fr.rental_duration - f.duree_autorisee) AS jr
            FROM fact_rental fr
            JOIN dim_film f ON fr.film_key=f.film_key
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE fr.rental_duration > f.duree_autorisee
              AND {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
            GROUP BY f.titre, f.categorie ORDER BY jr DESC LIMIT 15
        """)
        if not df_ret.empty:
            df_ret['jr'] = pd.to_numeric(df_ret['jr'], errors='coerce').fillna(0)
            fig2 = px.bar(df_ret, x='jr', y='titre', orientation='h',
                color='jr', color_continuous_scale=[BORDER, DANGER],
                labels={'jr':'Jours retard','titre':''})
            lay(fig2, 400, coloraxis_showscale=False,
                yaxis=dict(categoryorder='total ascending', color=TEXT, tickfont_color=TEXT, showgrid=False))
            st.plotly_chart(fig2, use_container_width=True)

    c_c, c_d = st.columns(2)
    with c_c:
        section("Volume par catégorie")
        df_cat = q(f"""
            SELECT f.categorie, COUNT(*) AS nb, COALESCE(SUM(fr.amount),0) AS ca
            FROM fact_rental fr
            JOIN dim_film f ON fr.film_key=f.film_key
            JOIN dim_date d ON fr.date_key=d.date_key
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
            GROUP BY f.categorie ORDER BY nb DESC
        """)
        if not df_cat.empty:
            df_cat['nb'] = pd.to_numeric(df_cat['nb'], errors='coerce').fillna(0)
            fig3 = px.bar(df_cat, x='nb', y='categorie', orientation='h',
                color='nb', color_continuous_scale=[BORDER, NAVY], labels={'nb':'Locations','categorie':''})
            lay(fig3, 370, coloraxis_showscale=False,
                yaxis=dict(categoryorder='total ascending', color=TEXT, tickfont_color=TEXT, showgrid=False))
            st.plotly_chart(fig3, use_container_width=True)

    with c_d:
        section("Part du CA par catégorie")
        if not df_cat.empty:
            df_cat['ca'] = pd.to_numeric(df_cat['ca'], errors='coerce').fillna(0)
            fig4 = px.pie(df_cat, values='ca', names='categorie', hole=0.55,
                color_discrete_sequence=COLORS)
            fig4.update_traces(textfont_color=CARD)
            lay(fig4, 370, legend=dict(orientation='h', y=-0.15, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
            st.plotly_chart(fig4, use_container_width=True)

    section("Performance par rating")
    df_rat = q(f"""
        SELECT f.rating, COUNT(*) AS nb, COALESCE(SUM(fr.amount),0) AS ca
        FROM fact_rental fr
        JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_date d ON fr.date_key=d.date_key
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
        GROUP BY f.rating ORDER BY nb DESC
    """)
    if not df_rat.empty:
        df_rat['nb'] = pd.to_numeric(df_rat['nb'], errors='coerce').fillna(0)
        df_rat['ca'] = pd.to_numeric(df_rat['ca'], errors='coerce').fillna(0)
        for col, (_, row) in zip(st.columns(len(df_rat)), df_rat.iterrows()):
            with col:
                st.metric(f"Rating {row['rating']}", f"{int(row['nb']):,}", f"{float(row['ca']):,.0f} $")

    section("Taux d'occupation inventaire Q4", "Films jamais loués au dernier trimestre")
    yr_q4 = f.get('year') or load_years()[-1]
    df_occ = q(f"SELECT COUNT(DISTINCT f2.film_key) AS tot, COUNT(DISTINCT fr2.film_key) AS lou FROM dim_film f2 LEFT JOIN fact_rental fr2 ON f2.film_key=fr2.film_key LEFT JOIN dim_date d2 ON fr2.date_key=d2.date_key AND d2.trimestre=4 AND d2.annee={yr_q4}")
    tot = safe(df_occ['tot'].iloc[0], int, 1000)
    lou = safe(df_occ['lou'].iloc[0], int)
    c_pie, c_tbl = st.columns([1, 2])
    with c_pie:
        fig_o = go.Figure(go.Pie(
            labels=[f'Loués ({lou})', f'Non loués ({tot-lou})'],
            values=[lou, tot-lou], hole=0.65,
            marker=dict(colors=[NAVY, DANGER], line=dict(color=CARD, width=3))))
        fig_o.update_traces(textfont_color=CARD)
        lay(fig_o, 250, legend=dict(orientation='h', y=-0.1, bgcolor="rgba(0,0,0,0)", font_color=TEXT),
            annotations=[dict(text=f"<b>{round(lou*100/tot,1)}%</b>",
                x=0.5, y=0.5, font_size=18, font_color=NAVY, showarrow=False)])
        st.plotly_chart(fig_o, use_container_width=True)
    with c_tbl:
        df_nl = q(f"""
            SELECT f.titre, f.categorie, f.rating FROM dim_film f
            WHERE f.film_key NOT IN (
                SELECT DISTINCT fr.film_key FROM fact_rental fr
                JOIN dim_date d ON fr.date_key=d.date_key
                WHERE d.trimestre=4 AND d.annee={yr_q4})
            ORDER BY f.categorie, f.titre LIMIT 40
        """)
        st.caption(f"📋 {len(df_nl)} films jamais loués — Q4 {yr_q4}")
        st.dataframe(df_nl, use_container_width=True, height=220)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
def page_clients(f):
    c_seg, c_top = st.columns(2)

    with c_seg:
        section("Segmentation clientèle", "Fidèle / Régulier / Occasionnel")
        df_seg = q("SELECT segment, COUNT(*) AS nb FROM dim_customer GROUP BY segment ORDER BY nb DESC")
        if not df_seg.empty:
            df_seg['nb'] = pd.to_numeric(df_seg['nb'], errors='coerce').fillna(0)
            fig_s = px.pie(df_seg, values='nb', names='segment', hole=0.6,
                color_discrete_sequence=[NAVY, GOLD, SUCCESS])
            fig_s.update_traces(textfont_color=CARD, textinfo="label+value")
            lay(fig_s, 270, legend=dict(orientation='h', y=-0.1, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
            st.plotly_chart(fig_s, use_container_width=True)
            for _, row in df_seg.iterrows():
                pct = round(float(row['nb'])*100/599, 1)
                w_bar = int(pct)
                st.markdown(f"""<div style="display:flex;align-items:center;gap:0.8rem;
                    padding:0.4rem 0;border-bottom:1px solid {BORDER}">
                    <span style="width:90px;font-size:0.8rem;color:{TEXT};font-weight:500">{row['segment']}</span>
                    <div style="flex:1;background:{BG};border-radius:4px;height:6px;overflow:hidden">
                        <div style="width:{w_bar}%;background:{NAVY};height:100%;border-radius:4px"></div></div>
                    <span style="font-size:0.78rem;color:{MUTED};width:80px;text-align:right">
                        {int(row['nb'])} — {pct}%</span>
                </div>""", unsafe_allow_html=True)

    with c_top:
        section("Top 20 clients — CA généré")
        df_tc = q(f"""
            SELECT c.prenom || ' ' || c.nom AS client, c.segment, c.pays,
                   COUNT(*) AS locations, COALESCE(SUM(fr.amount),0) AS ca
            FROM fact_rental fr
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            JOIN dim_date d ON fr.date_key=d.date_key
            WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
            GROUP BY c.customer_key, c.prenom, c.nom, c.segment, c.pays
            ORDER BY ca DESC LIMIT 20
        """)
        if not df_tc.empty:
            df_tc['ca'] = pd.to_numeric(df_tc['ca'], errors='coerce').fillna(0)
        st.dataframe(df_tc, use_container_width=True, height=370)

    section("CA moyen par segment × catégorie", "Comportement d'achat selon la fidélité")
    df_sc = q(f"""
        SELECT c.segment, f.categorie, COALESCE(AVG(fr.amount),0) AS ca_moy
        FROM fact_rental fr
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_date d ON fr.date_key=d.date_key
        WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
        GROUP BY c.segment, f.categorie ORDER BY c.segment, ca_moy DESC
    """)
    if not df_sc.empty:
        df_sc['ca_moy'] = pd.to_numeric(df_sc['ca_moy'], errors='coerce').fillna(0)
        fig_sc = px.bar(df_sc, x='categorie', y='ca_moy', color='segment', barmode='group',
            color_discrete_sequence=[NAVY, GOLD, SUCCESS],
            labels={'categorie':'Catégorie','ca_moy':'CA moyen ($)','segment':'Segment'})
        lay(fig_sc, 260, legend=dict(orientation='h', y=1.05, bgcolor="rgba(0,0,0,0)", font_color=TEXT))
        st.plotly_chart(fig_sc, use_container_width=True)

    c_fr, c_pp = st.columns(2)
    with c_fr:
        section("Fréquence de location par client")
        df_freq = q(f"""
            SELECT nb, COUNT(*) AS clients FROM (
                SELECT c.customer_key, COUNT(*) AS nb
                FROM fact_rental fr
                JOIN dim_customer c ON fr.customer_key=c.customer_key
                JOIN dim_date d ON fr.date_key=d.date_key
                WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
                GROUP BY c.customer_key) sub
            GROUP BY nb ORDER BY nb
        """)
        if not df_freq.empty:
            df_freq['nb'] = pd.to_numeric(df_freq['nb'], errors='coerce')
            df_freq['clients'] = pd.to_numeric(df_freq['clients'], errors='coerce')
            fig_f = px.bar(df_freq, x='nb', y='clients',
                color='clients', color_continuous_scale=[BORDER, NAVY],
                labels={'nb':'Nb locations','clients':'Nb clients'})
            lay(fig_f, 250, coloraxis_showscale=False)
            st.plotly_chart(fig_f, use_container_width=True)

    with c_pp:
        section("Top 15 pays — Clients")
        df_pp = q(f"""
            SELECT c.pays, COUNT(DISTINCT c.customer_key) AS clients
            FROM fact_rental fr
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            JOIN dim_date d ON fr.date_key=d.date_key
            WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
            GROUP BY c.pays ORDER BY clients DESC LIMIT 15
        """)
        if not df_pp.empty:
            df_pp['clients'] = pd.to_numeric(df_pp['clients'], errors='coerce')
            fig_pp = px.bar(df_pp, x='clients', y='pays', orientation='h',
                color='clients', color_continuous_scale=[BORDER, NAVY],
                labels={'clients':'Clients','pays':''})
            lay(fig_pp, 250, coloraxis_showscale=False,
                yaxis=dict(categoryorder='total ascending', color=TEXT, tickfont_color=TEXT, showgrid=False))
            st.plotly_chart(fig_pp, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — GÉOGRAPHIE
# ══════════════════════════════════════════════════════════════════════════════
def page_geo(f):
    section("Analyse 3 — Corrélation pays × catégorie", "Top 20 pays — Heatmap des locations")
    df_geo = q(f"""
        SELECT c.pays, f.categorie, COUNT(*) AS nb
        FROM fact_rental fr
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_date d ON fr.date_key=d.date_key
        WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
        GROUP BY c.pays, f.categorie
    """)
    if not df_geo.empty:
        df_geo['nb'] = pd.to_numeric(df_geo['nb'], errors='coerce').fillna(0)
        top20 = df_geo.groupby('pays')['nb'].sum().sort_values(ascending=False).head(20).index.tolist()
        df_heat = df_geo[df_geo['pays'].isin(top20)].pivot_table(
            index='pays', columns='categorie', values='nb', fill_value=0)
        fig_h = px.imshow(df_heat, color_continuous_scale=[BORDER, NAVY], aspect='auto',
            labels=dict(x='Catégorie', y='Pays', color='Locations'))
        fig_h.update_layout(**PL, height=480,
            coloraxis_colorbar=dict(tickfont_color=MUTED, title_font_color=NAVY))
        fig_h.update_xaxes(color=TEXT, tickfont_color=MUTED)
        fig_h.update_yaxes(color=TEXT, tickfont_color=MUTED, showgrid=False)
        st.plotly_chart(fig_h, use_container_width=True)

    c_g1, c_g2 = st.columns(2)
    with c_g1:
        section("Top 15 pays — CA total")
        df_pca = q(f"""
            SELECT c.pays, COALESCE(SUM(fr.amount),0) AS ca, COUNT(*) AS nb
            FROM fact_rental fr
            JOIN dim_customer c ON fr.customer_key=c.customer_key
            JOIN dim_date d ON fr.date_key=d.date_key
            WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
            GROUP BY c.pays ORDER BY ca DESC LIMIT 15
        """)
        if not df_pca.empty:
            df_pca['ca'] = pd.to_numeric(df_pca['ca'], errors='coerce').fillna(0)
            fig_p = px.bar(df_pca, x='ca', y='pays', orientation='h',
                color='ca', color_continuous_scale=[BORDER, NAVY], labels={'ca':'CA ($)','pays':''})
            lay(fig_p, 360, coloraxis_showscale=False,
                yaxis=dict(categoryorder='total ascending', color=TEXT, tickfont_color=TEXT, showgrid=False))
            st.plotly_chart(fig_p, use_container_width=True)

    with c_g2:
        section("Catégorie favorite par pays")
        if not df_geo.empty:
            df_fav = df_geo.loc[df_geo.groupby('pays')['nb'].idxmax()].sort_values('nb', ascending=False).head(20)
            fig_fav = px.bar(df_fav, x='nb', y='pays', color='categorie',
                orientation='h', color_discrete_sequence=COLORS,
                labels={'nb':'Locations','pays':'','categorie':'Catégorie fav.'})
            lay(fig_fav, 360, legend=dict(orientation='h', y=1.05, bgcolor="rgba(0,0,0,0)", font_color=TEXT),
                yaxis=dict(categoryorder='total ascending', color=TEXT, tickfont_color=TEXT, showgrid=False))
            st.plotly_chart(fig_fav, use_container_width=True)

    section("Tableau complet — Tous les pays")
    df_pf = q(f"""
        SELECT c.pays, COUNT(DISTINCT c.customer_key) AS clients,
               COUNT(*) AS locations,
               ROUND(COALESCE(SUM(fr.amount),0),2) AS ca_total,
               ROUND(COALESCE(AVG(fr.amount),0),2) AS ca_moyen
        FROM fact_rental fr
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        JOIN dim_date d ON fr.date_key=d.date_key
        WHERE {W(f, cat=False, pays=True, store=True, seg=True, yr=True)}
        GROUP BY c.pays ORDER BY ca_total DESC
    """)
    if not df_pf.empty:
        for col in ['ca_total','ca_moyen','clients','locations']:
            df_pf[col] = pd.to_numeric(df_pf[col], errors='coerce').fillna(0)
    c_tbl, c_dl = st.columns([4, 1])
    with c_tbl:
        st.dataframe(df_pf, use_container_width=True, height=280)
    with c_dl:
        if not df_pf.empty:
            csv = df_pf.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("⬇️ CSV", data=csv, file_name="geo_pays.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — DONNÉES BRUTES
# ══════════════════════════════════════════════════════════════════════════════
def page_raw(f):
    nb_rows = st.slider("Lignes à afficher", 50, 1000, 200, 50)
    df_raw = q(f"""
        SELECT fr.rental_id,
               d.date_complete AS date, d.libelle_mois AS mois, d.trimestre,
               c.prenom || ' ' || c.nom AS client, c.segment, c.pays,
               f.titre AS film, f.categorie, f.rating,
               s.ville AS magasin, fr.rental_duration AS duree_j, fr.amount AS montant
        FROM fact_rental fr
        JOIN dim_date d ON fr.date_key=d.date_key
        JOIN dim_customer c ON fr.customer_key=c.customer_key
        JOIN dim_film f ON fr.film_key=f.film_key
        JOIN dim_store s ON fr.store_key=s.store_key
        WHERE {W(f, cat=True, pays=True, store=True, seg=True, yr=True)}
        ORDER BY fr.rental_id DESC LIMIT {nb_rows}
    """)
    if not df_raw.empty:
        df_raw['montant'] = pd.to_numeric(df_raw['montant'], errors='coerce').fillna(0)
    st.dataframe(df_raw, use_container_width=True, height=450)
    if not df_raw.empty:
        csv = df_raw.to_csv(index=False, encoding='utf-8-sig')
        yr_label = f.get('year') or "all"
        st.download_button("⬇️ Télécharger CSV", data=csv,
            file_name=f"sakila360_{yr_label}.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTING
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state.page
icon, subtitle = PAGES[page]

page_header(page, subtitle)
render_filter_bar()
f = get_flt()

if   page == "Vue d'ensemble":     page_overview(f)
elif page == "Analyse temporelle": page_temporal(f)
elif page == "Performances":       page_performances(f)
elif page == "Clients":            page_clients(f)
elif page == "Géographie":         page_geo(f)
elif page == "Données brutes":     page_raw(f)

st.markdown(f"""<div style="text-align:center;color:{MUTED};font-size:0.7rem;
    margin-top:3rem;padding-top:1rem;border-top:1px solid {BORDER}">
    Sakila 360 · ISSEA 2025-2026 ·
    AMBASSA Sammuel Lumière · AYONTA NDJOUTSE Vanelle · BAMOGO Karim ·
    Encadrant : <span style="color:{GOLD}">M. TAPAMO</span>
</div>""", unsafe_allow_html=True)
