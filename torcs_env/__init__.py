from gym.envs.registration import register

register(
    id='TorcsEnv-v0',
    entry_point='torcs_env.envs:TorcsEnv',
    kwargs={'vision' : False, 'throttle' : False, 'gear_change' : False},
    max_episode_steps=10000,
)