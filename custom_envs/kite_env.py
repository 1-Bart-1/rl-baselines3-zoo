import numpy as np
from shutil import move
import gymnasium as gym
from gymnasium import spaces
import random
from os import path, environ

curdir = path.dirname(__file__)
environ['JULIA_NUM_THREADS'] = '1'
environ['PYTHON_JULIACALL_SYSIMAGE'] = path.join(curdir, "Environment/bin/sysimage.so")
# from juliacall import Main as jl

data_dir = path.join(curdir, "Environment/data")

class KiteEnv(gym.Env):
  def __init__(self, render_mode="bin", render_name="render"):
    self.action_space = spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float32) # policies scaling from -1 to 1
            # range:
            #   depower: [0, 1], steering [-1, 1], v_reel_in_out [-8, 8]
            # all converted from range -1, 1

    self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(15,)) # policies scaling from -1 to 1
            # [w_old, x_old, y_old, z_old, w, x, y, z, force, elevation, azimuth, tether_length, max_force, min_elevation, wanted_azimuth]
    
    from juliacall import Main as jl
    jl.seval("using Pkg")
    jl.Pkg.activate(path.join(curdir, "Environment"))
    jl.seval("using Environment")
    jl.Environment.set_data_path(data_dir)
    jl.seval("e = Env()")
    self.Environment = jl.Environment
    self.e = jl.e
    
    self.max_episode_time = 40 # in seconds
    self.sample_freq = 20
    self.max_episode_length = int(self.max_episode_time*self.sample_freq)
    self.rendered = False
    self.verbose = 2
    self.render_name = render_name
    self.model_path = ""
    self.steps = 0
    
    self.metadata = {"render_modes": ["bin"], "render_fps": 3}
    self.render_mode = render_mode
    
    
  def reset(self, seed=None, options={}):
    super().reset(seed=seed)
    if options == None: options = {}
    if 'render_name' in options:
      self.render_name = options['render_name']
      print("received render name")
    if 'model_path' in options:
      self.model_path = options['model_path']
      print(self.model_path)
    if 'verbose' in options:
      self.verbose = 3

    self.steps = 0
    
    for try_count in range(0, 100):
      if seed is not None:
        random.seed(seed + try_count)
        
      # self.max_episode_length = int(self.max_episode_time*self.sample_freq)
        
      try:
        observation = self.Environment.reset(self.e, self.render_name)

        if self.render_mode == 'bin' and self.rendered:
          print("moving bin file")
          move(path.join(data_dir, f"{self.render_name}.arrow"), path.join(self.model_path, f"{self.render_name}.arrow"))

        return np.array(observation, dtype=np.float32), {}
      except Exception as e:
        print(f"Unable to reset, trying number {try_count}")
        print(e)
  
  def step(self, action):
    self.steps += 1
    reward = 0.0
    terminated = False
    
    observation = np.zeros(15)
    try:
      (terminated, observation) = self.Environment.step(self.e, action)
    except Exception as e:
      if(self.verbose >= 3):
        print(e)
      terminated = True

    reward = observation[0]
    truncated = self.steps > self.max_episode_length
    if terminated:
      reward = -10
    return np.array(observation, dtype=np.float32), reward, terminated, truncated, {}
  
  def render(self):
    if self.render_mode == 'bin':
      self.rendered = True
      # print("rendering...")
      self.Environment.render(self.e)
  
