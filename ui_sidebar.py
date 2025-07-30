import streamlit as st
from data import DEFAULT_EXACT_SERIES_VALUE, WEEK_DAYS

def display_sidebar(all_muscle_groups, on_change_callback):
    st.sidebar.header("⚙️ Configuración de Rutina")
    st.sidebar.write('Ajusta los parámetros para generar tu rutina personalizada.')

    with st.sidebar.expander("1️⃣ Configuración General", expanded=True):
        st.number_input(
            label="Máx. repeticiones de un ejercicio en la semana:",
            min_value=1,
            step=1,
            key='max_repetitions_per_exercise_weekly',
            on_change=on_change_callback,
            help="Número máximo de veces que un mismo ejercicio puede aparecer en la rutina semanal. '1' significa que no se repetirá."
        )
        st.number_input(
            "Máximo de series totales por día:",
            min_value=1,
            step=1,
            key='max_series_day_input',
            on_change=on_change_callback,
            help="Número máximo de series que puedes hacer en un solo día."
        )
        st.number_input(
            "Máximo de series por grupo muscular por día:",
            min_value=1,
            step=1,
            key='max_series_grupo_dia_input',
            on_change=on_change_callback,
            help="Número máximo de series para un grupo muscular en un solo día. Ayuda a distribuir el volumen."
        )

    with st.sidebar.expander("2️⃣ Selección de Días y Grupos Musculares", expanded=True):
        st.multiselect(
            label="Selecciona los días de entrenamiento:",
            options=WEEK_DAYS,
            key='selected_weeks_day',
            on_change=on_change_callback,
            placeholder="Escoge tus días"
        )
        st.multiselect(
            "Selecciona los grupos musculares a entrenar:",
            options=all_muscle_groups,
            key='selected_muscle_groups',
            on_change=on_change_callback,
            placeholder="Escoge los grupos musculares"
        )

    with st.sidebar.expander("3️⃣ Asignación y Series Semanales", expanded=True):
        st.subheader("Asignación de Grupos por Día")
        if not st.session_state.selected_weeks_day:
            st.info("Selecciona al menos un día de entrenamiento para asignar grupos musculares.")
        else:
            for day in st.session_state.selected_weeks_day:
                st.session_state.group_per_day[day] = st.multiselect(
                    f"Grupos musculares para {day}:",
                    options=st.session_state.selected_muscle_groups,
                    default=st.session_state.group_per_day.get(day, []),
                    key=f"day_{day}_groups",
                    on_change=on_change_callback,
                    placeholder="Asigna grupos a este día"
                )

        st.subheader("Series Semanales Exactas")
        if not st.session_state.selected_muscle_groups:
            st.info("Selecciona al menos un grupo muscular para definir las series.")
        else:
            for group in sorted(st.session_state.selected_muscle_groups):
                st.number_input(
                    f"Series exactas para {group}:",
                    min_value=0,
                    value=st.session_state.exact_series_group.get(group, DEFAULT_EXACT_SERIES_VALUE),
                    step=1,
                    key=f"exact_series_{group}",
                    on_change=on_change_callback
                )
            
            new_exact_series = {}
            for group in st.session_state.selected_muscle_groups:
                widget_key = f"exact_series_{group}"
                series_value = st.session_state.get(widget_key, 0)
                if series_value > 0:
                    new_exact_series[group] = series_value
            
            st.session_state.exact_series_group = new_exact_series
