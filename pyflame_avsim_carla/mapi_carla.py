'''
Message API Package for Interfacing between Flame Manager and CARLA SImulator
@auhtor Byunghun Hwang(bh.hwang@iae.re.kr)
'''

import threading
import pathlib
from typing import Any
import paho.mqtt.client as mqtt
import json

WORKING_PATH = pathlib.Path(__file__).parent
APP_NAME = "avsim-carla"

'''
Singleton Pattern Class
'''
class singleton(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(singleton, cls).__new__(cls)
        return cls.instance
    
'''
Message API Class
'''
class mapi(threading.Thread):
    
    def __init__(self, broker_ip):
        super(mapi, self).__init__()
        
        # declared for subscribing mapi
        self.message_api = {
            "flame/avsim/carla/mapi_set_scenario_start" : self.mapi_set_scenario_start,
            "flame/avsim/carla/mapi_set_scenario_end" : self.mapi_set_scenario_end,
            "flame/avsim/carla/mapi_set_scenario_init" : self.mapi_set_scenario_init
        }
        
        self.mq_client = mqtt.Client(client_id="flame-avsim-carla",transport='tcp',protocol=mqtt.MQTTv311, clean_session=True)
        self.mq_client.on_connect = self.on_mqtt_connect
        self.mq_client.on_message = self.on_mqtt_message
        self.mq_client.on_disconnect = self.on_mqtt_disconnect
        self.mq_client.connect_async(broker_ip, port=1883, keepalive=60)
        self.mq_client.loop_start()
        
        super(mapi, self).start()
        
        # flags
        self._scenario_start = False
        self._scenario_end = False
        self._scenario_init = False
        
        
    # thread callback function for loop    
    def run(self):
        pass
        
    # publish data to data collector
    def _write_log(self, data) -> bool:
        if self.mq_client.is_connected():
            if type(data) is dict:
                data["app"] = APP_NAME
                self.mq_client.publish("flame/avsim/carla/log", json.dumps(data), 0)
                return True
            else:
                print("invalid type of data")
        else:
            print("It cannot be connected to broker")
        return False
    
    # message api for actor/ego location initialization
    def mapi_get_scenario_init(self):
        init = False
        if self._scenario_init is True:
            init = True
            self._scenario_init = False
            
            # save log
            self._write_log({"scenario_init":int(True)})
            
        return init
    
    # message api for actor/ego location initialization
    def mapi_set_scenario_init(self, payload):
        self._scenario_init = True
            
    
    # message api callback
    def mapi_set_scenario_start(self, payload):
        self._scenario_start = True
                
            
    # check scenario start event
    def mapi_get_scenario_start(self):
        start = False
        if self._scenario_start is True:
            start = True
            self._scenario_start = False
            
            # save log
            self._write_log({"scenario_start":int(True)})
            
        return start
    
    # ego vehicle status (vel, acc, throttle, break, streering)
    def mapi_set_ego_status(self, status):
        if self.mq_client.is_connected():
            updated_status = {}
            if type(status) is dict:
                updated_status["app"] = APP_NAME
                
                # ego vehicle status (float type data only)
                float_status = ["speed", "accel_x", "accel_y", "steer", "gyro_x", "gyro_y", "gyro_z", "loc_x", "loc_y", "throttle", "brake"]
                for status_key in float_status:
                    if status_key in status.keys():
                        if type(status[status_key])==float:
                            updated_status[status_key] = status[status_key]
                                
                self._write_log(updated_status) # write log data
        
    # collision warning alert
    def mapi_set_alert_collision(self):
        #write log
        self._write_log({"alert_collision":int(True)})
        
        # re-publish
        if self.mq_client.is_connected():
            msg = {"app" : APP_NAME}
            self.mq_client.publish("flame/avsim/carla/notify_alert_collision", json.dumps(msg), 0)
        else:
            print("Not connected to broker")
    
    # scenario end
    def mapi_get_scenario_end(self):
        end = False
        if self._scenario_end is True:
            end = True
            self._scenario_end = False
            
            # save log
            self._write_log({"scenario_end":int(True)})
        return end
    
    # evnet for scenario end
    def mapi_set_scenario_end(self, payload):
        if self.mq_client.is_connected():
            msg = {"app":APP_NAME, "scenario_end":True}
            self.mq_client.publish("flame/avsim/carla/set_scenario_end", json.dumps(msg), 0)
        else:
            print("Not connected to broker")
        
    def mapi_notify_active(self):
        if self.mq_client.is_connected():
            msg = {"app":APP_NAME}
            self.mq_client.publish("flame/avsim/carla/notify_active", json.dumps(msg), 0)
        else:
            print("Not connected to broker")
        
    # MQTT callbacks
    def on_mqtt_connect(self, mqttc, obj, flags, rc):
        # subscribe message api
        for topic in self.message_api.keys():
            print("Subscribing Topic : ", topic)
            self.mq_client.subscribe(topic, 0)
        
        self.mapi_notify_active()
        
    def on_mqtt_disconnect(self, mqttc, userdata, rc):
        self.show_on_statusbar("Disconnected to Broker({})".format(str(rc)))
    
    # message api processing
    def on_mqtt_message(self, mqttc, userdata, msg):
        mapi = str(msg.topic)
        try:
            if mapi in self.message_api.keys():
                payload = json.loads(msg.payload)
                if "app" not in payload:
                    print("message payload does not contain the app")
                    return
                
                if payload["app"] != APP_NAME:
                    self.message_api[mapi](payload)
            else:
                print("Unknown MAPI was called :", mapi)

        except json.JSONDecodeError as e:
            print("MAPI Message payload cannot be converted")
    
    
