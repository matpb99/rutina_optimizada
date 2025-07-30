import streamlit as st
import json
from optimizer_logic import run_optimization
from data import ALL_EXERCISES
from ui_sidebar import display_sidebar
from ui_main_content import (
    display_exercise_manager,
    display_penalty_manager,
    display_results,
)

def initialize_state():
    if 'exercises' not in st.session_state:
        st.session_state.exercises = ALL_EXERCISES.copy()
    if 'group_per_day' not in st.session_state:
        st.session_state.group_per_day = {}
    if 'exact_series_group' not in st.session_state:
        st.session_state.exact_series_group = {}
    if 'penalties' not in st.session_state:
        st.session_state.penalties = {}
    if 'max_repetitions_per_exercise_weekly' not in st.session_state:
        st.session_state.max_repetitions_per_exercise_weekly = 1
    if 'max_series_day_input' not in st.session_state:
        st.session_state.max_series_day_input = 20
    if 'max_series_grupo_dia_input' not in st.session_state:
        st.session_state.max_series_grupo_dia_input = 8
    if 'selected_weeks_day' not in st.session_state:
        st.session_state.selected_weeks_day = []
    if 'selected_muscle_groups' not in st.session_state:
        st.session_state.selected_muscle_groups = []
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None
    if 'json_uploader_key' not in st.session_state:
        st.session_state.json_uploader_key = 0

def clear_results():
    st.session_state.optimization_results = None

def handle_optimization_click(exercises_for_optimization, key_exercises):
    if not st.session_state.selected_weeks_day:
        st.error("Por favor, selecciona al menos un día de entrenamiento.")
        return
    if not st.session_state.selected_muscle_groups:
        st.error("Por favor, selecciona al menos un grupo muscular.")
        return
    if not any(st.session_state.group_per_day.values()):
        st.error("Por favor, asigna al menos un grupo muscular a un día.")
        return

    problem, series, penalized = run_optimization(
        st.session_state.selected_weeks_day,
        st.session_state.group_per_day,
        exercises_for_optimization,
        st.session_state.exact_series_group,
        st.session_state.max_series_day_input,
        st.session_state.max_series_grupo_dia_input,
        st.session_state.penalties,
        st.session_state.max_repetitions_per_exercise_weekly,
        key_exercises,
    )
    st.session_state.optimization_results = (problem, series, penalized)

initialize_state() 

st.set_page_config(layout="wide")
st.title("🏋️‍♂️ Optimizador de Rutina de Gimnasio")

st.subheader("Cargar Rutina Guardada")
st.write("Sube un archivo JSON previamente descargado para restaurar tu configuración.")
uploaded_file = st.file_uploader("Selecciona un archivo JSON", type=["json"], key=f"json_uploader_{st.session_state.json_uploader_key}")

if uploaded_file is not None:
    try:
        loaded_data = json.loads(uploaded_file.read())
        for key, value in loaded_data.items():
            if key == "penalties":
                st.session_state[key] = {eval(k) if isinstance(k, str) and k.startswith('(') and k.endswith(')') else k: v for k, v in value.items()}
            else:
                st.session_state[key] = value
        st.success("Rutina cargada exitosamente.")
        st.session_state.json_uploader_key += 1
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al cargar el archivo JSON: {e}")

all_muscle_groups = sorted(list(set(st.session_state.exercises.values())))
display_sidebar(all_muscle_groups, on_change_callback=clear_results)

with st.expander("💾 Guardar Rutina Actual", expanded=False):
    st.subheader("Guardar Rutina Actual")
    st.write("Descarga tu configuración actual para cargarla más tarde o en otro dispositivo.")

    save_data = {
        "exercises": st.session_state.exercises,
        "group_per_day": st.session_state.group_per_day,
        "exact_series_group": st.session_state.exact_series_group,
        "penalties": {str(k): v for k, v in st.session_state.penalties.items()},
        "max_repetitions_per_exercise_weekly": st.session_state.max_repetitions_per_exercise_weekly,
        "max_series_day_input": st.session_state.max_series_day_input,
        "max_series_grupo_dia_input": st.session_state.max_series_grupo_dia_input,
        "selected_weeks_day": st.session_state.selected_weeks_day,
        "selected_muscle_groups": st.session_state.selected_muscle_groups,
    }
    json_data = json.dumps(save_data, indent=4, ensure_ascii=False)

    st.download_button(
        label="Descargar Rutina (JSON)",
        data=json_data,
        file_name="rutina_optimizada.json",
        mime="application/json"
    )

with st.expander("🏋️‍♀️ Gestión de Ejercicios", expanded=True):
    exercises_for_optimization, key_exercises = display_exercise_manager(all_muscle_groups)
    st.session_state.exercises_for_optimization = exercises_for_optimization

with st.expander("🚫 Ejercicios Incompatibles (Penalizaciones)", expanded=True):
    display_penalty_manager()

st.button(
    "Generar Rutina Optimizada",
    on_click=handle_optimization_click,
    args=(exercises_for_optimization, key_exercises)
)

if st.session_state.optimization_results:
    with st.expander("📊 Resultados de la Optimización", expanded=True):
        problem, series, penalized = st.session_state.optimization_results
        display_results(problem, series, penalized)
