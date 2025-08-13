import io
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Validador de Parafiscales", layout="wide")

st.title("Validador de desprendibles / parafiscales")

# -------------------------
# 1) Cargar tabla de niveles
# -------------------------
st.sidebar.header("1) Configurar insumos")
niveles_file = st.sidebar.file_uploader("Excel de niveles salariales", type=["xlsx", "xls"])
if niveles_file:
    niveles_df = pd.read_excel(niveles_file)
    # Esperado: columnas: nivel, salario_base, aplica_aux_transporte (S/N)
    # Puedes renombrar aquí si tus cabeceras reales difieren
    expected_cols = {"nivel","salario_base"}
    if not expected_cols.issubset(set(c.lower() for c in niveles_df.columns)):
        st.sidebar.error("El Excel de niveles debe incluir columnas: nivel, salario_base (y opcional aplica_aux_transporte).")
        st.stop()
    # Normalizar
    niveles_df.columns = [c.lower() for c in niveles_df.columns]
else:
    st.info("Sube el Excel de niveles para habilitar el formulario.")
    st.stop()

# -------------------------
# 2) Parámetros de cálculo
# -------------------------
st.sidebar.header("2) Parámetros")
horas_mes_base = st.sidebar.number_input("Horas base al mes", min_value=160, max_value=300, value=240, step=1)
# Factores configurables (ejemplos – AJÚSTALOS a tu política/leyes internas)
pct_extra_diurna   = st.sidebar.number_input("Factor Hora Extra Diurna (%)", value=25, step=1) / 100.0
pct_extra_nocturna = st.sidebar.number_input("Factor Hora Extra Nocturna (%)", value=75, step=1) / 100.0
pct_recargo_noct   = st.sidebar.number_input("Recargo Nocturno Ordinario (%)", value=35, step=1) / 100.0
pct_dom_fest       = st.sidebar.number_input("Recargo Dominical/Festivo (%)", value=75, step=1) / 100.0

aux_transporte_mensual = st.sidebar.number_input("Auxilio de transporte mensual (si aplica)", min_value=0, value=200000, step=1000)
prorratear_aux_trans = st.sidebar.checkbox("Prorratear aux. transporte por días", value=True)

# -------------------------
# 3) Formulario por persona
# -------------------------
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

# Horas y conceptos
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

# -------------------------
# 4) Cálculo esperado segun nivel y reglas
# -------------------------
row_nivel = niveles_df.loc[niveles_df["nivel"] == nivel_sel].iloc[0]
salario_base = float(row_nivel["salario_base"])

# Aplica aux transporte: auto según excel si existe columna, o según elección manual
aplica_auto = False
if "aplica_aux_transporte" in niveles_df.columns and aplica_aux_trans == "Auto(desde nivel)":
    aplica_auto = True
    aplica_aux = str(row_nivel["aplica_aux_transporte"]).strip().upper().startswith("S")
else:
    if aplica_aux_trans == "Sí":
        aplica_aux = True
    elif aplica_aux_trans == "No":
        aplica_aux = False
    else:
        # sin columna y marcado auto -> por defecto True (ajústalo a tu política)
        aplica_aux = True

# Salario proporcional
salario_proporcional = round(salario_base * (dias_trab / 30.0), 2)

# Valor hora ordinaria base (salario / horas_mes_base)
valor_hora = salario_base / horas_mes_base

# Montos por hora/recargo (ajusta fórmulas a tu política exacta)
val_ord_diurnas = round(horas_ord_diurnas * valor_hora, 2)
val_extra_diurnas = round(horas_extra_diurnas * valor_hora * (1.0 + pct_extra_diurna), 2)
val_ord_noct = round(horas_ord_noct * valor_hora * (1.0 + pct_recargo_noct), 2)
val_dom_fest = round(horas_dom_fest * valor_hora * (1.0 + pct_dom_fest), 2)

# Aux transporte
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

# -------------------------
# 5) (Opcional) Comparar con valores del PDF/Excel real
# -------------------------
st.subheader("Comparar contra valores reportados (opcional)")
col_a, col_b = st.columns(2)
with col_a:
    total_dev_reportado = st.number_input("Total devengado reportado ($)", min_value=0.0, value=0.0, step=1000.0)
with col_b:
    neto_reportado = st.number_input("Neto a pagar reportado ($)", min_value=0.0, value=0.0, step=1000.0)

diferencia = round(total_dev_reportado - total_devengado_calc, 2)
st.metric("Diferencia (reportado - calculado)", f"${diferencia:,.2f}")

# Alertas simples
alerts = []
if abs(diferencia) > 1000:
    alerts.append(f"Diferencia de devengados supera umbral: ${diferencia:,.2f}")
if dias_trab > 30:
    alerts.append("Días trabajados > 30.")
if valor_hora <= 0:
    alerts.append("Valor hora no válido (revisa horas base/salario).")

if alerts:
    st.warning("⚠️ Alertas:\n- " + "\n- ".join(alerts))
else:
    st.success("Sin alertas por ahora.")

# -------------------------
# 6) Exportar registro y consolidado en memoria
# -------------------------
st.divider()
st.subheader("Exportar")
registro = {
    "cedula": cedula, "nombre": nombre, "nivel": nivel_sel, "dias": dias_trab,
    **devengados, "total_devengado_calc": total_devengado_calc,
    "total_dev_reportado": total_dev_reportado,
    "diferencia_dev": diferencia, "neto_reportado": neto_reportado
}
df_registro = pd.DataFrame([registro])

csv = df_registro.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Descargar reporte de esta persona (CSV)", csv, file_name=f"reporte_{cedula or 'sin_cc'}.csv", mime="text/csv")
