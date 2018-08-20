# Torcs-Env-Windows
This is a modified version of [gym-torcs](https://github.com/ugo-nama-kun/gym_torcs) for windows user.

## Requirement 
python 3  
gym  
Torcs  
torcs src-server patch  

## Usage
1. Install Torcs and its src-server patch according to the [Manual](https://arxiv.org/pdf/1304.1672.pdf)
2. If you installed correctlly, you can see torcs folder at C:\Program Files (x86)\torcs.
   Then, you need to move "bin" folder from this repository to torcs folder, and set the Path.
3. cd TorcsEnv and 
```
import gym
import torcs_env.envs.gym_torcs
env= gym.make('TorcsEnv-v0')
```

You can also install TorcsEnv as following (see https://github.com/openai/gym-soccer and its Installation), 
but I don't check it yet so don't guarantee its operation.
```
cd Torcs_Env_Windows
pip install -e .
```
 
