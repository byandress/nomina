import io
import math
from typing import List, Dict, Optional

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Validador de Parafiscales", layout="wide")

# ========= Helper: mensajes bonitos =========
def ok(msg: str):
    st.success(f"✅ {msg}")

def warn(msg: str):
    st.warning(f"⚠️ {msg}")

def err(msg: str):
    st.error(f"❌ {msg}")

# ========= Validadores de archivos =========
REQ_NIVELES = {"nivel", "salario_base"}  # aplica_aux_transporte es opcional
REQ_NOMINA = {"cedula", "total_devengado_reportado"}  # nombre, nivel y neto_reportado son opcionales

def normaliza_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def validar_excel_niveles(df: pd.DataFrame) -> Optional[str]:
    cols = set(df.columns)
    faltan = REQ_NIVELES - cols
    if faltan:
        return f"El Excel de niveles debe incluir columnas: {', '.join(REQ_NIVELES)}. Faltan: {', '.join(faltan)}"
    # salario_base debe ser numérico
    try:
        _ = pd.to_numeric(df["salario_base"])
    except Exception:
        return "La columna 'salario_base' debe ser numérica (sin símbolos como $ o puntos de miles)."
    return None

def validar_excel_nomina(df: pd.DataFrame) -> Optional[str]:
    cols = set(df.columns)
    faltan = REQ_NOMINA - cols
    if faltan:
        return f"El Excel de nómina debe incluir columnas mínimas: {', '.join(REQ_NOMINA)}. Faltan: {', '.join(faltan)}"
    # cedula y total_devengado_reportado deben existir y ser válidos
    if df["cedula"].isna().any():
        return "Existen filas sin cédula en la nómina mensual."
    try:
        _ = pd.to_numeric(df["total_devengado_reportado"])
    except Exception:
        return "La columna 'total_devengado_reportado' debe ser numérica (sin símbolos)."
    return None

# ========= Sidebar: Insumos y parámetros =========
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Claro_logo.svg/512px-Claro_logo.svg.png",
    caption="(Logo de ejemplo, puedes subir uno propio abajo)", use_column_width=True
)

logo_file = st.sidebar.file_uploader("Logo (opcional, PNG/JPG)", type=["png", "jpg", "jpeg"])
logo_url = st.sidebar.text_input("o URL de logo (opcional)")

st.sidebar.header("1) Excel de niveles")
niveles_file = st.sidebar.file_uploader("Sube Excel de niveles salariales", type=["xlsx", "xls"])

st.sidebar.header("2) Excel de nómina mensual (para comparar)")
nomina_file = st.sidebar.file_uploader("Sube Excel de nómina del mes", type=["xlsx", "xls"])

st.sidebar.header("3) Parámetros")
horas_mes_base = st.sidebar.number_input("Horas base al mes", min_value=160, max_value=300, value=240, step=1)
pct_extra_diurna   = st.sidebar.number_input("Factor Hora Extra Diurna (%)", value=25, step=1) / 100.0
pct_extra_nocturna = st.sidebar.number_input("Factor Hora Extra Nocturna (%)", value=75, step=1) / 100.0
pct_recargo_noct   = st.sidebar.number_input("Recargo Nocturno Ordinario (%)", value=35, step=1) / 100.0
pct_dom_fest       = st.sidebar.number_input("Recargo Dominical/Festivo (%)", value=75, step=1) / 100.0

aux_transporte_mensual = st.sidebar.number_input("Auxilio de transporte mensual (si aplica)", min_value=0, value=200000, step=1000)
prorratear_aux_trans = st.sidebar.checkbox("Prorratear aux. transporte por días", value=True)

# ========= Branding simple en el header =========
col_logo, col_title = st.columns([1,4])
with col_logo:
    if logo_file:
        st.image(logo_file, use_column_width=True)
    elif logo_url:
        st.image(logo_url, use_column_width=True)
with col_title:
    st.title("Validador de desprendibles / parafiscales")

# ========= Cargar y validar excels =========
if not niveles_file:
    st.info("Sube el **Excel de niveles** en la barra lateral para continuar.")
    st.stop()

niveles_df = normaliza_cols(pd.read_excel(niveles_file))
msg = validar_excel_niveles(niveles_df)
if msg:
    err(msg)
    st.stop()

ok("Excel de niveles cargado correctamente.")

if nomina_file:
    nomina_df = normaliza_cols(pd.read_excel(nomina_file))
    msg2 = validar_excel_nomina(nomina_df)
    if msg2:
        err(msg2)
        st.stop()
    ok("Excel de nómina mensual cargado correctamente.")
else:
    nomina_df = None
    warn("Aún no subiste el Excel de nómina mensual. Puedes trabajar solo con el formulario y luego comparar.")

# ========= Formulario por persona =========
st.header("Formulario por persona (cálculo y validación)")
col1, col2, col3 = st.columns(3)
with col1:
    cedula = st.text_input("Cédula")
    nombre = st.text_input("Nombre")
with col2:
    nivel_sel = st.selectbox("Nivel salarial", options=sorted(niveles_df["nivel"].unique()))
    dias_trab = st.number_input("Días laborados en el período", min_value=0, max_value=31, value=30)
with col3:
    aplica_aux_trans = st.selectbox("¿Aplica aux. transporte?", options=["Auto(desde nivel)", "Sí", "No"])

st.subheader("Horas y conceptos del período")
c1, c2, c3, c4 = st.columns(4)
with c1:
    horas_ord_diurnas = st.number_input("Horas ordinarias diurnas", min_value=0.0, value=0.0, step=1.0)
with c2:
    horas_extra_diurnas = st.number_input("Horas extra diurnas", min_value=0.0, value=0.0, step=1.0)
with c3:
    horas_ord_noct = st.number_input("Horas ordinarias nocturnas (recargo)", min_value=0.0, value=0.0, step=1.0)
with c4:
    horas_dom_fest = st.number_input("Horas dominical/festivo (recargo)", min_value=0.0, value=0.0, step=1.0)

c5, c6, c7 = st.columns(3)
with c5:
    aux_alim = st.number_input("Aux. alimentación (total $)", min_value=0, value=0, step=1000)
with c6:
    retroactivos = st.number_input("Retroactivos/bonos ($)", min_value=0, value=0, step=1000)
with c7:
    otros_dev = st.number_input("Otros devengados ($)", min_value=0, value=0, step=1000)

st.divider()

# ========= Cálculo esperado =========
row_nivel = niveles_df.loc[niveles_df["nivel"] == nivel_sel].iloc[0]
salario_base = float(row_nivel["salario_base"])

# aplica aux transporte
if "aplica_aux_transporte" in niveles_df.columns and aplica_aux_trans == "Auto(desde nivel)":
    aplica_aux = str(row_nivel["aplica_aux_transporte"]).strip().upper().startswith("S")
else:
    if aplica_aux_trans == "Sí":
        aplica_aux = True
    elif aplica_aux_trans == "No":
        aplica_aux = False
    else:
        aplica_aux = True  # por defecto si no hay columna

salario_proporcional = round(salario_base * (dias_trab / 30.0), 2)
valor_hora = salario_base / horas_mes_base

val_ord_diurnas   = round(horas_ord_diurnas   * valor_hora,                       2)
val_extra_diurnas = round(horas_extra_diurnas * valor_hora * (1.0 + pct_extra_diurna),   2)
val_ord_noct      = round(horas_ord_noct      * valor_hora * (1.0 + pct_recargo_noct),   2)
val_dom_fest      = round(horas_dom_fest      * valor_hora * (1.0 + pct_dom_fest),       2)

if aplica_aux:
    aux_trans = aux_transporte_mensual * (dias_trab/30.0) if prorratear_aux_trans else aux_transporte_mensual
    aux_trans = round(aux_trans, 2)
else:
    aux_trans = 0.0

devengados = {
    "salario_proporcional": salario_proporcional,
    "horas_ord_diurnas": val_ord_diurnas,
    "horas_extra_diurnas": val_extra_diurnas,
    "horas_ord_noct_recargo": val_ord_noct,
    "recargo_dom_fest": val_dom_fest,
    "aux_transporte": aux_trans,
    "aux_alimentacion": aux_alim,
    "retroactivos_bonos": retroactivos,
    "otros_dev": otros_dev
}
total_devengado_calc = round(sum(devengados.values()), 2)

st.subheader("Resultado calculado (esperado)")
st.write(pd.DataFrame([devengados | {
    "total_devengado": total_devengado_calc,
    "salario_base_nivel": salario_base,
    "valor_hora_base": round(valor_hora, 2)
}]))

# ========= Comparación contra nómina mensual =========
st.subheader("Comparar contra Excel de nómina mensual (opcional)")
total_dev_reportado = 0.0
neto_reportado = 0.0
encontrado = None

if nomina_df is not None and cedula:
    # buscar por cédula (coincidencia exacta)
    encontrados = nomina_df[nomina_df["cedula"].astype(str) == str(cedula)]
    if not encontrados.empty:
        encontrado = encontrados.iloc[0].to_dict()
        total_dev_reportado = float(encontrado.get("total_devengado_reportado", 0) or 0)
        neto_reportado = float(encontrado.get("neto_reportado", 0) or 0)
        ok(f"Encontrado en nómina mensual: {encontrado.get('nombre','(sin nombre)')}")
    else:
        warn("Esa cédula no aparece en el Excel de nómina mensual.")

col_a, col_b = st.columns(2)
with col_a:
    total_dev_manual = st.number_input("Total devengado reportado ($)", min_value=0.0, value=float(total_dev_reportado or 0), step=1000.0)
with col_b:
    neto_manual = st.number_input("Neto a pagar reportado ($)", min_value=0.0, value=float(neto_reportado or 0), step=1000.0)

diferencia = round(total_dev_manual - total_devengado_calc, 2)
st.metric("Diferencia (reportado - calculado)", f"${diferencia:,.2f}")

# Alertas
alerts = []
if abs(diferencia) > 1000:
    alerts.append(f"Diferencia de devengados supera umbral: ${diferencia:,.2f}")
if dias_trab > 30:
    alerts.append("Días trabajados > 30.")
if valor_hora <= 0:
    alerts.append("Valor hora no válido (revisa horas base/salario).")

if alerts:
    st.warning("Alertas:\n- " + "\n- ".join(alerts))
else:
    st.success("Sin alertas por ahora.")

# ========= Consolidado en sesión =========
if "consolidado" not in st.session_state:
    st.session_state["consolidado"] = []

st.divider()
colx, coly = st.columns([1,3])
with colx:
    if st.button("➕ Agregar al consolidado"):
        registro = {
            "cedula": cedula, "nombre": nombre, "nivel": nivel_sel, "dias": dias_trab,
            **devengados, "total_devengado_calc": total_devengado_calc,
            "total_dev_reportado": total_dev_manual,
            "diferencia_dev": diferencia, "neto_reportado": neto_manual
        }
        st.session_state["consolidado"].append(registro)
        ok("Agregado al consolidado.")

with coly:
    if st.button("🗑️ Vaciar consolidado"):
        st.session_state["consolidado"] = []
        warn("Consolidado vaciado.")

# Mostrar tabla consolidada
st.subheader("Consolidado (en memoria)")
df_cons = pd.DataFrame(st.session_state["consolidado"])
st.dataframe(df_cons, use_container_width=True)

# ========= Exportar Excel consolidado con formato =========
def exportar_excel_consolidado(df: pd.DataFrame) -> bytes:
    if df.empty:
        return b""
    # Orden de columnas sugerido
    cols = [
        "cedula","nombre","nivel","dias",
        "salario_proporcional","horas_ord_diurnas","horas_extra_diurnas",
        "horas_ord_noct_recargo","recargo_dom_fest","aux_transporte",
        "aux_alimentacion","retroactivos_bonos","otros_dev",
        "total_devengado_calc","total_dev_reportado","diferencia_dev","neto_reportado"
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
        wb  = writer.book
        ws  = writer.sheets["Datos"]

        # Formatos
        header_fmt = wb.add_format({"bold": True, "bg_color": "#F2F2F2", "border":1})
        money_fmt  = wb.add_format({"num_format": "#,##0", "border":1})
        text_fmt   = wb.add_format({"border":1})
        alert_fmt  = wb.add_format({"bg_color": "#FFF2CC", "border":1})

        # Encabezados
        for col_num, value in enumerate(df.columns.values):
            ws.write(0, col_num, value, header_fmt)

        # Ajustar anchos y formato numérico
        num_cols = {i for i,c in enumerate(df.columns) if c not in {"cedula","nombre","nivel"}}
        for i, col in enumerate(df.columns):
            width = 18 if col in {"cedula","nombre"} else 16
            ws.set_column(i, i, width)
            # aplicar formato por columna
            if i in num_cols:
                ws.set_column(i, i, width, money_fmt)
            else:
                ws.set_column(i, i, width, text_fmt)

        # Hoja de alertas
        alerts_df = df[df["diferencia_dev"].abs() > 1000][["cedula","nombre","nivel","total_devengado_calc","total_dev_reportado","diferencia_dev"]]
        alerts_df.to_excel(writer, index=False, sheet_name="Alertas")
        ws2 = writer.sheets["Alertas"]
        for col_num, value in enumerate(alerts_df.columns.values):
            ws2.write(0, col_num, value, header_fmt)
        for i in range(0, len(alerts_df.columns)):
            ws2.set_column(i, i, 20, alert_fmt)

    return output.getvalue()

st.subheader("Descargar consolidado")
excel_bytes = exportar_excel_consolidado(df_cons)
st.download_button(
    "⬇️ Descargar Consolidado.xlsx",
    data=excel_bytes,
    file_name="Consolidado.xlsx",
    disabled=len(df_cons)==0,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("Tip: Sube tu logo, completa el formulario por persona, agrega al consolidado y descarga el Excel final con pestaña de Alertas.")
