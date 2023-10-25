from datetime import date, timedelta
from enum import Enum
from pydantic import BaseModel

class Week(BaseModel):
    """A week of the schedule"""
    first_day: date

    def datestring_of_first_day(self) -> str:
        """Returns the datestring of the first day of the week"""
        return self.first_day.strftime("%Y-%m-%d")
    
    def datestring_of_last_day(self) -> str:
        """Returns the datestring of the last day of the week"""
        return (self.first_day + timedelta(days=6)).strftime("%Y-%m-%d")
    
    def datestring_of_week(self) -> str:
        """Returns the datestring of the week"""
        return f"{self.datestring_of_first_day()} to {self.datestring_of_last_day()}"
    
    def __hash__(self) -> int:
        return self.datestring_of_first_day().__hash__()
    
    def __eq__(self, __value: object) -> bool:
        return self.first_day == __value.first_day

class SentimentEnum(int, Enum):
    """An enum for sentiment"""
    VERY_POSITIVE = 2
    POSITIVE = 1
    NEUTRAL = 0
    NEGATIVE = -1
    VERY_NEGATIVE = -2

class Preferences(BaseModel):
    """A developer's preference for a week"""
    week: Week
    sentiment: SentimentEnum

    def __hash__(self) -> int:
        return (self.week, self.sentiment).__hash__()

class Developer(BaseModel):
    """A developer"""
    name: str
    preferences: set[Preferences]

    def __hash__(self) -> int:
        return self.name.__hash__()
    
    def __eq__(self, __value: object) -> bool:
        self.name == __value.name

class Assignment(BaseModel):
    """A support assignment for a developer"""
    developer: Developer
    week: Week
    on_support: bool

    def __hash__(self) -> int:
        return (self.developer,  self.week).__hash__()

class Schedule(BaseModel):
    weeks: set[Week] = set()
    developers: set[Developer] = set()
    assignments: set[Assignment] = set()
    
    def add_seed_data(self) -> None:
        """Add base data to the schedule"""
        # Add developers
        for name in ["Matt Davis", "Matt Koski", "Eric",  "Nick",  "Himani", "Abhi"]:
            self.developers.add(Developer(name=name, preferences=set()))
        first_day = date.today() - timedelta(days=7*12)
        # Add weeks
        for i in range(24):
            # Get date of the sunday prior to first_day + timedelta(days=7*i)
            prior_sunday = first_day + timedelta(days=7*i) - timedelta(days=first_day.weekday())
            self.weeks.add(Week(first_day=prior_sunday))
        
        # add assignments
        for week in self.get_weeks_sorted():
            for dev in self.developers:
                self.assignments.add(Assignment(developer=dev, week=week, on_support=False))

    def get_week_containing_day(self, day: date) -> Week:
        """Returns the week containing the given day"""
        for week in self.get_weeks_sorted():
            if week.first_day <= day <= week.first_day + timedelta(days=6):
                return week

    def get_devs_sorted(self) -> list[Developer]:
        """Returns the developers sorted by name"""
        return sorted(self.developers, key=lambda dev: dev.name)

    def get_weeks_sorted(self) -> list[Week]:
        """Returns the weeks sorted by first day"""
        return sorted(self.weeks, key=lambda week: week.first_day)

    def get_assignments_for_week(self, week: Week) -> set[Assignment]:
        """Returns the assignments for the given week"""
        return {assignment for assignment in self.assignments if assignment.week == week}
    
    def get_assignments_for_week_sorted_by_developer(self, week: Week) -> list[Assignment]:
        """Returns the assignments for the given week, sorted by developer"""
        return sorted(self.get_assignments_for_week(week), key=lambda assignment: assignment.developer.name)
    
    def get_assignments_for_day(self, day: date) -> set[Assignment]:
        """Returns the assignments for the given day"""
        week = self.get_week_containing_day(day)
        return self.get_assignments_for_week(week)
    
    def get_dev_by_name(self, name: str) -> Developer:
        """Returns the developer with the given name"""
        for dev in self.developers:
            if dev.name == name:
                return dev
    
    def add_developer_preference(self, developer_name: str, week: Week, sentiment: int) -> None:
        """Adds a developer preference"""
        dev = self.get_dev_by_name(developer_name)
        dev.preferences.add(Preferences(week=week, sentiment=sentiment))