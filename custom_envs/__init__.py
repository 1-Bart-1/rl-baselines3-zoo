from gymnasium.envs.registration import register

register(
    id="KiteEnv-v1",
    entry_point="custom_envs.kite_env:KiteEnv",
    max_episode_steps=1024,
)