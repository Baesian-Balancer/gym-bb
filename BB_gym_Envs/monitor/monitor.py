import time
from glob import glob
import csv
import os.path as osp
import json

from . import BB_gym_Envs.common.vec_env.vec_env.VecEnvWrapper
import numpy as np
import time
from collections import deque

class VecMonitor(VecEnvWrapper):
    def __init__(self, venv, filename=None, keep_buf=0, info_keywords=()):
        VecEnvWrapper.__init__(self, venv)
        self.eprets = None
        self.eplens = None
        self.epcount = 0
        self.tstart = time.time()
        if filename:
            self.results_writer = ResultsWriter(filename, header={'t_start': self.tstart},
                extra_keys=info_keywords)
        else:
            self.results_writer = None
        self.info_keywords = info_keywords
        self.keep_buf = keep_buf
        if self.keep_buf:
            self.epret_buf = deque([], maxlen=keep_buf)
            self.eplen_buf = deque([], maxlen=keep_buf)

    def reset(self):
        obs = self.venv.reset()
        self.eprets = np.zeros(self.num_envs, 'f')
        self.eplens = np.zeros(self.num_envs, 'i')
        return obs

    def step_wait(self):
        obs, rews, dones, infos = self.venv.step_wait()
        self.eprets += rews
        self.eplens += 1

        newinfos = list(infos[:])
        for i in range(len(dones)):
            if dones[i]:
                info = infos[i].copy()
                ret = self.eprets[i]
                eplen = self.eplens[i]
                epinfo = {'r': ret, 'l': eplen, 't': round(time.time() - self.tstart, 6)}
                for k in self.info_keywords:
                    epinfo[k] = info[k]
                info['episode'] = epinfo
                if self.keep_buf:
                    self.epret_buf.append(ret)
                    self.eplen_buf.append(eplen)
                self.epcount += 1
                self.eprets[i] = 0
                self.eplens[i] = 0
                if self.results_writer:
                    self.results_writer.write_row(epinfo)
                newinfos[i] = info
        return obs, rews, dones, newinfos


class ResultsWriter(object):
    def __init__(self, filename, header='', extra_keys=()):
        self.extra_keys = extra_keys
        assert filename is not None
        if not filename.endswith(Monitor.EXT):
            if osp.isdir(filename):
                filename = osp.join(filename, Monitor.EXT)
            else:
                filename = filename + "." + Monitor.EXT
        self.f = open(filename, "wt")
        if isinstance(header, dict):
            header = '# {} \n'.format(json.dumps(header))
        self.f.write(header)
        self.logger = csv.DictWriter(self.f, fieldnames=('r', 'l', 't')+tuple(extra_keys))
        self.logger.writeheader()
        self.f.flush()

    def write_row(self, epinfo):
        if self.logger:
            self.logger.writerow(epinfo)
            self.f.flush()


def get_monitor_files(dir):
    return glob(osp.join(dir, "*" + Monitor.EXT))

def load_results(dir):
    import pandas
    monitor_files = (
        glob(osp.join(dir, "*monitor.json")) +
        glob(osp.join(dir, "*monitor.csv"))) # get both csv and (old) json files
    if not monitor_files:
        raise LoadMonitorResultsError("no monitor files of the form *%s found in %s" % (Monitor.EXT, dir))
    dfs = []
    headers = []
    for fname in monitor_files:
        with open(fname, 'rt') as fh:
            if fname.endswith('csv'):
                firstline = fh.readline()
                if not firstline:
                    continue
                assert firstline[0] == '#'
                header = json.loads(firstline[1:])
                df = pandas.read_csv(fh, index_col=None)
                headers.append(header)
            elif fname.endswith('json'): # Deprecated json format
                episodes = []
                lines = fh.readlines()
                header = json.loads(lines[0])
                headers.append(header)
                for line in lines[1:]:
                    episode = json.loads(line)
                    episodes.append(episode)
                df = pandas.DataFrame(episodes)
            else:
                assert 0, 'unreachable'
            df['t'] += header['t_start']
        dfs.append(df)
    df = pandas.concat(dfs)
    df.sort_values('t', inplace=True)
    df.reset_index(inplace=True)
    df['t'] -= min(header['t_start'] for header in headers)
    df.headers = headers # HACK to preserve backwards compatibility
    return df
