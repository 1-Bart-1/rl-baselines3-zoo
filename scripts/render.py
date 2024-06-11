import sys
sys.path.append('../custom_envs')

import gymnasium as gym
from sb3_contrib import ARS
import custom_envs
import numpy as np
from datetime import date
import os

current_date = date.today()
formatted_date = current_date.strftime('%d-%m-%y')
print(formatted_date)

model = ARS.load(os.path.join(os.curdir(), "logs/ars/KiteEnv-v1_15/best_model"))
env = gym.make("KiteEnv-v1")

def render(options=None, close=False):
    options['render_name'] = formatted_date
    obs, _ = env.reset(options)
    
    done = False
    step = 0
    try:
        while step < 2048:
            action, _ = model.predict(obs)
            obs, _, term, trunc, _ = env.step(action)
            done = term or trunc
            env.render()
            # print(obs)
            step += 1
    except Exception as e:
        print(e)
    finally:
        if close:
            env.reset()
            print("Closing environment")
            env.close()

render(close=True)

# render({
#     'wanted_azimuth': 0,
#     'min_elevation': np.pi/4,
#     'max_force': 100,
#     'render_name': '0_45_100',
# }, close=True)