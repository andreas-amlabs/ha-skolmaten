"""
A component which allows you to parse the RSS feed from "skolmaten" into a sensor

This component is based on the work of
https://github.com/custom-components/sensor.feedparser
"""

import logging
import voluptuous as vol
from datetime import timedelta
from dateutil import parser
from time import strftime
from subprocess import check_output
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)

from homeassistant.const import CONF_MONITORED_CONDITIONS


__version__ = '0.0.4'
_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['feedparser']

SENSOR_TYPES = {
    'monday': ['Mon', None],
    'tuesday': ['Tue', None],
    'wednesday': ['Wed', None],
    'thursday': ['Thu', None],
    'friday': ['Fri', None],
}

CONF_NAME = 'name'
CONF_FEED_URL = 'feed_url'
CONF_DATE_FORMAT = 'date_format'
CONF_INCLUSIONS = 'inclusions'
CONF_EXCLUSIONS = 'exclusions'

DEFAULT_SCAN_INTERVAL = timedelta(hours=4)

COMPONENT_REPO = 'https://github.com/andreas-amlabs/ha-skolmaten'
SCAN_INTERVAL = timedelta(hours=4)
ICON = 'mdi:rss'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_FEED_URL): cv.string,
    vol.Required(CONF_DATE_FORMAT, default='%a, %b %d %I:%M %p'): cv.string,
    vol.Optional(CONF_INCLUSIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUSIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_MONITORED_CONDITIONS, default=[]): vol.All(cv.ensure_list, vol.Length(min=1), [vol.In(SENSOR_TYPES)]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    #name = config.get(CONF_NAME)
    dev = []
    for sensor_type in config[CONF_MONITORED_CONDITIONS]:
        dev.append(SkolmatenSensor(hass, config, sensor_type))

    add_devices(dev)

class SkolmatenSensor(Entity):
    def __init__(self, hass, config, sensor_type):
        self.hass = hass
        self._feed = config[CONF_FEED_URL]
        self._name = config[CONF_NAME] + "_" + str(sensor_type)
        self._sensor_type = sensor_type
        self._date_format = config[CONF_DATE_FORMAT]
        self._inclusions = config[CONF_INCLUSIONS]
        self._exclusions = config[CONF_EXCLUSIONS]
        self._state = None
        self.hass.data[self._name] = {}
        #_LOGGER.debug("New instance: %s" % (self._name))
        self.update()


    def update(self):
        import feedparser
        parsedFeed = feedparser.parse(self._feed)

        if not parsedFeed :
            return False
        else:
            self._state = len(parsedFeed.entries)
            self.hass.data[self._name] = {}
            #_LOGGER.debug("Updating sensor %s" % (self._sensor_type))

            # Process the RSS feed
            for entry in parsedFeed.entries:
                title = entry['title']
                #_LOGGER.debug("Processing %s" % (title))

                if not title:
                  continue

                day = entry['published']

                if not day:
                  continue

                day = day.split(",")[0]

                # Is this the day this sensor matches ?
                if day == SENSOR_TYPES[self._sensor_type][0]:
                    # Should try here ...
                    summary = entry['summary']
                    if summary:
                        summary = summary.replace("<br/>", ".")

                    self._state = title + ": " + str(summary)
                    self._state = self._state[:250]
                    self.hass.data[self._name][title] = {'day': day, 'summary': summary}
                    #_LOGGER.debug("Built state %s" % (self._state))
                    break

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        return self.hass.data[self._name]
