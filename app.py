"""
ERSeP – DDJJ Transporte Interurbano
Sistema de Declaración Jurada de Producción, Costos y Documentación
Subdirección Jurisdicción de Costos y Tarifas – Provincia de Córdoba
"""

import streamlit as st
import pandas as pd
import json
import io
import zipfile
from pathlib import Path
from datetime import datetime

# ─── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# ─── Config página ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERSeP – DDJJ Transporte Interurbano",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html,body,[class*="css"]{font-family:'Inter',sans-serif !important}
  .main .block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1200px}
  h1,h2,h3{color:#1F3864 !important}
  .stButton>button{border-radius:8px !important;font-weight:600 !important}
  .stTabs [data-baseweb="tab"]{font-weight:600 !important}
  .stTabs [aria-selected="true"]{color:#2E75B6 !important}
  div[data-testid="metric-container"]{
    background:#f0f4fc;border-radius:10px;padding:12px 16px;
    border-top:3px solid #2E75B6;
  }
</style>
""", unsafe_allow_html=True)

# ─── Constantes ───────────────────────────────────────────────────────────────
MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
AÑOS  = [2024, 2025, 2026]

EMPRESAS = {
    "30-54633555-7": {"rs":"COTA LA CALERA LTDA.",                  "pass":"cota123"},
    "30-70730781-8": {"rs":"EMPRESA SARMIENTO S.R.L.",              "pass":"sarm123"},
    "30-67871434-4": {"rs":"EMPRENDIMIENTOS S.R.L. (FONO BUS)",     "pass":"fono123"},
    "30-64484750-7": {"rs":"EXCURSIONES SIERRAS DE CALAMUCHITA",    "pass":"sier123"},
    "30-54624472-1": {"rs":"COATA S.A.",                            "pass":"coat123"},
}

ADMIN = {"user":"ERSEP", "pass":"ersep2026"}

DOCS_CONFIG = [
    {"id":"a1","sec":"A","label":"A1 – Facturas de combustible",
     "hint":"Facturas del período: nº, fecha, tipo (gasoil/GNC), litros, precio unitario.",
     "ext":["pdf"]},
    {"id":"a2","sec":"A","label":"A2 – Remitos de carga",
     "hint":"Planilla por evento: fecha, patente, proveedor/punto de carga, litros cargados.",
     "ext":["xlsx","xls","csv"]},
    {"id":"a3","sec":"A","label":"A3 – Padrón de flota activa",
     "hint":"Listado: patente, marca, modelo, año, categoría vehicular, tipo combustible, cap. tanque.",
     "ext":["xlsx","xls","csv"]},
    {"id":"b1","sec":"B","label":"B1 – Libro de Sueldos Digital (LSD)",
     "hint":"Apertura individual por CUIL: categoría, función, remuneración, adicionales, hs extra.",
     "ext":["xlsx","xls","csv"]},
    {"id":"b2","sec":"B","label":"B2 – Formulario F.931 (AFIP)",
     "hint":"Declaración jurada del período. Validación masa salarial y contribuciones patronales.",
     "ext":["pdf"]},
]

# ─── Utils ────────────────────────────────────────────────────────────────────
def mes_str(año, mes):
    return f"{MESES[int(mes)-1]} {año}"

def periodo_key(año, mes):
    return f"{año}-{str(mes).zfill(2)}"

def ddjj_path(cuit, año, mes):
    return DATA_DIR / f"ddjj_{cuit.replace('-','_')}_{periodo_key(año,mes)}.json"

def upload_dir(cuit, año, mes):
    d = UPLOAD_DIR / cuit.replace("-","_") / periodo_key(año, mes)
    d.mkdir(parents=True, exist_ok=True)
    return d

def load_ddjj(cuit, año, mes):
    p = ddjj_path(cuit, año, mes)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None

def save_ddjj(data, cuit, año, mes):
    data["cuit"] = cuit
    data["año"]  = int(año)
    data["mes"]  = int(mes)
    data.setdefault("rs", EMPRESAS.get(cuit, {}).get("rs", ""))
    p = ddjj_path(cuit, año, mes)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_all_ddjj():
    out = []
    for f in DATA_DIR.glob("ddjj_*.json"):
        try:
            with open(f, encoding="utf-8") as fp:
                out.append(json.load(fp))
        except Exception:
            pass
    return out

def empty_ddjj():
    return {
        "lineas":[{"linea":"","tramo":"","kmT":0,"svcs":0,"ing":0}],
        "vehiculosActivos":0, "choferes":0, "administrativos":0,
        "taller":0, "litrosCombustible":0,
        "documentos":{}, "estado":"borrador", "fechaEnvio":None,
    }

def calc_kpi(d):
    if not d:
        return {k:0 for k in ["km_total","ing_total","empleados","choferes",
                               "ing_km","chs_veh","empl_veh","km_veh","lts_veh","km_lts"]}
    lineas = d.get("lineas", [])
    km   = sum(float(l.get("kmT") or 0) * float(l.get("svcs") or 0) for l in lineas)
    ing  = sum(float(l.get("ing") or 0) for l in lineas)
    chs  = float(d.get("choferes") or 0)
    adm  = float(d.get("administrativos") or 0)
    tal  = float(d.get("taller") or 0)
    empl = chs + adm + tal
    vehs = float(d.get("vehiculosActivos") or 0)
    lts  = float(d.get("litrosCombustible") or 0)
    return {
        "km_total": km,  "ing_total": ing,
        "empleados": empl, "choferes": chs,
        "ing_km":   ing/km   if km   else 0,
        "chs_veh":  chs/vehs if vehs else 0,
        "empl_veh": empl/vehs if vehs else 0,
        "km_veh":   km/vehs  if vehs else 0,
        "lts_veh":  lts/vehs if vehs else 0,
        "km_lts":   km/lts   if lts  else 0,
    }

def fn(v, dec=0):
    try:
        v = float(v or 0)
        return f"{v:,.{dec}f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "-"

def fm(v): return f"$ {fn(v)}"

def export_excel_all(rows, periodo_str):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        wb  = writer.book
        hdr = wb.add_format({"bold":True,"bg_color":"#1F3864","font_color":"white","border":1,"font_size":10})
        nrm = wb.add_format({"border":1,"font_size":10})
        alt = wb.add_format({"border":1,"font_size":10,"bg_color":"#f0f4fc"})

        # Hoja 1 – Resumen
        ws = wb.add_worksheet("Resumen")
        ws.set_zoom(90)
        cols = ["Empresa","CUIT","Estado","Km Producidos","Ingresos ($)","Vehículos",
                "Choferes","Empleados Totales","Litros Combustible",
                "Ing/km","Chs/Veh","Empl/Veh","Km/Veh","Lts/Veh","Km/Ltro"]
        ws.write_row(0, 0, cols, hdr)
        ws.set_column(0,0,35); ws.set_column(1,1,16); ws.set_column(2,2,12); ws.set_column(3,14,14)
        for i, r in enumerate(rows):
            k = calc_kpi(r)
            fmt = nrm if i % 2 == 0 else alt
            ws.write_row(i+1, 0, [
                r.get("rs",""), r.get("cuit",""), r.get("estado","sin datos"),
                round(k["km_total"]), round(k["ing_total"]),
                r.get("vehiculosActivos",""), r.get("choferes",""),
                round(k["empleados"]) or "", r.get("litrosCombustible",""),
                round(k["ing_km"],2), round(k["chs_veh"],2), round(k["empl_veh"],2),
                round(k["km_veh"]), round(k["lts_veh"]), round(k["km_lts"],2),
            ], fmt)

        # Hoja 2 – Líneas
        ws2 = wb.add_worksheet("Líneas")
        ws2.set_zoom(90)
        cols2 = ["Empresa","CUIT","Línea","Tramo","Km/Trayecto","Servicios","Km Prod.","Ingresos ($)"]
        ws2.write_row(0,0,cols2,hdr)
        ws2.set_column(0,0,35); ws2.set_column(1,1,16); ws2.set_column(3,3,35)
        ri = 1
        for r in rows:
            for l in r.get("lineas",[]):
                km_p = float(l.get("kmT") or 0) * float(l.get("svcs") or 0)
                ws2.write_row(ri, 0, [
                    r.get("rs",""), r.get("cuit",""), l.get("linea",""),
                    l.get("tramo",""), l.get("kmT",""), l.get("svcs",""),
                    round(km_p), l.get("ing","")
                ], nrm if ri%2==0 else alt)
                ri += 1

        # Hoja 3 – Documentación
        ws3 = wb.add_worksheet("Documentación")
        ws3.set_zoom(90)
        cols3 = ["Empresa","CUIT","Documento","Archivo","Tamaño","Fecha adjunto"]
        ws3.write_row(0,0,cols3,hdr)
        ws3.set_column(0,0,35); ws3.set_column(1,1,16); ws3.set_column(2,2,28)
        ws3.set_column(3,3,30); ws3.set_column(4,5,15)
        ri = 1
        for r in rows:
            for dc in DOCS_CONFIG:
                meta = r.get("documentos",{}).get(dc["id"])
                ws3.write_row(ri, 0, [
                    r.get("rs",""), r.get("cuit",""), dc["label"],
                    meta["nombre"] if meta else "Sin adjuntar",
                    meta.get("tamaño","") if meta else "",
                    meta.get("fecha","") if meta else "",
                ], nrm if ri%2==0 else alt)
                ri += 1

    buf.seek(0)
    return buf

# ─── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "screen":"login", "user":None,
    "año":datetime.now().year, "mes":datetime.now().month,
    "ddjj": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

ss = st.session_state

# ─── Componentes UI ───────────────────────────────────────────────────────────
def header_bar():
    u = ss.user or {}
    label = u.get("rs","Panel Regulador") if u.get("tipo")=="empresa" else "Panel Regulador · ERSeP"
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div style="background:#1F3864;padding:12px 20px;border-radius:10px;
            margin-bottom:14px;display:flex;align-items:center;gap:14px">
          <div style="background:#fff;padding:4px 14px;border-radius:6px">
            <span style="color:#C1272D;font-weight:900;font-size:22px;letter-spacing:-1px">ERSeP</span>
          </div>
          <div>
            <div style="color:#fff;font-weight:700;font-size:14px">
              DDJJ – {label}
            </div>
            <div style="color:#94b8d8;font-size:12px">
              Sistema de Declaración Jurada · {mes_str(ss.año, ss.mes)}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Salir", use_container_width=True):
            ss.screen = "login"
            ss.user   = None
            ss.ddjj   = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 1 – LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def screen_login():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin:30px 0 24px">
          <div style="display:inline-block;background:#1F3864;padding:14px 32px;
              border-radius:14px;margin-bottom:14px;box-shadow:0 4px 20px rgba(0,0,0,.15)">
            <span style="color:#C1272D;font-weight:900;font-size:40px;letter-spacing:-2px">ERSeP</span>
          </div>
          <h2 style="margin:0 0 4px;font-size:18px">Sistema de DDJJ</h2>
          <p style="color:#5a6478;font-size:12px;margin:0">
            Servicio Público de Transporte Automotor Interurbano<br>
            Subdirección Jurisdicción de Costos y Tarifas
          </p>
        </div>
        """, unsafe_allow_html=True)

        tipo = st.radio("Tipo", ["🏢  Empresa Operadora", "🔐  Panel Regulador"],
                        horizontal=True, label_visibility="collapsed")
        es_emp = "Empresa" in tipo

        with st.form("form_login", clear_on_submit=False):
            st.markdown(f"#### {'Ingreso Empresa' if es_emp else 'Ingreso Regulador'}")
            usuario  = st.text_input("CUIT" if es_emp else "Usuario",
                                     placeholder="30-XXXXXXXX-X" if es_emp else "ERSEP")
            password = st.text_input("Contraseña", type="password")
            submit   = st.form_submit_button("Ingresar →", use_container_width=True, type="primary")

        if submit:
            if es_emp:
                emp = EMPRESAS.get(usuario.strip())
                if not emp:
                    st.error("⚠ CUIT no registrado en el sistema.")
                elif emp["pass"] != password:
                    st.error("⚠ Contraseña incorrecta.")
                else:
                    ss.user   = {"tipo":"empresa","cuit":usuario.strip(),"rs":emp["rs"]}
                    ss.screen = "periodo"
                    st.rerun()
            else:
                if usuario.strip() == ADMIN["user"] and password == ADMIN["pass"]:
                    ss.user   = {"tipo":"admin"}
                    ss.screen = "periodo"
                    st.rerun()
                else:
                    st.error("⚠ Usuario o contraseña incorrectos.")

        if es_emp:
            st.caption("**Demo:** CUIT `30-54633555-7` · contraseña `cota123`")

        st.markdown("""
        <div style="text-align:center;margin-top:20px;font-size:11px;color:#aaa">
          ERSeP © 2026 – Provincia de Córdoba
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 2 – SELECCIÓN DE PERÍODO
# ═══════════════════════════════════════════════════════════════════════════════
def screen_periodo():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        u    = ss.user or {}
        tipo = u.get("tipo","")

        st.markdown(f"""
        <div style="text-align:center;margin:30px 0 20px">
          <div style="display:inline-block;background:#1F3864;padding:10px 26px;
              border-radius:12px;margin-bottom:12px">
            <span style="color:#C1272D;font-weight:900;font-size:32px;letter-spacing:-1px">ERSeP</span>
          </div>
          <h3 style="margin:6px 0;font-size:16px">
            {'Bienvenido — ' + u.get('rs','') if tipo=='empresa' else 'Panel Regulador'}
          </h3>
          <p style="color:#5a6478;font-size:12px;margin:0">
            {'Seleccioná el período de la declaración' if tipo=='empresa'
             else 'Seleccioná el período a consultar'}
          </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_periodo"):
            c1, c2 = st.columns(2)
            with c1:
                año = st.selectbox("Año", AÑOS,
                                   index=AÑOS.index(ss.año) if ss.año in AÑOS else 2)
            with c2:
                mes = st.selectbox("Mes", range(1,13),
                                   format_func=lambda m: MESES[m-1],
                                   index=ss.mes - 1)

            st.markdown(f"""
            <div style="background:#D6E4F0;border-radius:10px;padding:16px;
                text-align:center;margin:12px 0;border:1px solid #2E75B620">
              <div style="font-size:24px;font-weight:900;color:#1F3864">
                {MESES[mes-1]} {año}
              </div>
              <div style="font-size:11px;color:#5a6478;margin-top:4px">
                {'Período a declarar' if tipo=='empresa' else 'Período a consultar'}
              </div>
            </div>
            """, unsafe_allow_html=True)

            ok = st.form_submit_button("Continuar →", use_container_width=True, type="primary")

        if ok:
            ss.año = año
            ss.mes = mes
            if tipo == "empresa":
                existing = load_ddjj(u["cuit"], año, mes)
                ss.ddjj  = existing if existing else empty_ddjj()
            ss.screen = "admin" if tipo == "admin" else "empresa"
            st.rerun()

        if st.button("← Volver al inicio", use_container_width=True):
            ss.screen = "login"
            ss.user   = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  APP EMPRESA
# ═══════════════════════════════════════════════════════════════════════════════
def screen_empresa():
    header_bar()
    u   = ss.user
    d   = ss.ddjj or empty_ddjj()
    año = ss.año
    mes = ss.mes

    tab1, tab2, tab3 = st.tabs([
        "📋  Datos Generales",
        "📎  Documentación Obligatoria",
        "📤  Enviar DDJJ",
    ])

    # ── TAB 1: DATOS GENERALES ──────────────────────────────────────────────
    with tab1:
        st.markdown("### 📍 Producción por Línea / Tramo")
        st.caption("Completá una fila por cada línea operada. Podés agregar o eliminar filas.")

        lineas   = d.get("lineas", [{"linea":"","tramo":"","kmT":0,"svcs":0,"ing":0}])
        df_in    = pd.DataFrame(lineas)
        for col in ["linea","tramo","kmT","svcs","ing"]:
            if col not in df_in.columns:
                df_in[col] = 0 if col in ["kmT","svcs","ing"] else ""

        edited = st.data_editor(
            df_in[["linea","tramo","kmT","svcs","ing"]].rename(columns={
                "linea":"Línea", "tramo":"Tramo / Descripción",
                "kmT":"Km/Trayecto", "svcs":"N° Servicios", "ing":"Ingresos ($)",
            }),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Línea":               st.column_config.TextColumn(width="small"),
                "Tramo / Descripción": st.column_config.TextColumn(width="large"),
                "Km/Trayecto":         st.column_config.NumberColumn(min_value=0, format="%d km"),
                "N° Servicios":        st.column_config.NumberColumn(min_value=0, format="%d"),
                "Ingresos ($)":        st.column_config.NumberColumn(min_value=0, format="$ %d"),
            },
            key="editor_lineas",
        )

        new_lineas = edited.rename(columns={
            "Línea":"linea","Tramo / Descripción":"tramo",
            "Km/Trayecto":"kmT","N° Servicios":"svcs","Ingresos ($)":"ing",
        }).to_dict("records")
        d["lineas"] = new_lineas

        km_t  = sum(float(l.get("kmT") or 0) * float(l.get("svcs") or 0) for l in new_lineas)
        ing_t = sum(float(l.get("ing") or 0) for l in new_lineas)
        c1, c2 = st.columns(2)
        c1.metric("Km producidos totales", fn(km_t))
        c2.metric("Ingresos totales del período", fm(ing_t))

        st.divider()
        st.markdown("### 🚌 Parque, Personal y Combustible")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**Parque Móvil**")
            d["vehiculosActivos"] = st.number_input(
                "Vehículos activos", min_value=0,
                value=int(d.get("vehiculosActivos") or 0), key="vehs")

        with c2:
            st.markdown("**Personal**")
            d["choferes"]        = st.number_input("Choferes",         min_value=0, value=int(d.get("choferes") or 0),        key="chs")
            d["administrativos"] = st.number_input("Administrativos",  min_value=0, value=int(d.get("administrativos") or 0), key="adm")
            d["taller"]          = st.number_input("Taller",           min_value=0, value=int(d.get("taller") or 0),          key="tal")

        with c3:
            st.markdown("**Combustible**")
            d["litrosCombustible"] = st.number_input(
                "Litros consumidos (gasoil + GNC equiv.)",
                min_value=0, value=int(d.get("litrosCombustible") or 0), key="lts")

        st.divider()
        st.markdown("### 📊 Indicadores calculados del período")
        kpi = calc_kpi(d)
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Ingreso/km",         fm(kpi["ing_km"]))
        c2.metric("Choferes/vehículo",  fn(kpi["chs_veh"],  2))
        c3.metric("Empleados/vehículo", fn(kpi["empl_veh"], 2))
        c4.metric("Km/vehículo",        fn(kpi["km_veh"]))
        c5.metric("Lts/vehículo",       fn(kpi["lts_veh"]))
        c6.metric("Km/litro",           fn(kpi["km_lts"],   2))

        st.divider()
        if st.button("💾 Guardar borrador", type="primary", key="btn_save_datos"):
            ss.ddjj = d
            save_ddjj(d, u["cuit"], año, mes)
            st.success("✅ Datos guardados correctamente.")

    # ── TAB 2: DOCUMENTACIÓN ────────────────────────────────────────────────
    with tab2:
        st.markdown("### 📎 Documentación obligatoria del período")
        st.info("Los archivos se guardan en el servidor y quedan disponibles para descarga por el regulador.")

        docs = d.get("documentos", {})
        udir = upload_dir(u["cuit"], año, mes)
        changed = False

        for sec_id, sec_label in [("A","🔥 A – Combustible"), ("B","👷 B – Costo Laboral")]:
            st.markdown(f"#### {sec_label}")
            for dc in [x for x in DOCS_CONFIG if x["sec"] == sec_id]:
                meta  = docs.get(dc["id"])
                label = f"{'✅' if meta else '⬜'}  {dc['label']}"
                with st.expander(label, expanded=not bool(meta)):
                    st.caption(f"📌 {dc['hint']}")
                    st.caption(f"Formatos aceptados: {', '.join(dc['ext']).upper()}")
                    upfile = st.file_uploader(
                        "Seleccionar archivo", type=dc["ext"],
                        key=f"up_{dc['id']}", label_visibility="collapsed",
                    )
                    if upfile:
                        fname = f"{dc['id']}_{upfile.name}"
                        fpath = udir / fname
                        with open(fpath, "wb") as fp:
                            fp.write(upfile.getbuffer())
                        docs[dc["id"]] = {
                            "nombre": upfile.name,
                            "tamaño": f"{upfile.size/1024:.1f} KB",
                            "fecha":  datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "ruta":   str(fpath),
                        }
                        changed = True
                        st.success(f"✅ Archivo guardado: **{upfile.name}**")

                    if meta:
                        st.success(f"📎 **{meta['nombre']}** · {meta['tamaño']} · adjuntado el {meta['fecha']}")
                        fp_path = Path(meta.get("ruta",""))
                        if fp_path.exists():
                            with open(fp_path,"rb") as fp:
                                st.download_button(
                                    f"⬇ Descargar {meta['nombre']}",
                                    data=fp.read(), file_name=meta["nombre"],
                                    key=f"dl_emp_{dc['id']}",
                                    use_container_width=True,
                                )

        total_ok = sum(1 for dc in DOCS_CONFIG if docs.get(dc["id"]))
        st.progress(total_ok / 5, text=f"Documentación: {total_ok}/5 archivos adjuntos")

        if changed or st.button("💾 Guardar documentación", type="primary", key="btn_save_docs"):
            d["documentos"] = docs
            ss.ddjj = d
            save_ddjj(d, u["cuit"], año, mes)
            if not changed:
                st.success("✅ Documentación guardada.")
            st.rerun()

    # ── TAB 3: ENVIAR DDJJ ──────────────────────────────────────────────────
    with tab3:
        kpi   = calc_kpi(d)
        docs  = d.get("documentos", {})
        lineas_ok  = any((l.get("linea") or l.get("tramo")) for l in d.get("lineas",[]))
        docs_count = sum(1 for dc in DOCS_CONFIG if docs.get(dc["id"]))

        st.markdown("### ✅ Verificación pre-envío")
        checks = [
            (lineas_ok,                      "Líneas declaradas"),
            (bool(d.get("vehiculosActivos")), "Vehículos activos"),
            (bool(d.get("choferes")),         "Choferes declarados"),
            (bool(d.get("litrosCombustible")),"Consumo combustible"),
            (docs_count >= 3,                f"Documentación ({docs_count}/5 — mín. 3)"),
        ]
        for ok, label in checks:
            icon = "✅" if ok else "⬜"
            st.markdown(f"{icon} &nbsp; {label}")

        st.divider()
        if d.get("estado") == "enviado":
            st.success(f"✅ **DDJJ enviada** el {d.get('fechaEnvio','')} — Período: {mes_str(año,mes)}")
            st.balloons()
        else:
            all_ok = all(c[0] for c in checks)
            if not all_ok:
                st.warning("⚠ Completá los campos marcados antes de enviar.")

            st.markdown("**Resumen de la declaración:**")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Km producidos",  fn(kpi["km_total"]))
            c2.metric("Ingresos",       fm(kpi["ing_total"]))
            c3.metric("Vehículos",      d.get("vehiculosActivos") or "-")
            c4.metric("Empleados tot.", fn(kpi["empleados"]) or "-")

            if st.button("📤 Confirmar y enviar DDJJ", type="primary",
                         disabled=not all_ok, key="btn_enviar"):
                d["estado"]     = "enviado"
                d["fechaEnvio"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                ss.ddjj = d
                save_ddjj(d, u["cuit"], año, mes)
                st.success("✅ DDJJ enviada correctamente al ERSeP.")
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  APP ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
def screen_admin():
    header_bar()
    año = ss.año
    mes = ss.mes

    # Cambio de período sin salir
    with st.expander("📅 Cambiar período de consulta"):
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            año2 = st.selectbox("Año", AÑOS, index=AÑOS.index(año) if año in AÑOS else 2, key="adm_año")
        with c2:
            mes2 = st.selectbox("Mes", range(1,13), format_func=lambda m:MESES[m-1], index=mes-1, key="adm_mes")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Aplicar", type="primary", key="btn_aplicar"):
                ss.año = año2; ss.mes = mes2; st.rerun()

    # Cargar datos del período
    all_data = list_all_ddjj()
    rows     = [d for d in all_data if int(d.get("año",0))==año and int(d.get("mes",0))==mes]
    # Completar con empresas sin datos
    cuits_ok = {r["cuit"] for r in rows}
    for cuit, emp in EMPRESAS.items():
        if cuit not in cuits_ok:
            rows.append({"cuit":cuit,"rs":emp["rs"],"año":año,"mes":mes,
                         "estado":"sin datos","lineas":[],"documentos":{}})

    n_env = sum(1 for r in rows if r.get("estado")=="enviado")
    st.markdown(f"### 📊 Panel Regulador — {mes_str(año, mes)}")
    st.caption(f"{n_env} DDJJ enviadas  ·  {len(rows)} empresas registradas  ·  {len(rows)-n_env} pendientes")

    tab1, tab2, tab3 = st.tabs([
        "📊  Dashboard / Benchmarking",
        "🏢  Por empresa",
        "📥  Descargas",
    ])

    rows_con_datos = [r for r in rows if r.get("lineas")]

    # ── DASHBOARD ───────────────────────────────────────────────────────────
    with tab1:
        if not rows_con_datos:
            st.warning("No hay datos declarados para este período.")
        else:
            kpis = [calc_kpi(r) for r in rows_con_datos]
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Empresas con datos", len(rows_con_datos))
            c2.metric("Km totales", fn(sum(k["km_total"] for k in kpis)))
            c3.metric("Ingresos sistema", fm(sum(k["ing_total"] for k in kpis)))
            c4.metric("Vehículos totales", fn(sum(float(r.get("vehiculosActivos") or 0) for r in rows_con_datos)))
            c5.metric("Empleados totales", fn(sum(k["empleados"] for k in kpis)))

            st.divider()
            st.markdown("#### Benchmarking por empresa")
            bench = []
            for r, k in zip(rows_con_datos, kpis):
                bench.append({
                    "Empresa":    r.get("rs",""),
                    "Estado":     r.get("estado",""),
                    "Km prod.":   int(round(k["km_total"])),
                    "Ingresos $": int(round(k["ing_total"])),
                    "Vehículos":  r.get("vehiculosActivos",""),
                    "Choferes":   r.get("choferes",""),
                    "Empleados":  int(round(k["empleados"])) or "",
                    "Ing/km":     round(k["ing_km"],2),
                    "Chs/Veh":    round(k["chs_veh"],2),
                    "Empl/Veh":   round(k["empl_veh"],2),
                    "Km/Veh":     int(round(k["km_veh"])),
                    "Lts/Veh":    int(round(k["lts_veh"])),
                    "Km/Ltro":    round(k["km_lts"],2),
                })
            df_bench = pd.DataFrame(bench)
            st.dataframe(df_bench, use_container_width=True, hide_index=True,
                column_config={
                    "Ingresos $": st.column_config.NumberColumn(format="$ %d"),
                    "Km prod.":   st.column_config.NumberColumn(format="%d"),
                })

            st.markdown("#### Km producidos por empresa (miles)")
            chart = pd.DataFrame({
                r.get("rs","").split(" ")[0]: [round(k["km_total"]/1000,1)]
                for r,k in zip(rows_con_datos,kpis)
            })
            st.bar_chart(chart.T, use_container_width=True)

    # ── POR EMPRESA ─────────────────────────────────────────────────────────
    with tab2:
        rs_opciones = [r.get("rs","") for r in rows]
        sel_rs = st.selectbox("Seleccionar empresa", rs_opciones, key="sel_empresa")
        r = next((x for x in rows if x.get("rs")==sel_rs), {})
        kpi = calc_kpi(r)

        estado = r.get("estado","sin datos")
        color  = "🟢" if estado=="enviado" else ("🟡" if estado=="borrador" else "🔴")
        st.markdown(f"**Estado:** {color} `{estado}`")

        if not r.get("lineas"):
            st.warning("Esta empresa no tiene datos cargados para el período seleccionado.")
        else:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Km producidos", fn(kpi["km_total"]))
            c2.metric("Ingresos",      fm(kpi["ing_total"]))
            c3.metric("Vehículos",     r.get("vehiculosActivos") or "-")
            c4.metric("Empleados",     fn(kpi["empleados"]) or "-")

            st.markdown("**Líneas declaradas:**")
            df_l = pd.DataFrame(r.get("lineas",[]))
            if not df_l.empty:
                for col in ["kmT","svcs","ing"]:
                    if col in df_l.columns:
                        df_l[col] = pd.to_numeric(df_l[col], errors="coerce").fillna(0)
                if {"kmT","svcs"}.issubset(df_l.columns):
                    df_l["Km prod."] = (df_l["kmT"] * df_l["svcs"]).astype(int)
                st.dataframe(
                    df_l.rename(columns={
                        "linea":"Línea","tramo":"Tramo","kmT":"Km/Tray",
                        "svcs":"Servicios","ing":"Ingresos ($)"
                    }),
                    use_container_width=True, hide_index=True
                )

        st.markdown("**Documentación adjunta:**")
        docs = r.get("documentos",{})
        doc_rows = []
        for dc in DOCS_CONFIG:
            meta = docs.get(dc["id"])
            doc_rows.append({
                "Doc.":    dc["label"],
                "Estado":  "✅ Adjunto" if meta else "⬜ Pendiente",
                "Archivo": meta["nombre"] if meta else "-",
                "Tamaño":  meta.get("tamaño","") if meta else "-",
                "Fecha":   meta.get("fecha","") if meta else "-",
            })
        st.dataframe(pd.DataFrame(doc_rows), use_container_width=True, hide_index=True)

        st.markdown("**Descargar archivos:**")
        for dc in DOCS_CONFIG:
            meta = docs.get(dc["id"])
            if meta:
                fp = Path(meta.get("ruta",""))
                if fp.exists():
                    with open(fp,"rb") as f:
                        st.download_button(
                            f"⬇  {dc['label']} — {meta['nombre']}",
                            data=f.read(), file_name=meta["nombre"],
                            key=f"adm_dl_{r.get('cuit','')}_{dc['id']}",
                            use_container_width=True,
                        )

    # ── DESCARGAS ────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### Exportar datos del período")
        c1, c2 = st.columns(2)
        with c1:
            filtro = st.radio("Incluir empresas",
                ["Todas", "Solo las que enviaron DDJJ"], key="dl_filtro")
        with c2:
            sel_emp = st.multiselect(
                "O seleccioná específicas (vacío = todas)",
                [r.get("rs","") for r in rows], key="dl_sel")

        rows_exp = rows if filtro == "Todas" else [r for r in rows if r.get("estado")=="enviado"]
        if sel_emp:
            rows_exp = [r for r in rows_exp if r.get("rs") in sel_emp]

        n_exp = len(rows_exp)
        st.info(f"Se exportarán **{n_exp} empresa(s)** — {mes_str(año,mes)}")

        if rows_exp:
            # Excel
            buf_xl = export_excel_all(rows_exp, mes_str(año,mes))
            st.download_button(
                "📊 Descargar Excel con todos los datos (.xlsx)",
                data=buf_xl,
                file_name=f"ERSeP_DDJJ_{mes_str(año,mes).replace(' ','_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, type="primary",
            )

            # ZIP archivos adjuntos
            st.markdown("---")
            st.markdown("**Descargar todos los archivos adjuntos (ZIP):**")
            zip_buf = io.BytesIO()
            any_file = False
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in rows_exp:
                    for dc in DOCS_CONFIG:
                        meta = r.get("documentos",{}).get(dc["id"])
                        if meta:
                            fp = Path(meta.get("ruta",""))
                            if fp.exists():
                                folder = r.get("cuit","").replace("-","_")
                                zf.write(fp, f"{folder}/{dc['id']}_{meta['nombre']}")
                                any_file = True
            if any_file:
                zip_buf.seek(0)
                st.download_button(
                    "🗜 Descargar ZIP con archivos adjuntos",
                    data=zip_buf,
                    file_name=f"ERSeP_Archivos_{mes_str(año,mes).replace(' ','_')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
            else:
                st.caption("ℹ No hay archivos adjuntos guardados para la selección.")

# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
screen = ss.screen
if   screen == "login":   screen_login()
elif screen == "periodo": screen_periodo()
elif screen == "empresa": screen_empresa()
elif screen == "admin":   screen_admin()
