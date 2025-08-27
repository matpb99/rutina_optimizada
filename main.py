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
    if 'key_exercises' not in st.session_state:
        st.session_state.key_exercises = []
    if 'exercises_for_optimization' not in st.session_state:
        st.session_state.exercises_for_optimization = {}


def clear_results():
    st.session_state.optimization_results = None


def handle_optimization_click(exercises_for_optimization, key_exercises):

    if not st.session_state.selected_weeks_day:
        st.error("Error: Debes seleccionar al menos un día de entrenamiento.")
        return

    if not st.session_state.selected_muscle_groups:
        st.error("Error: Debes seleccionar al menos un grupo muscular.")
        return

    if not any(st.session_state.group_per_day.values()):
        st.error(
            "Error: Debes asignar al menos un grupo muscular a un día de entrenamiento.")
        return

    for day, groups in st.session_state.group_per_day.items():
        if not groups:
            continue
        for group in groups:
            exercises_in_group = [
                e for e, g in exercises_for_optimization.items() if g == group]
            if not exercises_in_group:
                st.error(
                    f"Error en el día '{day}': El grupo muscular '{group}' está asignado, pero no tiene ningún ejercicio activo. Por favor, activa al menos un ejercicio para este grupo o quítalo del día.")
                return

    for group, min_series in st.session_state.exact_series_group.items():
        if min_series <= 0:
            continue

        exercises_in_group = [
            e for e, g in exercises_for_optimization.items() if g == group]
        # Asumiendo 4 series max por ejercicio
        max_possible_series = len(
            exercises_in_group) * st.session_state.max_repetitions_per_exercise_weekly * 4

        if max_possible_series < min_series:
            st.error(f"Error de configuración: El grupo muscular '{group}' tiene un objetivo de {min_series} series semanales, pero con los ejercicios activos y sus límites solo es posible alcanzar un máximo de {max_possible_series} series. Considera activar más ejercicios para este grupo, aumentar las repeticiones semanales o reducir el objetivo de series.")
            return

    problem, series, penalized, status = run_optimization(
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

    if status == -1:
        st.error(
            "No se pudo generar una rutina con las restricciones actuales. La configuración es demasiado estricta.")
        st.warning("Sugerencias para solucionar el problema:")
        st.markdown("""
        - **Aumenta el máximo de series por día.**
        - **Reduce el mínimo de series semanales** para algún grupo muscular.
        - **Activa más ejercicios** para los grupos musculares con objetivos de series altos.
        - **Revisa las penalizaciones**, podrías tener demasiados ejercicios incompatibles.
        - **Aumenta las repeticiones máximas semanales** para los ejercicios clave.
        """)
        st.session_state.optimization_results = None
        return

    st.session_state.optimization_results = (problem, series, penalized)


initialize_state()

st.set_page_config(layout="wide")
st.title("🏋️‍♂️ Optimizador de Rutina de Gimnasio")

st.subheader("Cargar Rutina Guardada")
st.write("Sube un archivo JSON previamente descargado para restaurar tu configuración.")
uploaded_file = st.file_uploader("Selecciona un archivo JSON", type=[
                                 "json"], key=f"json_uploader_{st.session_state.json_uploader_key}")

if uploaded_file is not None:
    try:
        loaded_data = json.loads(uploaded_file.read())
        for key, value in loaded_data.items():
            if key == "penalties":
                st.session_state[key] = {eval(k) if isinstance(k, str) and k.startswith(
                    '(') and k.endswith(')') else k: v for k, v in value.items()}
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
    st.write(
        "Descarga tu configuración actual para cargarla más tarde o en otro dispositivo.")

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
        "key_exercises": st.session_state.get("key_exercises", []),
        "exercises_for_optimization": st.session_state.get("exercises_for_optimization", {}),
    }
    json_data = json.dumps(save_data, indent=4, ensure_ascii=False)

    st.download_button(
        label="Descargar Rutina (JSON)",
        data=json_data,
        file_name="rutina_optimizada.json",
        mime="application/json"
    )

with st.expander("🏋️‍♀️ Gestión de Ejercicios", expanded=True):
    exercises_for_optimization, key_exercises = display_exercise_manager(
        all_muscle_groups)
    st.session_state.exercises_for_optimization = exercises_for_optimization
    st.session_state.key_exercises = key_exercises

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
