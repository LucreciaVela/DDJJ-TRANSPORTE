# ERSeP – Sistema DDJJ Transporte Interurbano

Sistema web de Declaración Jurada de Producción, Costos y Documentación  
**Subdirección Jurisdicción de Costos y Tarifas – Provincia de Córdoba**

---

## 🚀 Cómo ejecutar localmente

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/ersep-ddjj.git
cd ersep-ddjj

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la app
streamlit run app.py
```

La app se abre en: `http://localhost:8501`

---

## 🌐 Deploy en Streamlit Community Cloud (gratuito)

1. Subir este repositorio a **GitHub** (puede ser privado)
2. Ir a [share.streamlit.io](https://share.streamlit.io)
3. Conectar tu cuenta de GitHub
4. Seleccionar el repositorio → rama `main` → archivo `app.py`
5. Click **Deploy** → en ~2 minutos tenés la URL pública

---

## 🔐 Credenciales de acceso

### Panel Regulador
| Usuario | Contraseña |
|---------|-----------|
| `ERSEP` | `ersep2026` |

### Empresas (demo)
| CUIT | Contraseña | Empresa |
|------|-----------|---------|
| `30-54633555-7` | `cota123` | COTA LA CALERA LTDA. |
| `30-70730781-8` | `sarm123` | EMPRESA SARMIENTO S.R.L. |
| `30-67871434-4` | `fono123` | EMPRENDIMIENTOS S.R.L. (FONO BUS) |
| `30-64484750-7` | `sier123` | EXCURSIONES SIERRAS DE CALAMUCHITA |
| `30-54624472-1` | `coat123` | COATA S.A. |

---

## 📁 Estructura del proyecto

```
ersep-ddjj/
├── app.py                  # Aplicación principal
├── requirements.txt        # Dependencias Python
├── .streamlit/
│   └── config.toml         # Tema institucional
├── data/                   # DDJJ guardadas (JSON)
├── uploads/                # Archivos adjuntos por empresa
└── README.md
```

---

## 📋 Funcionalidades

### Empresa
- **Datos Generales**: líneas/tramos, km, servicios, ingresos, flota, personal, combustible
- **Indicadores automáticos**: ingreso/km, choferes/vehículo, km/vehículo, etc.
- **Documentación**: carga de 5 documentos obligatorios (A1-A3 combustible, B1-B2 personal)
- **Envío DDJJ**: verificación y confirmación

### Panel Regulador (ERSeP)
- **Dashboard**: KPIs del sistema + benchmarking por empresa
- **Por empresa**: detalle completo + descarga de archivos adjuntos
- **Descargas**: Excel multi-hoja + ZIP con todos los archivos

---

## ⚠️ Nota sobre persistencia de datos

En **Streamlit Community Cloud**, los archivos se guardan en el servidor pero se **resetean** con cada redeploy.  
Para persistencia permanente se recomienda integrar con:
- **Google Drive** (via API)
- **AWS S3 / Cloudflare R2** 
- **Base de datos PostgreSQL** (Neon, Supabase — versión gratuita)

Para uso interno en servidor propio, los datos persisten sin problema.
