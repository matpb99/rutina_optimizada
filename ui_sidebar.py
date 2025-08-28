import streamlit as st
import pandas as pd
from data import DEFAULT_EXACT_SERIES_VALUE, WEEK_DAYS


def display_sidebar(all_muscle_groups, on_change_callback):
    st.sidebar.header("⚙️ Configuración de Rutina")
    st.sidebar.write("Ajusta los parámetros para generar tu rutina personalizada.")

    with st.sidebar.expander("1️⃣ Configuración General", expanded=True):
        st.number_input(
            label="Máx. días de un ejercicio en la semana:",
            min_value=1,
            step=1,
            key="max_days_per_exercise_weekly",
            on_change=on_change_callback,
            help="Número máximo de veces que un mismo ejercicio puede aparecer en la rutina semanal. '1' significa que no se repetirá.",
        )
        st.number_input(
            "Máximo de series totales por día:",
            min_value=1,
            step=1,
            key="max_series_day_input",
            on_change=on_change_callback,
            help="Número máximo de series que puedes hacer en un solo día.",
        )
        st.number_input(
            "Máximo de series por grupo muscular por día:",
            min_value=1,
            step=1,
            key="max_series_grupo_dia_input",
            on_change=on_change_callback,
            help="Número máximo de series para un grupo muscular en un solo día. Ayuda a distribuir el volumen.",
        )

    with st.sidebar.expander("2️⃣ Selección de Días y Grupos Musculares", expanded=True):
        st.multiselect(
            label="Selecciona los días de entrenamiento:",
            options=WEEK_DAYS,
            key="selected_weeks_day",
            on_change=on_change_callback,
            placeholder="Escoge tus días",
        )
        st.multiselect(
            "Selecciona los grupos musculares a entrenar:",
            options=all_muscle_groups,
            key="selected_muscle_groups",
            on_change=on_change_callback,
            placeholder="Escoge los grupos musculares",
        )

    with st.sidebar.expander("3️⃣ Asignación y Series Semanales", expanded=True):
        st.subheader("Asignación de Grupos por Día")
        if (
            not st.session_state.selected_weeks_day
            or not st.session_state.selected_muscle_groups
        ):
            st.info(
                "Para continuar, selecciona los días y grupos musculares que entrenarás."
            )
        else:
            days = st.session_state.selected_weeks_day
            groups = st.session_state.selected_muscle_groups

            # Create a dictionary for the DataFrame data
            data_for_df = {}
            for group in groups:
                # For each group, create a list of booleans indicating if it's assigned to each day
                data_for_df[group] = [
                    group in st.session_state.group_per_day.get(day, []) for day in days
                ]

            # Create the DataFrame with groups as columns and days as index
            assignment_df = pd.DataFrame(data_for_df, index=days)

            st.data_editor(
                assignment_df,
                key="day_group_assignment_editor",
                use_container_width=True,
            )

        st.subheader("Series Semanales Exactas")
        if not st.session_state.selected_muscle_groups:
            st.info("Selecciona al menos un grupo muscular para definir las series.")
        else:
            series_data = {
                "Grupo Muscular": st.session_state.selected_muscle_groups,
                "Series": [
                    st.session_state.exact_series_group.get(
                        g, DEFAULT_EXACT_SERIES_VALUE
                    )
                    for g in st.session_state.selected_muscle_groups
                ],
            }
            series_df = pd.DataFrame(series_data)

            st.data_editor(
                series_df,
                key="series_editor",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Grupo Muscular": st.column_config.TextColumn(disabled=True),
                    "Series": st.column_config.NumberColumn(min_value=0, step=1),
                },
            )
