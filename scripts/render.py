import sys
sys.path.append('.')

import gymnasium as gym
from sb3_contrib import ARS
from stable_baselines3.common.vec_env import VecNormalize
from stable_baselines3.common.env_util import make_vec_env
import custom_envs
import numpy as np
from datetime import date
import os

current_date = date.today()
formatted_date = current_date.strftime('%d-%m-%y')
print(formatted_date)

model_path = os.path.join(os.path.dirname(__file__), "../logs/ars/KiteEnv-v3_59")
model = ARS.load(os.path.join(model_path, "best_model.zip"))

env = make_vec_env("KiteEnv-v3", env_kwargs={"render_mode": "bin"})
env = VecNormalize.load(os.path.join(model_path, "KiteEnv-v3/vecnormalize.pkl"), env)

def render(options={}, close=False):
    options['render_name'] = formatted_date
    options['model_path'] = model_path
    env.set_options(options)
    obs = env.reset()
    
    done = False
    step = 0
    try:
        while not done:
            action, _ = model.predict(obs)
            obs, reward, term, trunc = env.step(action)
            reward = reward[0]
            term = term[0]
            trunc = trunc[0]['TimeLimit.truncated']
            done = term
            print(f"Reward: {reward}, Term: {term}, Trunc: {trunc}")
            env.render()
            # print(obs)
            step += 1
    except Exception as e:
        print(e)
    finally:
        if close:
            # env.set_options({'save_render': True})
            # env.reset()
            print("Closing environment")
            env.close()

render(close=True)

# render({
#     'wanted_azimuth': 0,
#     'min_elevation': np.pi/4,
#     'max_force': 100,
#     'render_name': '0_45_100',
# }, close=True)