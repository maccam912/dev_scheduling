import sched
from ortools.sat.python import cp_model
from models import Assignment, Developer, Schedule, Week

def print_solution(solver, weeks, num_devs, num_weeks):
    print("Week ", end="")
    for d in range(num_devs):
        print(f"  Dev{d}", end="")
    print()
    
    for w in range(num_weeks):
        print(f"{w:4}", end="")
        for d in range(num_devs):
            if solver.Value(weeks[(d, w)]) == 1:
                print("     O", end="")
            else:
                print("     .", end="")
        print()

def assignment_for(dev: Developer, week: Week, assignments: list[Assignment]):
    for assignment in assignments:
        if assignment.developer.name == dev.name and assignment.week.first_day == week.first_day:
            return assignment
    breakpoint()


def solve_schedule(schedule: Schedule) -> Schedule | None:
    """Solves the schedule"""
    model = cp_model.CpModel()

    vars = {}

    for assignment in schedule.assignments:
        vars[assignment] = model.NewBoolVar(f"support_{assignment.developer.name}_{assignment.week.datestring_of_first_day()}")
    
    for w in schedule.weeks:
        model.Add(sum([vars[assignment] for assignment in schedule.get_assignments_for_week(w)]) == 2)
    
    max_shifts_per_dev = 8
    for d in schedule.developers:
        dev_assignments = []
        for assignment in schedule.assignments:
            if assignment.developer == d:
                dev_assignments.append(vars[assignment])
        model.Add(sum(dev_assignments) <= max_shifts_per_dev)
    
    for d in schedule.developers:
        weeks = schedule.get_weeks_sorted()
        for i in range(2, len(weeks)):
            w1 = weeks[i-2]
            w2 = weeks[i-1]
            w3 = weeks[i]

            model.Add((vars[assignment_for(d, w1, schedule.assignments)] + vars[assignment_for(d, w3,  schedule.assignments)]) >= vars[assignment_for(d, w2, schedule.assignments)])
            model.Add(vars[assignment_for(d, w1, schedule.assignments)] + vars[assignment_for(d, w3, schedule.assignments)] <= 1)

        for i in range(4, len(weeks)):
            w1 = weeks[i-4]
            w2 = weeks[i-3]
            w3 = weeks[i-2]
            w4 = weeks[i-1]
            w5 = weeks[i]

            assignment_vars = [vars[assignment_for(d, w, schedule.assignments)] for w in [w1, w2, w3, w4, w5]]
            model.Add(sum(assignment_vars) <= 2)
    
    for d in schedule.developers:
        for preference in d.preferences:
            if preference.sentiment == -2:
                model.Add(vars[assignment_for(d, preference.week, schedule.assignments)] == 0)
            if preference.sentiment == 2:
                model.Add(vars[assignment_for(d, preference.week, schedule.assignments)] == 1)

    solver = cp_model.CpSolver()

    if solver.Solve(model) == cp_model.OPTIMAL:
        new_schedule = schedule.model_copy()
        for assignment in new_schedule.assignments:
            if  solver.Value(vars[assignment]) == 1:
                assignment.on_support = True
            else:
                assignment.on_support = False
        return new_schedule
    return None

        # print_solution(solver, schedule.weeks, num_devs, num_weeks)
        # print("Max Difference in total weeks on support among devs: ", solver.Value(max_diff))
        # print("Total Objective: ", solver.Value(total_objective))