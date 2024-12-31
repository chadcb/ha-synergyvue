"""Support for StudentVUE Data."""
from datetime import timedelta
import logging

from synergyvue import StudentVUE
import voluptuous as vol

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = "synergyvue"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform in Home Assistant for StudentVUE Information."""
    data = StudentVueData(
        hass, config[CONF_USERNAME], config[CONF_PASSWORD], config[CONF_HOST]
    )

    data.update()
    student_id = data.sv_data["id"]
    if student_id:
        student_sensor_name = f"studentvue_{student_id}"
    else:
        return None

    sensors = [
        StudentVueSensor(hass, data, f"{student_sensor_name}"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_1_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_1_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_2_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_2_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_3_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_3_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_4_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_4_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_5_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_5_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_6_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_6_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_7_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_7_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_8_x"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_period_8_y"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_gpa"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_grade"),
        StudentVueSensor(hass, data, f"{student_sensor_name}_missing_assignments"),
    ]

    add_entities(sensors, True)


class StudentVueSensor(Entity):
    """StudentVUE Sensor."""

    def __init__(self, hass, data, name):
        self._data = data
        self._device_state_attributes = None
        self._icon = "mdi:school"
        self._name = name
        self._state = "off"
        self._hass = hass
        self.entity_id = f"sensor.{name}"

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def state(self):
        """Return the state."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._device_state_attributes

    @property
    def icon(self):
        """Return the icon."""
        return self._icon

    def update(self):
        """Update data"""
        self._data.update()

        # Set sensor data based on type
        if "_period_" in self.entity_id:
            try:
                self._device_state_attributes = {}
                course_period = self.entity_id.split("_", 2)[2]
                self._state = self._data.sv_data["courses"][course_period][
                    "grade_letter"
                ]
                for k, v in self._data.sv_data["courses"][course_period].items():
                    self._device_state_attributes[k] = v

                self._name = self._data.sv_data["courses"][course_period][
                    "course_title"
                ]
                return
            except:
                return

        if "_gpa" in self.entity_id:
            self._name = "GPA"
            self._state = self._data.sv_data["gpa"]
            return

        if "_missing_assignments" in self.entity_id:
            self._name = "Missing Assignments"
            self._state = self._data.sv_data["missing_assignments"]
            return

        if "_grade" in self.entity_id:
            self._name = "Grade"
            self._state = self._data.sv_data["grade"]
            return

        self._name = self._data.sv_data["name"]
        self._state = self._data.sv_data["meeting_day"]

        self._device_state_attributes = {
            "full_name": self._data.sv_data["full_name"],
            "gpa": self._data.sv_data["gpa"],
            "grade": self._data.sv_data["grade"],
            "id": self._data.sv_data["id"],
            "last_updated": self._data.sv_data["last_updated"],
            "meeting_date": self._data.sv_data["meeting_date"],
            "missing_assignments": self._data.sv_data["missing_assignments"],
            "name": self._data.sv_data["name"],
            "reporting_period": self._data.sv_data["reporting_period"],
            "reporting_period_end": self._data.sv_data["reporting_period_end"],
            "reporting_period_start": self._data.sv_data["reporting_period_start"],
            "school": self._data.sv_data["school"],
            "url": self._data.sv_data["url"],
        }


class StudentVueData:
    """Fetch student data from synergyvue."""

    def __init__(self, hass, username, password, host):
        self._data = {}
        self._hass = hass
        self._host = host
        self._password = password
        self._sv = None
        self._username = username

    @property
    def sv_data(self):
        """Return hass.data."""
        return self._data

    @staticmethod
    def _courses_by_period(courses, max_courses=8):
        """Organize courses by periods and alt schedules."""
        periods = []
        periods_xy = {}
        for i in range(1, max_courses + 1):
            x = f"period_{i}_x"
            y = f"period_{i}_y"
            periods_xy[x] = {}
            periods_xy[y] = {}

        for course, course_data in courses.items():
            period = course_data["period"]
            if period not in periods:
                period_name = f"period_{course_data['period']}_x"
                periods.append(period)
            else:
                period_name = f"period_{course_data['period']}_y"
            periods_xy[period_name]["course_title"] = course
            for k, v in course_data.items():
                periods_xy[period_name][k] = v
        return periods_xy

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get latest data from StudentVUE."""
        try:
            self._sv = StudentVUE(self._username, self._password, self._host)
        except:
            return None

        self._data["course_count"] = self._sv.course_count
        self._data["courses"] = StudentVueData._courses_by_period(self._sv.courses)
        self._data["full_name"] = self._sv.full_name
        self._data["gpa"] = self._sv.gpa
        self._data["grade"] = self._sv.grade
        self._data["id"] = self._sv.id
        self._data["last_updated"] = self._sv.last_updated
        self._data["meeting_date"] = self._sv.meeting_date
        self._data["meeting_day"] = self._sv.meeting_day
        self._data["missing_assignments"] = self._sv.missing_assignments
        self._data["name"] = self._sv.first_name
        self._data["reporting_period"] = self._sv.reporting_period
        self._data["reporting_period_end"] = self._sv.reporting_period_end
        self._data["reporting_period_start"] = self._sv.reporting_period_start
        self._data["school"] = self._sv.school_name
        self._data["url"] = self._sv.url
