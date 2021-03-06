"""Test MQTT fans."""
import unittest

from homeassistant.setup import setup_component
from homeassistant.components import fan
from homeassistant.components.mqtt.discovery import async_start
from homeassistant.const import ATTR_ASSUMED_STATE, STATE_UNAVAILABLE

from tests.common import (
    mock_mqtt_component, async_fire_mqtt_message, fire_mqtt_message,
    get_test_home_assistant)


class TestMqttFan(unittest.TestCase):
    """Test the MQTT fan platform."""

    def setUp(self):  # pylint: disable=invalid-name
        """Set up things to be run when tests are started."""
        self.hass = get_test_home_assistant()
        self.mock_publish = mock_mqtt_component(self.hass)

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        self.hass.stop()

    def test_default_availability_payload(self):
        """Test the availability payload."""
        assert setup_component(self.hass, fan.DOMAIN, {
            fan.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'availability_topic': 'availability_topic'
            }
        })

        state = self.hass.states.get('fan.test')
        self.assertEqual(STATE_UNAVAILABLE, state.state)

        fire_mqtt_message(self.hass, 'availability_topic', 'online')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertNotEqual(STATE_UNAVAILABLE, state.state)
        self.assertFalse(state.attributes.get(ATTR_ASSUMED_STATE))

        fire_mqtt_message(self.hass, 'availability_topic', 'offline')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertEqual(STATE_UNAVAILABLE, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '1')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertEqual(STATE_UNAVAILABLE, state.state)

        fire_mqtt_message(self.hass, 'availability_topic', 'online')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertNotEqual(STATE_UNAVAILABLE, state.state)

    def test_custom_availability_payload(self):
        """Test the availability payload."""
        assert setup_component(self.hass, fan.DOMAIN, {
            fan.DOMAIN: {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'state-topic',
                'command_topic': 'command-topic',
                'availability_topic': 'availability_topic',
                'payload_available': 'good',
                'payload_not_available': 'nogood'
            }
        })

        state = self.hass.states.get('fan.test')
        self.assertEqual(STATE_UNAVAILABLE, state.state)

        fire_mqtt_message(self.hass, 'availability_topic', 'good')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertNotEqual(STATE_UNAVAILABLE, state.state)
        self.assertFalse(state.attributes.get(ATTR_ASSUMED_STATE))

        fire_mqtt_message(self.hass, 'availability_topic', 'nogood')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertEqual(STATE_UNAVAILABLE, state.state)

        fire_mqtt_message(self.hass, 'state-topic', '1')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertEqual(STATE_UNAVAILABLE, state.state)

        fire_mqtt_message(self.hass, 'availability_topic', 'good')
        self.hass.block_till_done()

        state = self.hass.states.get('fan.test')
        self.assertNotEqual(STATE_UNAVAILABLE, state.state)


async def test_discovery_removal_fan(hass, mqtt_mock, caplog):
    """Test removal of discovered fan."""
    await async_start(hass, 'homeassistant', {})
    data = (
        '{ "name": "Beer",'
        '  "command_topic": "test_topic" }'
    )
    async_fire_mqtt_message(hass, 'homeassistant/fan/bla/config',
                            data)
    await hass.async_block_till_done()
    state = hass.states.get('fan.beer')
    assert state is not None
    assert state.name == 'Beer'
    async_fire_mqtt_message(hass, 'homeassistant/fan/bla/config',
                            '')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    state = hass.states.get('fan.beer')
    assert state is None
