from pulp import LpVariable, LpProblem, LpMaximize, lpSum


def run_optimization(
    days,
    group_per_day,
    exercises,
    exact_series_per_group,
    max_series_per_day,
    max_series_per_group_per_day,
    penalties,
    max_days_per_exercise_weekly,
    key_exercises,
):
    series = LpVariable.dicts(
        "Series",
        [(e, d) for e in exercises for d in days],
        cat="Integer",
        lowBound=0,
        upBound=4,
    )
    executed = LpVariable.dicts(
        "Executed", [(e, d) for e in exercises for d in days], cat="Binary"
    )

    problem = LpProblem("Optimized_Gym_Routine", LpMaximize)

    for e in exercises:
        for d in days:
            problem += series[(e, d)] >= 3 * executed[(e, d)]
            problem += series[(e, d)] <= 4 * executed[(e, d)]

    for d in days:
        groups_day = group_per_day[d]
        for e in exercises:
            if exercises[e] not in groups_day:
                problem += series[(e, d)] == 0
                problem += executed[(e, d)] == 0

    for d in days:
        problem += lpSum(series[(e, d)] for e in exercises) <= max_series_per_day

    for d in days:
        for group in set(exercises.values()):
            exercises_in_group = [e for e in exercises if exercises[e] == group]
            if group in group_per_day[d]:
                problem += (
                    lpSum(series[(e, d)] for e in exercises_in_group)
                    <= max_series_per_group_per_day
                )

    for group in set(exercises.values()):
        exercises_in_group = [e for e in exercises if exercises[e] == group]

        group_has_key_exercise = any(e in key_exercises for e in exercises_in_group)

        if group in exact_series_per_group and exact_series_per_group[group] > 0:
            problem += (
                lpSum(series[(e, d)] for e in exercises_in_group for d in days)
                == exact_series_per_group[group]
            )

        elif group not in exact_series_per_group and not group_has_key_exercise:
            problem += (
                lpSum(series[(e, d)] for e in exercises_in_group for d in days) == 0
            )

    for e_key in key_exercises:
        problem += lpSum(executed[(e_key, d)] for d in days) >= 1

    for e in exercises:
        problem += lpSum(executed[(e, d)] for d in days) <= max_days_per_exercise_weekly

    penalized = LpVariable.dicts(
        "Penalized", [(e1, e2, d) for (e1, e2) in penalties for d in days], cat="Binary"
    )

    for e1, e2 in penalties:
        for d in days:
            problem += penalized[(e1, e2, d)] <= executed[(e1, d)]
            problem += penalized[(e1, e2, d)] <= executed[(e2, d)]
            problem += (
                penalized[(e1, e2, d)] >= executed[(e1, d)] + executed[(e2, d)] - 1
            )

    problem += lpSum(series[(e, d)] for e in exercises for d in days) - lpSum(
        [
            penalties[(e1, e2)] * penalized[(e1, e2, d)]
            for (e1, e2) in penalties
            for d in days
        ]
    )

    status = problem.solve()

    return problem, series, penalized, status
