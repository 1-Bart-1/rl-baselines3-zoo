from juliacall import Main as jl
import numpy as np
from shutil import copy, rmtree, move
import gymnasium as gym
from gymnasium import spaces
import random
import yaml
from uuid import uuid4
from os import path, makedirs, environ

curdir = path.dirname(__file__)
# args = get_args()
environ['JULIA_NUM_THREADS'] = '1'
environ['PYTHON_JULIACALL_SYSIMAGE'] = path.join(curdir, "Environment/.julia_sysimage.so")


main_data_dir = path.expanduser("~/Code/work/data")
sim_data_dir = path.expanduser("~/Code/work/sim")


class KiteEnv(gym.Env):
  def __init__(self, render_mode="bin", render_name="render"):
    self.action_space = spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float32) # policies scaling from -1 to 1
            # range:
            #   depower: [0, 1], steering [-1, 1], v_reel_in_out [-8, 8]
            # all converted from range -1, 1

    self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(33,)) # policies scaling from -1 to 1
            # [w_old, x_old, y_old, z_old, w, x, y, z, force, elevation, azimuth, tether_length, max_force, min_elevation, wanted_azimuth]
    
    self.data_dir = path.join(main_data_dir, str(uuid4()))
    makedirs(self.data_dir)
    copy(path.join(main_data_dir, "polars.csv"), path.join(self.data_dir, "polars.csv"))
    copy(path.join(main_data_dir, "naca2412.dat"), path.join(self.data_dir, "naca2412.dat"))

    from juliacall import Main as jl
    jl.seval("using Pkg")
    jl.Pkg.activate(path.join(curdir, "Environment"))
    jl.seval("using Environment")
    jl.seval("e = Env()")
    self.Environment = jl.Environment
    self.e = jl.e

    copy(path.join(main_data_dir, "system.yaml"), 
                path.join(self.data_dir, "system.yaml"))
    copy(path.join(main_data_dir, "settings.yaml"), 
                path.join(self.data_dir, "settings.yaml"))
    self.Environment.set_data_path(self.data_dir)
    
    self.max_episode_time = 10 # in seconds
    self.sample_freq = 20
    self.max_episode_length = int(self.max_episode_time*self.sample_freq)
    self.rendered = False
    self.step_count = 0
    self.verbose = 2
    self.max_sim_force = 1000
    self.render_name = render_name
    self.model_path = ""
    self.steps = 0
    self.times_truncated = 0
    self.max_reward = 0.01
    
    self.metadata = {"render_modes": ["bin"], "render_fps": 3}
    self.render_mode = render_mode
    
    
  def reset(self, seed=None, options={}):
    # print("reset")
    super().reset(seed=seed)
    if options == None: options = {}
    self.steps = 0
    
    for try_count in range(0, 100):
      if seed is not None:
        random.seed(seed + try_count)
      with open(path.join(main_data_dir, "settings.yaml"), 'r') as file:
        settings = yaml.safe_load(file)
        
      # settings['initial']['elevation'] = float(random.choice(np.linspace(70, 80, 100, endpoint=False)))
      # settings['initial']['l_tether'] = float(random.choice(np.linspace(50, 60, 100, endpoint=False)))
      # settings['system']['sample_freq'] = self.sample_freq
      initial_tether_length = settings['initial']['l_tether']

      self.max_episode_length = int(self.max_episode_time*self.sample_freq)

      # wanted_azimuth = options.get('wanted_azimuth',random.uniform(-np.pi, np.pi))
      # min_elevation = options.get('min_elevation', random.uniform(0, np.pi/2))
      # max_force = options.get('max_force', random.uniform(0, self.max_sim_force))
      wanted_azimuth = 0.1
      min_elevation = np.pi / 8
      max_force = 5000.0
      
      with open(path.join(self.data_dir, "settings.yaml"), 'w') as file:
        yaml.safe_dump(settings, file)
        
      try:
        observation = self.Environment.reset(self.e, self.render_name, float(min_elevation), float(wanted_azimuth), float(initial_tether_length), float(max_force))

        if self.render_mode == 'bin' and self.rendered:
          print("moving bin file")
          move(path.join(self.data_dir, f"{self.render_name}.arrow"), path.join(self.model_path, f"{self.render_name}.arrow"))

        if 'render_name' in options:
          self.render_name = options['render_name']
          print("received render name")
          self.max_reward = np.inf
        if 'model_path' in options:
          self.model_path = options['model_path']
          print(self.model_path)

        return np.array(observation, dtype=np.float32), {}
      except Exception as e:
        print(f"Unable to reset, settings: {settings['initial']}")
        print(e)
  
  def step(self, action):
    # print("step")
    self.steps += 1
    reward = 0.0
    terminated = False
    
    observation = np.zeros(33)
    try:
      action = np.array(action)*300
      (terminated, observation) = self.Environment.step(self.e, action)
    except Exception as e:
      if(self.verbose >= 3):
        print(e)
      terminated = True

    reward = observation[0]
    # reward = min(reward, self.max_reward + self.times_truncated*0.005)
    truncated = self.steps > self.max_episode_length
    # if truncated:
    #   self.times_truncated += 1
    if terminated:
      reward = -100

    return np.array(observation, dtype=np.float32), reward, terminated, truncated, {}
  
  def render(self):
    if self.render_mode == 'bin':
      self.rendered = True
      # print("rendering...")
      self.Environment.render(self.e)
  
  def close(self):
    # self.Environment.close()
    if path.exists(self.data_dir):
      try:
        rmtree(self.data_dir)
      except Exception as e:
        print(e)

  def __del__(self):
    try:
      self.close()
      print("Environment deleted")
    except Exception as e:
      print(f"Unable to delete environment: {e}")
