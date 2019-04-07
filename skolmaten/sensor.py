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
from collections import OrderedDict

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
        # Using ordered dict since order matters
        #self.hass.data[self._name] = {}
        self.hass.data[self._name] = OrderedDict()
        self.update()


    def update(self):
        import feedparser
        parsedFeed = feedparser.parse(self._feed)

        if not parsedFeed :
            return False
        else:
            self._state = len(parsedFeed.entries)
            #self.hass.data[self._name] = {}
            self.hass.data[self._name] = OrderedDict()

            # Process the RSS feed
            for entry in parsedFeed.entries:
                title = entry['title'] if entry['title'] else entry['description']

                if not title:
                  continue

                self.hass.data[self._name][title] = {}

                for key, value in entry.items():
                  _LOGGER.debug("Have key %s: value %s" % (key, value))
                  if (self._inclusions and key not in self._inclusions) or ('parsed' in key) or (key in self._exclusions):
                    continue

                  if key in ['published', 'updated', 'created', 'expired']:
                    value = parser.parse(value).replace(tzinfo=None).strftime(self._date_format)

                  self.hass.data[self._name][title][key] = value

            # TODO This must be cleaned up ! Currently just a hack to get things going
            #_LOGGER.debug("Testing list %s" % (list(self.hass.data[self._name].items())[0][1]))
            #_LOGGER.debug("Testing list %s" % (list(self.hass.data[self._name].items())[1][1]))
            for i in range(self._state):
                day = list(self.hass.data[self._name].items())[i][1]['published'].split(",")[0]
                #_LOGGER.debug("Testing day %s:%s" % (day, SENSOR_TYPES[self._sensor_type][0]))
                if day == SENSOR_TYPES[self._sensor_type][0]:
                    #day, week = list(self.hass.data[self._name].items())[i][1]['title'].split(" - ")
                    summary = list(self.hass.data[self._name].items())[i][1]['summary']
                    # Replace <br/> with .
                    summary = summary.replace("<br/>", ".")
                    #self._state = day + " " + week + ": " + str(summary)
                    self._state = title + ": " + str(summary)
                    self._state = self._state[:250]
                    _LOGGER.debug("Built state %s" % (self._state))
                i=i+1

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
