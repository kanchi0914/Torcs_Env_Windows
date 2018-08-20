from gym.envs.registration import register

register(
    id='TorcsEnvWin-v0',
    entry_point='torcs_env_win.envs:WinTorcsEnv',
    max_episode_steps=1000,
)