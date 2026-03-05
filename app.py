
import streamlit as st
import pandas as pd
import json
import io
import zipfile
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="DDJJ Transporte", layout="wide")

# =============================
# CONTROL DE SESIÓN
# =============================

if "login_ok" not in st.session_state:
    st.session_state.login_ok = False

# =============================
# PANTALLA DE LOGIN
# =============================

if not st.session_state.login_ok:

    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(135deg, #1E2F4F 0%, #2F4B7C 100%);
    }

    .login-wrapper {
        text-align: center;
        margin-top: 40px;
    }

    .title {
        color: #F1F4FA;
        font-size: 24px;
        font-weight: 600;
        margin-top: 15px;
    }

    .subtitle {
        color: #C9D4EA;
        font-size: 14px;
        margin-bottom: 35px;
    }

    .login-card {
        background-color: #FFFFFF;
        padding: 35px;
        border-radius: 15px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.25);
        max-width: 460px;
        margin: auto;
    }

    label {
        font-size: 13px !important;
        font-weight: 500;
        color: #2F4B7C !important;
    }

    input {
        font-size: 14px !important;
    }

    .stButton>button {
        background-color: #4C6FBF;
        color: white;
        border-radius: 10px;
        height: 45px;
        font-weight: 500;
        width: 100%;
    }

    .stButton>button:hover {
        background-color: #3958A8;
    }

    .footer {
        text-align: center;
        color: #BFC8DA;
        margin-top: 30px;
        font-size: 13px;
    }

    </style>
    """, unsafe_allow_html=True)

    # Logo ERSeP
    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)
    st.image("logo-ersep.jpg", width=220)
    st.markdown("<div class='title'>Sistema de DDJJ — Transporte Interurbano</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Ente Regulador de los Servicios Públicos · Provincia de Córdoba</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-card'>", unsafe_allow_html=True)

    cuit = st.text_input("CUIT DE LA EMPRESA")
    password = st.text_input("CONTRASEÑA", type="password")

    if st.button("Ingresar al sistema →"):
        st.session_state.login_ok = True
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='footer'>Subdirección Jurisdicción de Costos y Tarifas · ERSeP 2026</div>", unsafe_allow_html=True)

    st.stop()

# =============================
# ESTILO SISTEMA INTERNO (GRIS)
# =============================

st.markdown("""
<style>

.stApp {
    background-color: #F4F6F9 !important;
}

h1 {
    font-size: 22px;
    font-weight: 600;
    color: #1F4E79;
}

h2, h3 {
    font-size: 18px;
    font-weight: 500;
    color: #2F4B7C;
}

p, div {
    font-size: 14px;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)

# =============================
# AQUI EMPIEZA TU SISTEMA REAL
# =============================

st.title("Panel de Gestión DDJJ Transporte")
