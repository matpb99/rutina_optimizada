import streamlit as st
import pandas as pd
from data import PENALTY_LEVELS, DAY_COLORS


def display_exercise_manager(all_muscle_groups):
    with st.container():
        st.header("🏋️‍♀️ Gestión de Ejercicios")
        st.write("Filtra y selecciona los ejercicios a incluir en la rutina. Los ejercicios solo aparecerán si su grupo muscular fue seleccionado en la barra lateral.")

    with st.expander("➕ Añadir Nuevo Ejercicio"):
        new_exercise_name = st.text_input(
            "Nombre del Ejercicio:", key="new_exercise_name")
        new_exercise_group = st.selectbox(
            "Grupo Muscular:",
            options=all_muscle_groups + ["(Nuevo Grupo Muscular)"],
            index=0 if all_muscle_groups else None,
            key="new_exercise_group"
        )
        if new_exercise_group == "(Nuevo Grupo Muscular)":
            new_exercise_group_custom = st.text_input(
                "Nombre del Nuevo Grupo Muscular:", key="new_exercise_group_custom")
            if new_exercise_group_custom:
                new_exercise_group = new_exercise_group_custom

        if st.button("Añadir Ejercicio a la Lista", key="add_exercise_button"):
            if new_exercise_name and new_exercise_group and new_exercise_group != "(Nuevo Grupo Muscular)":
                is_new_group = new_exercise_group not in all_muscle_groups

                st.session_state.exercises[new_exercise_name] = new_exercise_group
                st.success(
                    f"Ejercicio '{new_exercise_name}' añadido a '{new_exercise_group}'.")

                if is_new_group:
                    if new_exercise_group not in st.session_state.selected_muscle_groups:
                        st.session_state.selected_muscle_groups.append(
                            new_exercise_group)
                    st.rerun()
            else:
                st.error(
                    "Por favor, introduce un nombre de ejercicio y un grupo muscular válido.")

    st.subheader("Lista de Ejercicios para la Rutina")

    exercises_data = []
    for name, group in st.session_state.exercises.items():
        if group in st.session_state.selected_muscle_groups:
            exercises_data.append(
                {"Seleccionar": True, "Ejercicio": name, "Grupo Muscular": group, "Clave": False})

    if exercises_data:
        exercises_df = pd.DataFrame(exercises_data).sort_values(
            by="Grupo Muscular").reset_index(drop=True)
    else:
        exercises_df = pd.DataFrame(
            columns=["Seleccionar", "Ejercicio", "Grupo Muscular", "Clave"])

    edited_df = st.data_editor(
        exercises_df,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("Incluir", default=True),
            "Clave": st.column_config.CheckboxColumn("Clave", default=False)
        },
        hide_index=True,
        use_container_width=True,
        key='data_editor'
    )

    if not edited_df.empty:
        selected_exercises_names = edited_df[edited_df["Seleccionar"]]["Ejercicio"].tolist(
        )
        key_exercises = edited_df[edited_df["Clave"]]["Ejercicio"].tolist()

        exercises_for_optimization = {
            name: st.session_state.exercises[name]
            for name in selected_exercises_names
            if name in st.session_state.exercises and st.session_state.exercises[name] in st.session_state.selected_muscle_groups
        }
    else:
        exercises_for_optimization = {}
        key_exercises = []

    return exercises_for_optimization, key_exercises


def display_penalty_manager():
    with st.container():
        st.header("🚫 Ejercicios Incompatibles (Penalizaciones)")

        with st.expander("➕ Añadir Penalización"):
            available_exercises = sorted([
                name for name, group in st.session_state.exercises.items()
                if group in st.session_state.selected_muscle_groups
            ])

            if not available_exercises:
                st.info(
                    "Para añadir penalizaciones, primero selecciona los grupos musculares en la barra lateral.")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    penalty_exercise_1 = st.selectbox(
                        "Ejercicio 1:", options=available_exercises, key="ej1_pen")
                with col2:
                    penalty_exercise_2 = st.selectbox(
                        "Ejercicio 2:", options=available_exercises, key="ej2_pen")
                with col3:
                    penalty_level = st.selectbox("Nivel de Penalización:", options=list(
                        PENALTY_LEVELS.keys()), key="nivel_pen")

                if st.button("Añadir Penalización", key="add_penalty_button"):
                    if penalty_exercise_1 and penalty_exercise_2 and penalty_exercise_1 != penalty_exercise_2:
                        key = tuple(
                            sorted((penalty_exercise_1, penalty_exercise_2)))
                        st.session_state.penalties[key] = PENALTY_LEVELS[penalty_level]
                        st.success(
                            f"Penalización añadida: {penalty_exercise_1} y {penalty_exercise_2} con nivel {penalty_level}.")
                        st.rerun()
                    else:
                        st.error(
                            "Por favor, selecciona dos ejercicios diferentes para la penalización.")

        st.subheader("Penalizaciones Actuales")
        if st.session_state.penalties:
            penalties_data = []
            for (e1, e2), value in st.session_state.penalties.items():
                level = [k for k, v in PENALTY_LEVELS.items() if v == value][0]
                penalties_data.append(
                    {"Ejercicio 1": e1, "Ejercicio 2": e2, "Nivel": level})
            penalties_df = pd.DataFrame(penalties_data)
            st.dataframe(penalties_df, hide_index=True,
                         use_container_width=True)

            if st.button("Limpiar Penalizaciones", key="clear_penalties_button"):
                st.session_state.penalties = {}
                st.success("Todas las penalizaciones han sido eliminadas.")
                st.rerun()
        else:
            st.info("No hay penalizaciones configuradas actualmente.")


def display_results(problem, series, penalized):
    from pulp import LpStatus, value, lpSum
    st.subheader("Resultados de la Optimización")

    if LpStatus[problem.status] == "Optimal":
        st.success("Se pudo encontrar una combinación válida 🎉")

        total_series_global = 0

        for i in range(0, len(st.session_state.selected_weeks_day), 3):
            cols = st.columns(3)
            for j, d in enumerate(st.session_state.selected_weeks_day[i:i+3]):
                with cols[j]:
                    st.markdown(
                        f"### 📅 **<span style='color:{DAY_COLORS.get(d, '#28a745')};'>Día: {d}</span>**", unsafe_allow_html=True)
                    series_per_group_day = {
                        group: 0 for group in st.session_state.exact_series_group.keys()}
                    total_series_day = 0
                    exercises_day_data = []

                    for e in st.session_state.exercises_for_optimization:
                        n = series[(e, d)].varValue
                        if n and n > 0:
                            exercises_day_data.append(
                                {"Ejercicio": e, "Series": int(n)})
                            exercise_group = st.session_state.exercises_for_optimization[e]
                            if exercise_group in series_per_group_day:
                                series_per_group_day[exercise_group] += int(n)
                            total_series_day += int(n)

                    if exercises_day_data:
                        df_exercises = pd.DataFrame(exercises_day_data)
                        st.dataframe(df_exercises, hide_index=True,
                                     use_container_width=True)
                    else:
                        st.info("No hay ejercicios asignados para este día.")

                    st.markdown("--- Series por grupo ---")
                    series_group_data = []
                    for group, s in series_per_group_day.items():
                        if s > 0:
                            series_group_data.append(
                                {"Grupo Muscular": group, "Series": s})

                    if series_group_data:
                        df_series_group = pd.DataFrame(series_group_data)
                        st.dataframe(df_series_group, hide_index=True,
                                     use_container_width=True)
                    else:
                        st.write(
                            "No hay series asignadas a grupos musculares para este día.")

                    st.markdown(
                        f"**💪 Total series del día: {total_series_day}**")
                total_series_global += total_series_day

        total_penalty_calc = lpSum([
            st.session_state.penalties[(e1, e2)] *
            penalized[(e1, e2, d)].varValue
            for (e1, e2) in st.session_state.penalties
            for d in st.session_state.selected_weeks_day
            if (e1, e2, d) in penalized and penalized[(e1, e2, d)].varValue is not None
        ])
        value(total_penalty_calc)

        st.divider()
        st.markdown("### 📊 Resumen General")
        st.metric(label="Total de Series en la Semana",
                  value=total_series_global)

    else:
        st.error("No fue posible encontrar una combinación válida 😔")
        st.write("El modelo no fue capaz de encontrar una solución que pueda cumplir con todas las condiciones. Considera revisar la cantidad de series diarias máximas por grupo muscular, las series diarias máximas totales, las series semanales totales de cada grupo muscular y los ejercicios que no puedan estar juntos el mismo día (penalizaciones).")

    st.divider()
    st.markdown("**Nota:** Este optimizador utiliza programación lineal entera para encontrar la mejor combinación de ejercicios de acuerdo al número máximo de series por grupo muscular al día, el número máximo de series totales al día, los grupos musculares seleccionados para cada día, el número de series semanales totales por grupo muscular y los ejercicios que no pueden estar juntos el mismo día (penalizaciones).")
