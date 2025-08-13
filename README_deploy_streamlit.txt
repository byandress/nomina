# Despliegue rápido de tu app en Streamlit

## 1) ¿Qué es Streamlit?
Es un framework de Python para crear apps web de datos con pocas líneas de código. Permite construir formularios, subir archivos (PDF/Excel), mostrar tablas y descargar reportes.

## 2) Correr localmente (tu PC)
Requisitos: Python 3.10+ y pip.

Comandos (Windows PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py

Comandos (macOS/Linux):
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

Luego abre http://localhost:8501

## 3) Subir a la nube (Streamlit Community Cloud – gratis)
1. Crea un repo en GitHub con: app.py y requirements.txt
2. Entra a https://share.streamlit.io (inicia sesión)
3. New app -> selecciona repo, branch y app.py -> Deploy

Notas: En la nube el disco es temporal; usa st.download_button para bajar reportes. Si solo usas pdfplumber/pandas/openpyxl no necesitas Java ni Tesseract.

## 4) Estructura sugerida
/tu-repo
  app.py
  requirements.txt
  /sample_data (opcional)
    base_salarios.xlsx
    Desprendibles_Jun2025.pdf

## 5) Problemas comunes
- ModuleNotFoundError: agrega el paquete a requirements.txt
- Cambios de layout del PDF: ajusta regex/mapeos.
- Puerto bloqueado: usa el URL que imprime Streamlit (8501 por defecto).
