## json_mqtt_pub

Read JSON objects from stdin and publish them to MQTT.

### Publishing topics

This program can use the values of specific keys in JSON objects to determine the MQTT
topic it will publish to. If run with,
```
json_mqtt_pub --topic-prefix home/jsonstuff --topic-keys model id name --topic-suffix value
```
then the messages will be published to `home/jsonstuff[/model][/id][/name]/value`, where the model, id,
and name in the JSON object are filled in. For example, with the parameters above,

* **JSON**: `{'model':'Acme Corp', 'id':31415, 'name':'Combobulator', 'reading':2.71828}`
* **Topic**: `home/jsonstuff/Acme_Corp/31415/Combobulator/value`

The full JSON object is used as the payload, key/value pairs used to construct the topic are not removed.
If any topic-keys are missing, they will be omitted. For example,

* **JSON**: `{'model':'Acurite', 'name':'5-in-1', 'temperature':32}`
* **Topic**: `home/jsonstuff/Acurite/5-in-1/value`

### Usage

```
$ json_mqtt_pub -h
usage: json_mqtt_pub [-h] [--broker BROKER] [--port PORT] [--tls]
                     [--username USERNAME] [--password PASSWORD]
                     --topic-prefix TOPIC_PREFIX [--topic-keys KEY [KEY ...]]
                     [--topic-suffix TOPIC_SUFFIX] [--retain]
                     [--status-topic STATUS_TOPIC] [--no-retain-status]
                     [--nonjson {print,error}]

Read JSON objects from stdin and publish them to MQTT.

options:
  -h, --help            show this help message and exit
  --broker BROKER       Hostname or IP address of MQTT broker (default:
                        localhost)
  --port PORT           MQTT broker port (default: 8883 for TLS, 1883
                        otherwise)
  --tls                 Use TLS to connect to broker
  --username USERNAME   MQTT broker login username
  --password PASSWORD   MQTT broker login password
  --topic-prefix TOPIC_PREFIX
                        Base topic for publishing messages
  --topic-keys KEY [KEY ...]
                        Keys whose associated values will be used to create
                        subtopics
  --topic-suffix TOPIC_SUFFIX
                        Subtopic appended to prefix and key/value subtopics
  --retain              Publish messages with retain flag set
  --status-topic STATUS_TOPIC
                        Topic to which to publish status messages
  --no-retain-status    Do not publish status messages with retain flag set
  --nonjson {print,error}
                        Action to take when non-JSON objects are received on
                        stdin. (default: print)

Arguments can be passed in a file with the '@' character.
e.g. json_mqtt_pub @path/to/args.conf
```

If `myprog` is a program that outputs JSON objects, one per line, to standard out, then

```
myprog | json_mqtt_publish @args.conf
```

will publish those JSON objects to MQTT, as defined by the arguments in `args.conf`.
