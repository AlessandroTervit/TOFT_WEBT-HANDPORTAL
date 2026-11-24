import json, time
import paho.mqtt.publish as publish

# same setup as SteadyTouch config.py
MQTT_BROKER, MQTT_PORT, LAMPE_NAME = "localhost", 1883, "lampe"

HOLD_SECONDS = 0.3     # hand must stay in the area this long before toggling (ignores single noisy frames)
RELEASE_SECONDS = 0.5  # hand must be out of the area this long before it can toggle again (ignores flicker)


def lampe(**befehl):
    # from SteadyTouch actions/lights.py: publish.single + try, so a missing broker doesn't crash the camera loop
    try:
        publish.single(f"zigbee2mqtt/{LAMPE_NAME}/set", json.dumps(befehl), hostname=MQTT_BROKER, port=MQTT_PORT)
        print(f"[MQTT] Befehl gesendet an '{LAMPE_NAME}': {befehl}")
    except Exception as error:
        print(f"[MQTT] Fehler beim Senden an '{LAMPE_NAME}': {error}")


def toggle_lamp():
    lampe(state="TOGGLE")


_inside_since = None
_last_seen = float("-inf")
_fired = False


def toggle_on_enter(hand_in_area):
    """Call every frame. Toggles ONCE per entry: after HOLD_SECONDS in the area,
    then not again until the hand was out for RELEASE_SECONDS (like NO_REPEAT in SteadyTouch dispatcher.py)."""
    global _inside_since, _last_seen, _fired
    now = time.monotonic()
    if hand_in_area:
        _last_seen = now
        if _inside_since is None:
            _inside_since = now
        if not _fired and now - _inside_since >= HOLD_SECONDS:
            _fired = True
            toggle_lamp()
    elif now - _last_seen > RELEASE_SECONDS:
        _inside_since, _fired = None, False
