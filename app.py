from datetime import date
import json
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import HTMXTemplate
from litestar import get, post, Litestar
from litestar.response import Template

from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig

from pathlib import Path

from models import Schedule, Week
from scheduling import solve_schedule

def get_schedule_from_file() -> Schedule:
    """Returns the schedule, seed it if it doesn't exist"""
    if not Path("schedule.json").exists():
        schedule = Schedule()
        schedule.add_seed_data()
        save_schedule_to_file(schedule)
    with open("schedule.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        return Schedule(**data)

def save_schedule_to_file(schedule: Schedule) -> None:
    """Saves the schedule to the file"""
    with open("schedule.json", "w", encoding="utf-8") as f:
        f.write(schedule.model_dump_json())

def solve_and_save(schedule: Schedule) -> None:
    """Solves the schedule"""
    save_schedule_to_file(solve_schedule(schedule))

def convert_schedule_to_context(schedule: Schedule) -> dict:
    """Converts a schedule to a context dict"""
    context = {}
    # Add "devs" to context
    context["devs"] = [dev.name for dev in schedule.get_devs_sorted()]
    # add "schedule" to context
    context["schedule"] = []
    for week in schedule.get_weeks_sorted():
        assignments_obj = {"assignments": {}}
        assignments = schedule.get_assignments_for_week_sorted_by_developer(week)
        for assignment in assignments:
            assignments_obj["assignments"][assignment.developer.name] = "On" if assignment.on_support else "Off"
        assignments_obj["date_range"] = week.datestring_of_week()
        context["schedule"].append(assignments_obj)
    return context

@get(path="/table")
async def get_table(request: HTMXRequest) -> Template:
    return HTMXTemplate(
        template_name="partial.html",
        context=convert_schedule_to_context(get_schedule_from_file()),
    )


@get(path="/")
async def get_home(request: HTMXRequest) -> Template:
    return HTMXTemplate(
        template_name="index.html",
        context=convert_schedule_to_context(get_schedule_from_file()),
        push_url="/",
    )

@get(path='/solve')
async def solve(request: HTMXRequest) -> Template:
    schedule = get_schedule_from_file()
    solve_and_save(schedule)
    schedule = get_schedule_from_file()
    return HTMXTemplate(
        template_name="index.html",
        context=convert_schedule_to_context(schedule),
        push_url="/",
    )

@post(path="/vacation")
async def register_vacation(request: HTMXRequest) -> None:
    values = await request.form()
    first_date_str = values["week"].split()[0]
    first_date: date = date.fromisoformat(first_date_str)
    week = Week(first_day=first_date)
    sched = get_schedule_from_file()
    sched.add_developer_preference(values["dev"], week, -2)
    save_schedule_to_file(sched)
    return HTMXTemplate(template_name="submitted.html")



app = Litestar(
    route_handlers=[get_table, get_home, solve, register_vacation],
    debug=True,
    request_class=HTMXRequest,
    template_config=TemplateConfig(
        directory=Path("litestar_htmx/templates"),
        engine=JinjaTemplateEngine,
    ),
)
