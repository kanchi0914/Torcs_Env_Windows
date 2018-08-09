import gym
from gym import spaces
import snakeoil3_gym as snakeoil3
import numpy as np
import math
import os
import time
import subprocess
import pyautogui
from collections import OrderedDict

PATH_TO_TORCS = 'C:\\Program Files (x86)\\torcs\\bin'

class WinTorcsEnv(gym.Env):
    terminal_judge_start = 100  # If after 100 timestep still no progress, terminated
    termination_limit_progress = 5  # [km/h], episode terminates if car is running slower than this limit
    default_speed = 50

    initial_reset = True

    episode_count = 0
    relaunch_num = 1

    throttle = False
    windows = False
    visualize = False

    d = OrderedDict()
    d['speedX'] = [0, 200]
    d['speedY'] = [0, 200]
    d['speedZ'] = [0, 200]
    d['angle'] = [-3.1416, 3.1416]
    d['rpm'] = [0, 10000]
    d['trackPos'] = [-1, 1]
    track_list = [0, 3, 6, 9, 12, 15, 18]

    def __init__(self):

        self.initial_run = True

        if os.name == 'nt':
            self.windows = True

        if self.windows:
            if self.visualize:
                subprocess.Popen('wtorcs.bat', cwd='C:\\Program Files (x86)\\torcs\\bin', shell=True)
                time.sleep(2)
                pyautogui.press('enter', presses=4, interval=0.2)
            else:
                subprocess.Popen('wtorcs.bat -T', cwd='C:\\Program Files (x86)\\torcs\\bin', shell=True)
                time.sleep(2)
        else:
            os.system('pkill torcs')
            time.sleep(0.5)
            if self.vision is True:
                os.system('torcs -nofuel -nodamage -nolaptime -vision &')
            else:
                os.system('torcs -nofuel -nolaptime &')
            time.sleep(0.5)
            # os.system('sudo sh autostart.sh')
            subprocess.call('sh autostart.sh', shell=True)
            subprocess.call('xte \'key Return\'', shell=True)

        low_obs = np.array([], dtype=np.float32)
        for key in self.d:
            if(self.d[key][0] == 0):
                low_obs = np.append(low_obs, 0)
            else:
                low_obs = np.append(low_obs, -1)
        for i in self.track_list:
            low_obs = np.append(low_obs, 0)

        high_obs = np.array([], dtype=np.float32)
        for i in self.d:
            high_obs = np.append(high_obs, 1)
        for i in self.track_list:
            high_obs = np.append(high_obs, 1)

        self.observation_space = gym.spaces.Box(low_obs, high_obs)

        if self.throttle is False:
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,))
        else:
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,))

    def init_client(self, client):
        self.client = client

    def observation(self, o):

        obs = np.array([], dtype=np.float32)

        for key in self.d:
            obs = np.append(obs, np.clip(o[key], self.d[key][0], self.d[key][1]) / self.d[key][1])
        for i in self.track_list:
            obs = np.append(obs, o['track'][i] / 200)

        return obs

    def step(self, action):

        done = False
        
        client = self.client

        if not self.throttle:
            client.R.d['steer'] = action
            client.R.d['accel'] = 0.8
        else:
            client.R.d['steer'] = action[0]
            client.R.d['accel'] = action[1]

        #  Automatic Gear Change by Snakeoil
            client.R.d['gear'] = 1
            if self.throttle:
                if client.S.d['speedX'] > 50:
                    client.R.d['gear'] = 2
                if client.S.d['speedX'] > 80:
                    client.R.d['gear'] = 3
                if client.S.d['speedX'] > 110:
                    client.R.d['gear'] = 4
                if client.S.d['speedX'] > 140:
                    client.R.d['gear'] = 5
                if client.S.d['speedX'] > 170:
                    client.R.d['gear'] = 6

        # One-Step Dynamics Update #################################
        # Apply the Agent's action into torcs
        client.respond_to_server()
        # Get the response of TORCS
        client.get_servers_input()

        observation = self.observation(client.S.d)

        clipped_speed = np.clip(client.S.d['speedX'] / 150, 0, 1)
        cos_theta = math.cos(client.S.d['angle'])
        clipped_state = np.clip(abs(client.S.d['trackPos']), 0, 1)

        reward = clipped_speed * cos_theta - clipped_state

        if np.cos(client.S.d['angle']) < 0 or client.S.d['damage'] > 1: # Episode is terminated if the agent runs backward
            if (np.cos(client.S.d['angle']) < 0):
                print ("FAILED!!")
            else:
                print ("CRASHED!!")

            client.R.d['meta'] = 1
            reward = -10
            done = True

        self.time_step += 1
        #(observation)
        #print ("action:%3f  reward:%3f" % (action, reward))

        return observation, reward, done, {}

    def reset(self):

        #毎エピソード開始時に呼ばれる
        self.episode_count += 1
        self.time_step = 0

        #指定エピソード数ごとに，torcsを再起動
        if not self.initial_reset:
            self.client.respond_to_server()
            if not self.episode_count % self.relaunch_num:
                self.reset_torcs()
            else:
                pyautogui.press('enter', presses=3, interval=0.2)

        self.client = snakeoil3.Client(p=3001)  # Open new UDP in vtorcs

        client = self.client
        client.get_servers_input()  # Get the initial input from torcs

        print ("autocontroll start")
        for i in range (0,200):
            client.respond_to_server()
            self.autocontroll(client)
            client.get_servers_input()
        print ("autocontroll end")


        observation = self.observation(client.S.d)


        self.initial_reset = False

        return observation

    def autocontroll(self, c):
        '''This is only an example. It will get around the track but the
        correct thing to do is write your own `drive()` function.'''
        S, R = c.S.d, c.R.d
        target_speed = 1000

        # Steer To Corner
        R['steer'] = S['angle'] * 10 / 3.1415
        # Steer To Center
        R['steer'] -= S['trackPos'] * .10

        # Throttle Control
        if S['speedX'] < target_speed - (R['steer'] * 50):
            R['accel'] += .01
        else:
            R['accel'] -= .01
        if S['speedX'] < 10:
            R['accel'] += 1 / (S['speedX'] + .1)

        # Traction Control System
        if ((S['wheelSpinVel'][2] + S['wheelSpinVel'][3]) -
                (S['wheelSpinVel'][0] + S['wheelSpinVel'][1]) > 5):
            R['accel'] -= .2

        # Automatic Transmission
        R['gear'] = 1
        if S['speedX'] > 50:
            R['gear'] = 2
        if S['speedX'] > 80:
            R['gear'] = 3
        if S['speedX'] > 110:
            R['gear'] = 4
        if S['speedX'] > 140:
            R['gear'] = 5
        if S['speedX'] > 170:
            R['gear'] = 6
        return


    def render(self, mode='human'):
        pass

    def end(self):
        os.system('taskkill /im wtorcs.exe /f')

    def reset_torcs(self):
        if self.windows:
            if self.visualize:
                subprocess.Popen('wtorcs.bat', cwd='C:\\Program Files (x86)\\torcs\\bin', shell=True)
                time.sleep(2)
                pyautogui.press('enter', presses=4, interval=0.2)
            else:
                subprocess.Popen('wtorcs.bat -T', cwd='C:\\Program Files (x86)\\torcs\\bin', shell=True)
                time.sleep(2)
        else:
            os.system('pkill torcs')
            time.sleep(0.5)
            if self.vision is True:
                os.system('torcs -nofuel -nodamage -nolaptime -vision &')
            else:
                os.system('torcs -nofuel -nolaptime &')
            time.sleep(0.5)
            # os.system('sudo sh autostart.sh')
            time.sleep(5)
            subprocess.call('sh autostart.sh', shell=True)

            subprocess.call('xte \'key Return\'', shell=True)
            subprocess.call('xte \'usleep 100000\'', shell=True)
            subprocess.call('xte \'key Return\'', shell=True)
            subprocess.call('xte \'usleep 100000\'', shell=True)
            subprocess.call('xte \'key Return\'', shell=True)
            subprocess.call('xte \'usleep 100000\'', shell=True)
            time.sleep(0.5)




