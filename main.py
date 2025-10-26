import os
import re
import uuid
import io
import datetime
import pandas as pd
import streamlit as st
import google.generativeai as genai

# Configurar entorno y API
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = "none"
genai.configure(api_key=st.secrets["general"]["GOOGLE_API_KEY"])


model = genai.GenerativeModel("gemini-2.0-flash")

# Configuración de la página
st.set_page_config(
    page_title="Detector de Matrículas",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos personalizados
st.markdown("""
    <style>
        html, body, [class*="css"] {
            background-color: #0f172a !important;
            color: #e2e8f0 !important;
            font-family: "Inter", sans-serif;
        }
        h1 {
            background: linear-gradient(90deg, #38bdf8, #22d3ee, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            font-weight: 800;
            font-size: 2.4em;
            margin-bottom: 0.4em;
        }
        h2, h3 {
            color: #7dd3fc !important;
            font-weight: 600;
        }
        p, label {
            color: #cbd5e1 !important;
        }
        .stButton > button {
            background: linear-gradient(90deg, #06b6d4, #0ea5e9);
            color: white;
            border-radius: 10px;
            font-size: 16px;
            padding: 10px 18px;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #0ea5e9, #14b8a6);
            transform: scale(1.03);
        }
        .result-box {
            background: rgba(45, 212, 191, 0.1);
            padding: 1em;
            border-radius: 10px;
            text-align: center;
            color: #5eead4;
            font-size: 1.8em;
            font-weight: bold;
            letter-spacing: 2px;
            margin-top: 10px;
            border: 2px solid #14b8a6;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
            max-width: 1100px;
            margin: auto;
        }
        .section {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5em;
            box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.3);
        }
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
        }
        .css-1dp5vir, .stAlert {
            background-color: #1e293b !important;
            color: #e2e8f0 !important;
            border: 1px solid #334155 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Inicializar estado
if "matriculas" not in st.session_state:
    st.session_state.matriculas = []

# Título
st.markdown("<h1> Detector de Matrículas con Gemini 🚘</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>Sube imágenes y Gemini detectará automáticamente las matrículas. A la derecha verás el registro actualizado en tiempo real.</p>", unsafe_allow_html=True)
st.markdown("---")

# Layout
col_izq, col_der = st.columns([1.2, 1])

# --- Columna izquierda: Carga y análisis ---
with col_izq:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("Analizador de imagen")

    uploaded_image = st.file_uploader("Sube una imagen del coche:", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        st.image(uploaded_image, caption="Imagen cargada", width=400)

        if st.button("🔍 Detectar matrícula"):
            with st.spinner("Analizando imagen con Gemini..."):
                try:
                    # Leer imagen directamente en memoria
                    image_bytes = uploaded_image.read()

                    prompt = (
                        "Lee SOLO la matrícula del vehículo en la imagen. "
                        "Devuelve únicamente los caracteres alfanuméricos de la matrícula "
                        "sin texto adicional, sin explicación, sin espacios extra, "
                        "sin símbolos distintos de letras o números. "
                        "Ejemplo de salida: ABC1234"
                    )

                    response = model.generate_content([
                        prompt,
                        {"mime_type": "image/jpeg", "data": image_bytes}
                    ])

                    raw_result = response.text.strip()
                    clean_result = re.sub(r'[^A-Za-z0-9]', '', raw_result)

                    if clean_result:
                        st.markdown(f"<div class='result-box'>{clean_result}</div>", unsafe_allow_html=True)
                        st.success(f"✅ Matrícula '{clean_result}' agregada correctamente.")
                        st.session_state.matriculas.append({
                            "GUID": str(uuid.uuid4())[:8].upper(),
                            "Matricula": clean_result,
                            "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        st.warning("No se detectó ninguna matrícula legible.")
                except Exception as e:
                    st.error(f"Ocurrió un error con Gemini: {e}")
    else:
        st.info("Sube una imagen para comenzar el análisis.")

    st.markdown("</div>", unsafe_allow_html=True)

# --- Columna derecha: Registro ---
with col_der:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("Registro de matrículas")

    if st.session_state.matriculas:
        df = pd.DataFrame(st.session_state.matriculas)
        st.dataframe(df, use_container_width=True, height=400)

        # Guardar Excel en memoria (siempre mismo nombre)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=excel_buffer,
            file_name="matriculas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Aún no hay matrículas detectadas.")

    st.markdown("</div>", unsafe_allow_html=True)
