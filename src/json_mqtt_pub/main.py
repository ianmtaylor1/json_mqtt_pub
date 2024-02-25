#!/usr/bin/env python3

# This program listens for JSON messages on standard input, one per line, and 
# publishes them as MQTT messages in a specific topic/subtopic structure based
# on the message contents. 
# Based on the rtl_433_mqtt_relay.py example script included in the rtl_433
# package.

import json
import paho.mqtt.client as mqtt
import sys
import argparse
import shlex

# Map characters that will cause problems or be confusing in mqtt
# topics.
def sanitize(text):
    """Sanitize a name for MQTT use."""
    return (str(text)
            .replace(" ", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace("+", "_")
            .replace("#", "_")
            .replace("&", "_"))

def construct_topic(prefix, obj={}, keys=[], suffix=None):
    topic = prefix
    for k in keys:
        if k in obj:
            topic += "/" + sanitize(obj[k])
    if suffix is not None:
        topic += "/" + suffix
    return topic

def publish_object(client, prefix, keys, suffix, retain, obj, line=None):
    topic = construct_topic(prefix, obj, keys, suffix)
    if line is None:
        line = json.dumps(obj)
    return client.publish(
            topic = topic,
            payload = line.rstrip(),
            retain = retain)

def mqtt_connect_callback(client, userdata, connect_flags, reason_code, properties):
    """Handle MQTT connection callback."""
    print("MQTT connection: " + reason_code.getName(), file=sys.stderr)
    if (not reason_code.is_failure) and (userdata["status_topic"] is not None):
        client.publish(
                topic = userdata["status_topic"],
                payload = "online",
                retain = userdata["status_retain"])

def mqtt_disconnect_callback(client, userdata, disconnect_flags, reason_code, properties):
    """Handle MQTT disconnection callback."""
    print("MQTT disconnection: " + reason_code.getName(), file=sys.stderr)

def mqtt_client(broker, port, tls, username, password, status_topic, status_retain):
    """Create an MQTT client and connect it to the broker"""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.user_data_set({"status_topic":status_topic, "status_retain":status_retain})
    client.on_connect = mqtt_connect_callback
    client.on_disconnect = mqtt_disconnect_callback
    if status_topic is not None:
        client.will_set(
                topic = status_topic,
                payload = "offline",
                retain = status_retain)
    if tls:
        # Defaults are fine: use system CA store
        client.tls_set()
    client.username_pw_set(username, password)
    client.connect_async(broker, port)
    return client

###############################################################################

# Parse arguments from file split by spaces, but preserving quoted strings
class ShArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        return shlex.split(arg_line)

def get_config():
    parser = ShArgumentParser(
            fromfile_prefix_chars="@",
            description="Read JSON objects from stdin and publish them to MQTT.",
            epilog="Arguments can be passed in a file with the '@' character.  e.g. %(prog)s @path/to/args.conf"
            )
    parser.add_argument('--broker', default='localhost',
                        help="Hostname or IP address of MQTT broker (default: %(default)s)")
    parser.add_argument('--port', type=int,
                        help="MQTT broker port (default: 8883 for TLS, 1883 otherwise)")
    parser.add_argument('--tls', action='store_true',
                        help='Use TLS to connect to broker')
    parser.add_argument('--username',
                        help="MQTT broker login username")
    parser.add_argument('--password',
                        help="MQTT broker login password")
    parser.add_argument('--topic-prefix', required=True,
                        help="Base topic for publishing messages")
    parser.add_argument('--topic-keys', nargs='+', default=[], metavar="KEY",
                        help="Keys whose associated values will be used to create subtopics")
    parser.add_argument('--topic-suffix',
                        help="Subtopic appended to prefix and key/value subtopics")
    parser.add_argument('--retain', action="store_true",
                        help="Publish messages with retain flag set")
    parser.add_argument('--status-topic',
                        help="Topic to which to publish status messages")
    parser.add_argument('--no-retain-status', action="store_false", dest="status_retain",
                        help="Do not publish status messages with retain flag set")
    parser.add_argument('--nonjson', choices=['print', 'error'], default='print',
                        help="Action to take when non-JSON objects are received on stdin. (default: %(default)s)")
    args = parser.parse_args()
    
    if args.port is None:
        if args.tls:
            args.port = 8883
        else:
            args.port = 1883

    return args

###############################################################################

def handle_nonjson(text, action):
    if action == "print":
        print(text, end="")
    elif action == "error":
        raise Exception("Invalid input: '{}'".format(text))

def run():
    
    args = get_config()
    
    mqttc = mqtt_client(args.broker, args.port, args.tls,
                        args.username, args.password,
                        args.status_topic, args.status_retain)
    mqttc.loop_start()

    # Loop on stdin
    for line in sys.stdin:
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                publish_object(
                        mqttc, 
                        args.topic_prefix, args.topic_keys, args.topic_suffix,
                        args.retain,
                        obj, line)
            else:
                handle_nonjson(line, args.nonjson)
        except json.JSONDecodeError:
            handle_nonjson(line, args.nonjson)
    
    mqttc.loop_stop()
    mqttc.disconnect()

if __name__ == "__main__":
    run()

