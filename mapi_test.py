
'''
MAPI Test code to apply in CARLA Simulator
'''

from pyflame_avsim_carla import mapi_carla
import time
import datetime

if __name__ == '__main__':
    mapi_instance = mapi_carla.mapi(broker_ip="127.0.0.1")
    
    print("Start Testing...")
    while True:
        
        # check the scenario start event
        if mapi_instance.mapi_get_scenario_start():
            print("> Requested : scenario is now starting. ego vehicle moves to the start point.")
                   
            
        # write ego vehicle status into the database
        ego_status = {"velocity":0.0, "accel":0.0, "steer":0.0, "throttle":0.0, "brake":0.0}
        mapi_instance.mapi_set_ego_status(ego_status)
        
        # warning event
        mapi_instance.mapi_set_alert_collision()
        
        # scenario end
        if mapi_instance.mapi_get_scenario_end():
            print("> Requested : scenario is now stopping.")
            
        mapi_instance.mapi_set_scenario_end()
        mapi_instance.mapi_set_scenario_start()
        
        
        time.sleep(1)