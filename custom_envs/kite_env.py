from juliacall import Main as jl
import numpy as np
from shutil import copy, rmtree, move
import gymnasium as gym
from gymnasium import spaces
import random
import yaml
from uuid import uuid4
from os import path, makedirs, environ
from os.path import exists, expanduser

curdir = path.dirname(__file__)
# args = get_args()
environ['JULIA_NUM_THREADS'] = '1'
environ['PYTHON_JULIACALL_SYSIMAGE'] = path.join(curdir, ".julia_sysimage.so")

if exists("/cluster"):
  main_data_dir = "/cluster/work/bartva/data"
  sim_data_dir = "/cluster/work/bartva/sim"
else:
  main_data_dir = expanduser("~/Code/work/data")
  sim_data_dir = expanduser("~/Code/work/sim")


class KiteEnv(gym.Env):
  def __init__(self, render_mode="arrow", render_name="render"):
    self.action_space = spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float32) # policies scaling from -1 to 1
            # range:
            #   depower: [0, 1], steering [-1, 1], v_reel_in_out [-8, 8]
            # all converted from range -1, 1

    self.observation_space = spaces.Box(low=-1, high=1, shape=(15,)) # policies scaling from -1 to 1
            # [w_old, x_old, y_old, z_old, w, x, y, z, force, elevation, azimuth, tether_length, max_force, min_elevation, wanted_azimuth]
    
    from juliacall import Main as jl
    jl.seval("using Pkg")
    jl.Pkg.activate(path.join(curdir, "Environment"))
    jl.seval("using Environment")
    
    self.Environment = jl.Environment
    
    self.data_dir = path.join(main_data_dir, str(uuid4()))
    makedirs(self.data_dir)
    copy(path.join(main_data_dir, "system.yaml"), 
                path.join(self.data_dir, "system.yaml"))
    copy(path.join(main_data_dir, "settings.yaml"), 
                path.join(self.data_dir, "settings.yaml"))
    self.Environment.set_data_path(self.data_dir)
    
    self.max_episode_length = 1024
    self.rendered = False
    self.step_count = 0
    self.verbose = 2
    self.max_sim_force = 10000
    self.heading = 0
    self.rotation = 0
    self.render_name = render_name
    self.model_path = ""
    self.steps = 0
    self.crashed = False
    self.rewards = []
    
    self.observation = {
      'orientation_old': np.zeros(4),   # range [-1, 1]
      'orientation': np.zeros(4),       # range [-1, 1]
      'force': 0,                       # range [0, 10 000]
      'elevation': 0,                   # range [0, pi/2]
      'azimuth': 0,                     # range [-pi/2, pi/2]
      'tether_length': 0,               # range [0, 150]
      'max_force': 5000,             # range [0, 10 000]
      'min_elevation': np.pi / 8,    # range [0, pi/2]
      'wanted_azimuth': 0               # range [-pi/2, pi/2]
      # add wanted_tether_length
    }
    
    self.initial_tether_length = 150
    self.max_tether_length = 200
    self.min_tether_length = 149
    
    self.metadata = {"render_modes": ["arrow"], "render_fps": 20}
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
        
      settings['initial']['elevation'] = float(random.choice(np.linspace(70, 80, 100, endpoint=False)))
      settings['initial']['l_tether'] = float(random.choice(np.linspace(150, 200, 10, endpoint=False)))

      self.initial_tether_length = settings['initial']['l_tether']
      self.max_tether_length = settings['initial']['l_tether'] + 50
      self.min_tether_length = settings['initial']['l_tether'] - 1

      # settings['solver']['abs_tol'] = 0.6e-5
      # settings['solver']['rel_tol'] = 1e-5
                          
      # wanted_azimuth = options.get('wanted_azimuth',random.uniform(-np.pi, np.pi))
      # min_elevation = options.get('min_elevation', random.uniform(0, np.pi/2))
      # max_force = options.get('max_force', random.uniform(0, self.max_sim_force))
      wanted_azimuth = 0
      min_elevation = np.pi / 8
      max_force = 5000
      
      with open(path.join(self.data_dir, "settings.yaml"), 'w') as file:
        yaml.safe_dump(settings, file)
        
      try:
        reset_value = self.Environment.reset(self.render_name)

        if self.render_mode == 'arrow' and self.rendered:
          print("moving arrow file")
          move(path.join(self.data_dir, f"{self.render_name}.arrow"), path.join(self.model_path, f"{self.render_name}.arrow"))

        if 'render_name' in options:
          self.render_name = options['render_name']
        if 'model_path' in options:
          self.model_path = options['model_path']
          print(self.model_path)

        first_step = self.Environment.get_next_step(0.5,0.0,0.0)

        self.rotation = self.heading
        self.rotation += self._calculate_rotation_change(reset_value[8], first_step[8])
        self.heading = first_step[8]

        self.observation = {
          'orientation_old': reset_value[:4],
          'orientation': first_step[:4],
          'force': first_step[4],
          'elevation': first_step[5],
          'azimuth': first_step[6],
          'tether_length': first_step[7],
          'max_force': max_force,
          'min_elevation': min_elevation,
          'wanted_azimuth': wanted_azimuth
        }
        return np.array(self._normalize_obs(), dtype=np.float32), {}
      except Exception as e:
        print(f"Unable to reset, settings: {settings['initial']}")
        # print(e)
  
  def step(self, action):
    if not all(-1 <= i <= 1 for i in action):
      print(f"All values in action {action} must be between -1 and 1")

    self.action = {
      'power': action[0]/2 + 0.5,
      'steering': action[1],
      'v_reel_out': action[2] * 8
    }

    self.steps += 1
    reward = 0.0
    
    next_step = np.zeros(9)
    self.crashed = False
    try:
      next_step = self.Environment.get_next_step(float(self.action['power']), float(self.action['steering']), float(self.action['v_reel_out']))
    except Exception as e:
      if(self.verbose >= 3) or self.steps <= 10:
        print(e)
      # print(e)
      # print("crashed")
      self.crashed = True
    
    self.rotation += self._calculate_rotation_change(self.heading, next_step[8])
    self.heading = next_step[8]
    
    self.observation = {
      'orientation_old': self.observation['orientation'],
      'orientation': next_step[:4],
      'force': next_step[4],
      'elevation': next_step[5],
      'azimuth': next_step[6],
      'tether_length': next_step[7],
      'max_force': self.observation['max_force'],
      'min_elevation': self.observation['min_elevation'],
      'wanted_azimuth': self.observation['wanted_azimuth']
    }
    
    reward, terminated, truncated = self._calculate_reward()
    # print(reward)
    # if done:
    # print(f"force: {self.observation['force']}, elevation: {self.observation['elevation']}, azimuth: {self.observation['azimuth']}, tether_length: {self.observation['tether_length']}, rotation: {self.rotation}")
      
    return np.array(self._normalize_obs(), dtype=np.float32), reward, terminated, truncated, {}
  
  def render(self):
    if self.render_mode == 'arrow':
      self.rendered = True
      print("rendering...")
      self.Environment.render()
  
  def close(self):
    self.Environment.close()
    if path.exists(self.data_dir):
      try:
        rmtree(self.data_dir)
      except Exception as e:
        print(e)

  def _convert_action(self, action): # convert from [-1, 1] to the actual range and to a dictionary
    np.squeeze(action)
    action_dict = {
      'power': action[0]/2 + 0.5,
      'steering': action[1],
      'v_reel_out': action[2] * 8
    }
    return action_dict
  
  def _normalize_obs(self): # normalize the observation values to be between 0 and 1
    normalized_observation = np.concatenate((
      [(i+1)/2 for i in self.observation['orientation_old']],
      [(i+1)/2 for i in self.observation['orientation']],
      [self.observation['force'] / self.max_sim_force],
      [self.observation['elevation'] / (np.pi/2)],
      [(self.observation['azimuth'] + np.pi/2) / np.pi],
      [(self.observation['tether_length']-self.min_tether_length) / (self.max_tether_length-self.min_tether_length)],
      [self.observation['max_force'] / self.max_sim_force],
      [self.observation['min_elevation'] / (np.pi/2)],
      [(self.observation['wanted_azimuth'] + np.pi) / (np.pi*2)]
      ))
    # if not all(0 <= i <= 1 for i in normalized_observation):
    #   print(f"All values in normalized_observation {normalized_observation} must be between 0 and 1")
    return normalized_observation
  
  def _calculate_reward(self):
    if self.crashed:
      return -self.max_episode_length, True, False
    if (self.observation['force'] > self.observation['max_force'] or
      self.observation['elevation'] < self.observation['min_elevation'] or
      self.observation['tether_length'] > self.max_tether_length or
      self.observation['tether_length'] < self.min_tether_length or
      not -2*np.pi < self.rotation < 2*np.pi):
      return -self.max_episode_length, True, False
    
    force_component = self._calculate_force_component(self.observation['force'], self.observation['azimuth'], self.observation['elevation'], self.observation['wanted_azimuth'], self.observation['min_elevation'])
    reward = np.clip(force_component / self.observation['max_force'], 0.0, 1.0) # range [-1, 1] clipped to [0, 1] because 0 is physical minimum

    # if len(self.rewards) <= 10_000:
    #   self.rewards.append(reward)
    # if len(self.rewards) == 10_000:
    #   print("First - Fifth - Tenth percentile: ", np.percentile(self.rewards, 1), np.percentile(self.rewards, 5), np.percentile(self.rewards, 10))
    #   print("99th - 95th - 90th percentile: ", np.percentile(self.rewards, 99), np.percentile(self.rewards, 95), np.percentile(self.rewards, 90))

    if self.steps >= self.max_episode_length:
      return reward, False, True
    return reward, False, False
  
  def _calculate_force_component(self, force, azimuth, elevation, wanted_azimuth, wanted_elevation):
      force_vector = np.array([force, 0, 0])
      force_vector = np.array([force*np.cos(elevation), 0, force*np.sin(elevation)])
      rotation_matrix_z_axis = np.array([
          [np.cos(azimuth), -np.sin(azimuth), 0],
          [np.sin(azimuth), np.cos(azimuth), 0],
          [0, 0, 1]
      ])
      force_vector = np.dot(rotation_matrix_z_axis, force_vector)

      wanted_force_vector = np.array([force, 0, 0])
      wanted_force_vector = np.array([force*np.cos(wanted_elevation), 0, force*np.sin(wanted_elevation)])
      rotation_matrix_z_axis = np.array([
          [np.cos(wanted_azimuth), -np.sin(wanted_azimuth), 0],
          [np.sin(wanted_azimuth), np.cos(wanted_azimuth), 0],
          [0, 0, 1]
      ])
      wanted_force_vector = np.dot(rotation_matrix_z_axis, wanted_force_vector)

      force_component = np.dot(force_vector, wanted_force_vector) / np.linalg.norm(wanted_force_vector)
      return force_component

  def _calculate_rotation_change(self, old_heading, new_heading):
      rotation = new_heading - old_heading
      if rotation > 1:
          rotation -= 2*np.pi
      elif rotation < -1:
          rotation += 2*np.pi
      return rotation
  
  def __del__(self):
    try:
      self.close()
      print("Environment deleted")
    except Exception as e:
      print(f"Unable to delete environment: {e}")

