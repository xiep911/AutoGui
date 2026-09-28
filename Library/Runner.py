# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

"""执行层：运行参数打包、统一循环调度、按键/点击/录制回放。

内部基础设施（键转换、全局热键控制、校验、分片睡眠）因仅本模块使用而内聚于此，
以 _ 前缀标记为私有，不进入 __all__ 对外导出。
"""

import argparse
import json
import threading
import time
from dataclasses import dataclass

import pyautogui

# 消除 pyautogui 每次调用后自带的隐性 0.1s（PAUSE），让延时完全由 delay/wait/interval 决定
pyautogui.PAUSE = 0

try:
  from pynput import keyboard as pynput_keyboard
  from pynput import mouse as pynput_mouse
except ImportError:
  pynput_keyboard = None
  pynput_mouse = None

from Include.Base import *  # noqa: F403
from Library.Base import *  # noqa: F403

# --- 内部实现：键转换（Recorder 录制存盘用） ---

# pynput 特殊键枚举 -> pyautogui 按键名（录制时直接存这个名字，
# 停止键匹配时再经 KEY_ALIASES 归一化；仅保留 pyautogui.isValidKey 能识别的名字）。
# 数据依赖 pynput 枚举对象（适配数据），故留在实现层而非 Include/。
KEY_MAP = {}
if pynput_keyboard is not None:
  KEY_MAP.update({
    pynput_keyboard.Key.alt: 'alt',
    pynput_keyboard.Key.backspace: 'backspace',
    pynput_keyboard.Key.caps_lock: 'capslock',
    pynput_keyboard.Key.cmd: 'win',
    pynput_keyboard.Key.ctrl: 'ctrl',
    pynput_keyboard.Key.ctrl_l: 'ctrl',
    pynput_keyboard.Key.ctrl_r: 'ctrl',
    pynput_keyboard.Key.delete: 'delete',
    pynput_keyboard.Key.down: 'down',
    pynput_keyboard.Key.end: 'end',
    pynput_keyboard.Key.enter: 'enter',
    pynput_keyboard.Key.esc: 'escape',
    pynput_keyboard.Key.home: 'home',
    pynput_keyboard.Key.insert: 'insert',
    pynput_keyboard.Key.left: 'left',
    pynput_keyboard.Key.num_lock: 'numlock',
    pynput_keyboard.Key.page_down: 'pagedown',
    pynput_keyboard.Key.page_up: 'pageup',
    pynput_keyboard.Key.pause: 'pause',
    pynput_keyboard.Key.print_screen: 'printscreen',
    pynput_keyboard.Key.right: 'right',
    pynput_keyboard.Key.scroll_lock: 'scrolllock',
    pynput_keyboard.Key.shift: 'shift',
    pynput_keyboard.Key.shift_r: 'shift',
    pynput_keyboard.Key.space: 'space',
    pynput_keyboard.Key.tab: 'tab',
    pynput_keyboard.Key.up: 'up',
  })
  for _i in range(1, 21):
    KEY_MAP[getattr(pynput_keyboard.Key, f'f{_i}')] = f'f{_i}'

def _ToKeyName(key: object) -> str | None:
  """把 pynput 收到的按键转换成 pyautogui 按键名（录制存盘用），无法识别时返回 None。"""
  if pynput_keyboard is None:
    return None
  if isinstance(key, pynput_keyboard.Key):
    return KEY_MAP.get(key)
  char = getattr(key, 'char', None)
  if char is None or len(char) != 1:
    return None
  if pyautogui.isValidKey(char):
    return char if char.isdigit() else char.lower()
  return SHIFT_MAP.get(char)

def _ToStopKeyName(key: object) -> str | None:
  """把 pynput 收到的按键转换成停止键名（热键匹配用），无法识别时返回 None。"""
  if pynput_keyboard is None:
    return None
  if isinstance(key, pynput_keyboard.Key):
    return KEY_MAP.get(key)
  char = getattr(key, 'char', None)
  if char is not None and len(char) == 1:
    return char.lower()
  return None

# --- 内部实现：全局热键控制（开始 / 暂停 / 结束）与校验 ---

class _StopControl:
  """后台全局热键监听：终端失焦时也能停止鼠标/按键操作"""

  def __init__(self, key: str, label: str = 'stop') -> None:
    self.key = key
    self._Event = threading.Event()
    self._listener = None
    if pynput_keyboard is None:
      print(f'Warning: pynput not installed, {label} hotkey [{key}] disabled.')
      return
    self._listener = pynput_keyboard.Listener(on_press=self.OnPress)
    self._listener.daemon = True
    self._listener.start()

  def OnPress(self, key) -> None:
    """监听回调：命中热键时置位"""
    name = _ToStopKeyName(key)
    if name is not None and CanonKey(name) == CanonKey(self.key):
      self._Event.set()

  def Stopped(self) -> bool:
    """是否已按下热键"""
    return self._Event.is_set()

  def Stop(self) -> None:
    """停止后台监听"""
    if self._listener is not None:
      self._listener.stop()

def _ValidateHotkey(key: str, role: str) -> None:
  """校验热键名（开始/停止/暂停通用）；不合法抛 ValueError"""
  if not pyautogui.isValidKey(key):
    raise ValueError(f'Invalid {role} key: {key}')

class _StartControl(_StopControl):
  """后台全局热键监听：等待开始热键按下后开始执行（复用 _StopControl 的监听逻辑）"""

  def __init__(self, startKey: str) -> None:
    super().__init__(startKey, label='start')

  def WaitStarted(self, timeout: float | None = None) -> bool:
    """阻塞直到开始热键按下（事件驱动，无需轮询）"""
    return self._Event.wait(timeout)

  def Available(self) -> bool:
    """开始热键是否可用（依赖 pynput 全局监听）"""
    return self._listener is not None

class _PauseControl:
  """暂停/继续 切换热键：命中热键即翻转暂停状态（再按一次恢复）；key 为 None 时不监听（禁用）"""

  def __init__(self, key: str | None) -> None:
    self.key = key
    self._Paused = threading.Event()
    self._listener = None
    if key is None:
      return
    self._listener = pynput_keyboard.Listener(on_press=self.OnPress)
    self._listener.daemon = True
    self._listener.start()

  def OnPress(self, key) -> None:
    """监听回调：命中热键时切换（toggle）暂停状态"""
    name = _ToStopKeyName(key)
    if name is not None and CanonKey(name) == CanonKey(self.key):
      if self._Paused.is_set():
        self._Paused.clear()
        print('Resumed.')
      else:
        self._Paused.set()
        print(f'Paused. Press [{self.key}] to resume.')

  def Paused(self) -> bool:
    """是否处于暂停状态"""
    return self._Paused.is_set()

  def Stop(self) -> None:
    """停止后台监听"""
    if self._listener is not None:
      self._listener.stop()

def _ValidatePauseKey(pauseKey: str | None, startKey: str, stopKey: str) -> None:
  """校验暂停热键：合法键名，且不得与开始键/终止键相同（-k3 撞 -k1/-k2 会导致行为混乱）"""
  if pauseKey is None:
    return
  _ValidateHotkey(pauseKey, 'pause')
  if (CanonKey(pauseKey) == CanonKey(startKey) or CanonKey(pauseKey) == CanonKey(stopKey)):
    raise ValueError(f'Pause key ({pauseKey}) must differ from start key ({startKey}) and stop key ({stopKey})')

def _ValidateDistinctHotkeys(startKey: str, stopKey: str) -> None:
  """校验开始热键与结束热键必须不同（归一化比较，能识别 esc/escape 等别名）；
  相同键会同时触发开始与结束，导致行为混乱，故禁止"""
  if CanonKey(startKey) == CanonKey(stopKey):
    raise ValueError(f'Start key ({startKey}) and stop key ({stopKey}) must differ')

# --- 内部实现：分片睡眠与等待 ---

def _SleepResponsive(seconds: float, stopControl: _StopControl, pauseControl: _PauseControl | None) -> bool:
  """分片睡眠并响应暂停/停止热键（-k3/-k2 全局热键，失焦也能按）；
  暂停期间继续分片等待（仍响应停止键）；返回 True 表示应退出循环"""
  deadline = time.monotonic() + seconds
  while time.monotonic() < deadline:
    if _WaitResumeOrStop(stopControl, pauseControl):
      return True
    time.sleep(POLL_INTERVAL)
  return False

def _WaitResumeOrStop(stopControl: _StopControl, pauseControl: _PauseControl | None) -> bool:
  """暂停期间阻塞等待恢复或结束（-k3 再按一次恢复，-k2 结束）；返回 True 表示应退出循环"""
  if pauseControl is None:
    return stopControl.Stopped()
  while pauseControl.Paused():
    if stopControl.Stopped():
      return True
    time.sleep(POLL_INTERVAL)
  return False

def _WaitStartHotkey(startKey: str, stopControl: _StopControl, what: str) -> bool:
  """等待开始热键（全局监听，终端失焦也能触发，可在目标窗口就绪后按下）；
  期间按停止键 = 干净放弃本次执行；pynput 缺失时退化为回车开始；返回 False 表示已放弃"""
  startControl = _StartControl(startKey)
  if not startControl.Available():
    print(f'pynput not installed, press enter to start the {what}...')
    input()
    return True
  print(f'Press [{startKey}] to start {what}.')
  # 开始键事件驱动秒回，-k2 在等待阶段即生效（全局热键，失焦也能按）
  while not startControl.WaitStarted(timeout=POLL_INTERVAL) and not stopControl.Stopped():
    pass
  startControl.Stop()
  if stopControl.Stopped():
    stopControl.Stop()
    print(f'Aborted before start by [{stopControl.key}].')
    return False
  return True

# --- 运行参数打包（消除逐参传递） ---

@dataclass
class RunConfig:
  """一次执行的全部节奏/热键参数。

  历史教训：逐参传递（RunPress 8 个、RunClick/Replay 9 个）导致每加一个参数
  所有调用点同步改动。打包成 dataclass 后，加参数只改这里。
  """
  repeat: int = 0                    # 重复轮数，0 = 无限循环
  delay: float = DEFAULT_DELAY       # 命令间间隔（秒），Recorder 回放不用
  wait: float = 0.0                  # 轮间间隔（秒）
  speed: float = 1.0                 # 回放倍速（仅 Replay 用，2 = 2 倍速）
  startDelay: float = 0.0            # 开始前缓冲（秒），切入目标窗口用
  startKey: str | None = None        # 开始热键；None = -a 立即开始，不等待
  stopKey: str = DEFAULT_STOP_KEY    # 停止热键（全局监听，终端失焦也能按）
  pauseKey: str | None = None        # 暂停切换热键；None = 禁用（-k3 缺省）

# --- 公共 argparse 与 main 保护 ---

def AddCommonArgs(parser: argparse.ArgumentParser, *, withDelay: bool = False, withOutput: bool = False) -> None:
  """循环执行公共参数：-v/-r/-a/-s/-k1/-k2/-k3/-w；withDelay 追加 -d，withOutput 追加 -o（预设保存）"""
  parser.add_argument('-v', '--version', action='version', version=f'AutoGui {VERSION}')
  parser.add_argument('-r', '--repeat', type=int, required=True,
                      help='Number of repeat times, 0 for infinite loop')
  parser.add_argument('-a', '--auto', action='store_true', default=False,
                      help='Start immediately without waiting for the start key')
  parser.add_argument('-s', '--start-delay', type=float, default=0,
                      help='Time(seconds) to wait before starting, default: 0')
  parser.add_argument('-k1', '--start-key', type=str, default=DEFAULT_START_KEY,
                      help='Key to press to start (global hotkey), default: enter; ignored with -a/--auto')
  parser.add_argument('-k2', '--stop-key', type=str, default=DEFAULT_STOP_KEY,
                      help='Key to stop and end (global hotkey), default: esc')
  parser.add_argument('-k3', '--pause-key', type=str, default=None,
                      help='Key to toggle pause/resume during the loop (global hotkey), default: disabled')
  parser.add_argument('-w', '--wait', type=float, default=None,
                      help='Time(seconds) to wait between each round, default: 0')
  if withDelay:
    parser.add_argument('-d', '--delay', type=float, default=None,
                        help='Time(seconds) between commands, default: 0.1 or preset value if not given')
  if withOutput:
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Save the command list (+delay/wait) to a preset JSON file')

def CheckCommonArgs(args: argparse.Namespace, *, withDelay: bool = False) -> None:
  """公共参数校验：repeat/delay/wait/start_delay 非负 + 三热键合法且互异。

  子命令缺省的参数（如 record 无 -r/-w）用 getattr 跳过，允许 record/replay 共用。
  """
  if getattr(args, 'repeat', None) is not None and args.repeat < 0:
    raise ValueError('Invalid repeat times (-r/--repeat), 0 for infinite loop')
  if withDelay and getattr(args, 'delay', None) is not None and args.delay < 0:
    raise ValueError('Invalid delay time (-d/--delay)')
  if getattr(args, 'wait', None) is not None and args.wait < 0:
    raise ValueError('Invalid wait time (-w/--wait)')
  if args.start_delay < 0:
    raise ValueError('Invalid start delay time (-s/--start-delay)')
  _ValidateHotkey(args.start_key.lower(), 'start')
  _ValidateHotkey(args.stop_key.lower(), 'stop')
  _ValidateDistinctHotkeys(args.start_key.lower(), args.stop_key.lower())
  _ValidatePauseKey(args.pause_key.lower() if args.pause_key is not None else None,
                    args.start_key.lower(), args.stop_key.lower())

def GuardMain(run) -> int:
  """统一 main 保护：KeyboardInterrupt → EXIT_INTERRUPTED，其他异常 → EXIT_ERROR"""
  try:
    return run()
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
    return EXIT_INTERRUPTED
  except Exception as e:
    print(f'Error: {e}')
    return EXIT_ERROR

# --- 统一循环调度（KeyPress/MouseClick 共用） ---

# 点击选项 -> pyautogui 点击函数（脚本参数校验与执行共用）
CLICK_OPTION = {
  1: pyautogui.click,
  2: pyautogui.doubleClick,
  3: pyautogui.rightClick
}

def RunLoop(config: RunConfig, action, what: str, infinite: str) -> int:
  """统一循环调度：开始热键 → 每轮 action → 轮间等待 → 重复计数。

  action(stopControl, pauseControl) 执行一轮并响应暂停/停止，返回 True 表示本回合被打断
  （中断的未完成轮不计入轮数）；与重构前两个脚本的循环逻辑逐字等价。
  """
  # 后台监听停止热键，终端失焦时也能停止；等待开始阶段即生效（按停止键=放弃本次执行）
  stopControl = _StopControl(config.stopKey)
  print(f'Press [{config.stopKey}] to stop.')

  # 是否自动执行：-a 时 config.startKey 为 None 直接开始，否则等待开始热键（或按停止键放弃）
  if config.startKey is not None:
    if not _WaitStartHotkey(config.startKey, stopControl, what):
      stopControl.Stop()
      return EXIT_OK

  # 执行前等待
  pyautogui.sleep(config.startDelay)

  # 暂停/继续 切换监听（-k3，默认关闭）
  pauseControl = _PauseControl(config.pauseKey) if config.pauseKey is not None else None

  if config.repeat == 0:
    print(infinite)

  roundCount = 0
  while True:
    # 暂停期间阻塞等待恢复或结束
    if action(stopControl, pauseControl):
      break
    # 中途被停止键打断的未完成轮不计入轮数
    if stopControl.Stopped():
      break
    roundCount += 1
    # 轮间等待：分片睡眠并响应 -k2 停止 / -k3 暂停（全局热键，失焦也能按）
    if config.wait > 0 and _SleepResponsive(config.wait, stopControl, pauseControl):
      break
    if config.repeat > 0 and roundCount >= config.repeat:
      break
  stopControl.Stop()
  if pauseControl is not None:
    pauseControl.Stop()
  if stopControl.Stopped():
    print(f'Stopped by [{config.stopKey}] after {roundCount} round(s).')
  else:
    print(f'{what} finished: {roundCount} round(s).')
  return EXIT_OK

def _PressRound(keyList: list, delay: float):
  """按键一回合的执行体：响应暂停/停止；delay 注入 pyautogui interval
  （轮末最后一条 interval=0 以消除 delay+wait 叠加，wait 为纯轮间间隔）"""
  def _action(stopControl, pauseControl) -> bool:
    for j in range(len(keyList)):
      # 暂停期间阻塞等待恢复或结束
      if _WaitResumeOrStop(stopControl, pauseControl):
        return True
      # 依赖 pyautogui 0.9.52+ 每次调用后必 sleep(interval)（requirements.txt 已锁最低版本）
      pyautogui.press(keyList[j], presses=1, interval=0.0 if j == len(keyList) - 1 else delay)
    return False
  return _action

def RunPress(config: RunConfig, keyList: list) -> int:
  """按 keyList 循环按键；节奏/热键由 config 决定"""
  return RunLoop(config, _PressRound(keyList, config.delay), 'Key press',
                 'Pressing keys in infinite loop, Ctrl+C (terminal focused) to stop...')

def _ClickRound(clickList: list, positionList: list | None, delay: float):
  """点击一回合的执行体：响应暂停/停止；-m 时先移动再点；
  双击保持快速连点（interval=0），其余 delay 注入 interval（轮末不补以让 wait 成为纯轮间间隔）"""
  def _action(stopControl, pauseControl) -> bool:
    for j in range(len(clickList)):
      # 暂停期间阻塞等待恢复或结束
      if _WaitResumeOrStop(stopControl, pauseControl):
        return True
      if positionList is not None:
        pyautogui.moveTo(positionList[j][0], positionList[j][1])
      opt = CLICK_OPTION[clickList[j]]
      last = (j == len(clickList) - 1)
      if clickList[j] == 2:
        # 双击保持快速连点（interval=0），间隔在调用后补，轮末不补以让 wait 成为纯轮间间隔
        opt()
        if not last:
          time.sleep(delay)
      else:
        # delay 注入 interval，轮末最后一条 interval=0 消除 delay+wait 叠加
        # 依赖 pyautogui 0.9.52+ 每次调用后必 sleep(interval)（requirements.txt 已锁最低版本）
        opt(interval=0.0 if last else delay)
    return False
  return _action

def RunClick(config: RunConfig, clickList: list, positionList: list | None = None) -> int:
  """按 clickList 循环点击；节奏/热键/坐标由 config 决定"""
  return RunLoop(config, _ClickRound(clickList, positionList, config.delay), 'Clicks',
                 'Clicking in infinite loop, Ctrl+C (terminal focused) to stop...')

# --- 录制 / 回放 ---

EVENT_TYPES = ('down', 'up', 'scroll', 'keydown', 'keyup')

def Record(outFile: str, config: RunConfig) -> None:
  """录制用户操作；config.startKey 为 None（-a）时立即开始，否则等待开始热键"""
  # 是否自动执行：-a 时直接开始，否则等待开始热键（全局监听，终端失焦也能触发）
  if config.startKey is not None:
    startControl = _StartControl(config.startKey)
    print(f'Press [{config.startKey}] to start recording.')
    startControl.WaitStarted()
    startControl.Stop()

  # 开始键按下后的缓冲（-s），就绪用
  if config.startDelay > 0:
    print(f'Recording will start in {config.startDelay} seconds...')
    pyautogui.sleep(config.startDelay)

  events = []
  stopped = False
  heldKeys: set[str] = set()
  heldButtons: set[str] = set()

  def onClick(x: int, y: int, button, pressed: bool) -> None:
    name = getattr(button, 'name', str(button))
    if pressed:
      heldButtons.add(name)
    elif name in heldButtons:  # 停止时补记 up 后，未记录 down 的 up 不再产生
      heldButtons.discard(name)
    else:
      return
    events.append({
      't': time.perf_counter(),
      'type': 'down' if pressed else 'up',
      'button': name,
      'x': x, 'y': y
    })

  def onScroll(x: int, y: int, dx: int, dy: int) -> None:
    events.append({'t': time.perf_counter(), 'type': 'scroll',
                   'dx': dx, 'dy': dy, 'x': x, 'y': y})

  def onPress(key) -> None:
    nonlocal stopped
    name = _ToKeyName(key)
    if name is not None and CanonKey(name) == config.stopKey:
      print(f'\nStop key ({config.stopKey}) pressed, stopping recording...')
      stopped = True
      kbListener.stop()
      mouseListener.stop()
      # 补记停止瞬间仍在按住的键/鼠标键的抬起事件，避免回放时按键卡死
      for k in heldKeys:
        events.append({'t': time.perf_counter(), 'type': 'keyup', 'key': k})
      heldKeys.clear()
      x, y = pyautogui.position()
      for b in heldButtons:
        events.append({'t': time.perf_counter(), 'type': 'up', 'button': b, 'x': x, 'y': y})
      heldButtons.clear()
      return
    if not stopped and name is not None:
      heldKeys.add(name)
      events.append({'t': time.perf_counter(), 'type': 'keydown', 'key': name})

  def onRelease(key) -> None:
    if stopped:
      return
    name = _ToKeyName(key)
    if name is not None:
      heldKeys.discard(name)
      events.append({'t': time.perf_counter(), 'type': 'keyup', 'key': name})

  kbListener = pynput_keyboard.Listener(on_press=onPress, on_release=onRelease)
  mouseListener = pynput_mouse.Listener(on_click=onClick, on_scroll=onScroll)

  kbListener.start()
  mouseListener.start()
  print(f'Recording... Press [{config.stopKey}] to stop.')

  kbListener.join()
  mouseListener.join()

  if not events:
    print('No operation recorded.')
    return

  # 归一化为相对时间，并保证按时间有序
  events.sort(key=lambda e: e['t'])
  t0 = events[0]['t']
  for ev in events:
    ev['t'] = round(ev['t'] - t0, 6)

  data = {
    'version': 1,
    'created': time.strftime('%Y-%m-%d %H:%M:%S'),
    'stop_key': config.stopKey,
    'events': events
  }
  with open(outFile, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f'Saved {len(events)} events to {outFile}')

def LoadRecording(path: str) -> dict:
  """加载录制文件，校验 version 与每条事件的结构（与 LoadPreset 同样的严格风格）；非法时抛 ValueError。"""
  try:
    with open(path, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except OSError:
    raise ValueError(f'Cannot open recording file: {path}')
  except json.JSONDecodeError:
    raise ValueError(f'Invalid JSON in recording file: {path}')
  if not isinstance(data, dict) or data.get('version') != 1:
    raise ValueError(f'Unsupported recording file (version): {path}')
  events = data.get('events')
  if not isinstance(events, list):
    raise ValueError(f'Invalid events in recording file: {path}')
  for ev in events:
    if not isinstance(ev, dict):
      raise ValueError(f'Invalid event in recording file: {path}')
    etype = ev.get('type')
    if etype not in EVENT_TYPES:
      raise ValueError(f'Unknown event type in recording file {path}: {etype!r}')
    if isinstance(ev.get('t'), bool) or not isinstance(ev.get('t'), (int, float)):
      raise ValueError(f'Invalid event time in recording file: {path}')
    if etype in ('down', 'up'):
      if not isinstance(ev.get('button'), str):
        raise ValueError(f'Invalid event button in recording file: {path}')
    elif etype in ('keydown', 'keyup'):
      if not isinstance(ev.get('key'), str):
        raise ValueError(f'Invalid event key in recording file: {path}')
    elif etype == 'scroll':
      if isinstance(ev.get('dy'), bool) or not isinstance(ev.get('dy'), (int, float)):
        raise ValueError(f'Invalid event dy in recording file: {path}')
  # 与 Record 存盘前一致，按时间排序保证回放节奏正确
  events.sort(key=lambda e: e['t'])
  return data

def DispatchEvent(event: dict) -> None:
  """回放一条事件"""
  etype = event.get('type')
  try:
    if etype == 'down':
      pyautogui.mouseDown(button=event['button'], x=event.get('x'), y=event.get('y'))
    elif etype == 'up':
      pyautogui.mouseUp(button=event['button'], x=event.get('x'), y=event.get('y'))
    elif etype == 'scroll':
      pyautogui.scroll(int(event.get('dy', 1)), x=event.get('x'), y=event.get('y'))
    elif etype == 'keydown':
      if pyautogui.isValidKey(event.get('key', '')):
        pyautogui.keyDown(event['key'])
    elif etype == 'keyup':
      if pyautogui.isValidKey(event.get('key', '')):
        pyautogui.keyUp(event['key'])
    else:
      print(f'Warning: unknown event type: {etype}')
  except pyautogui.FailSafeException:
    raise
  except Exception as e:
    print(f'Warning: failed to replay {etype}: {e}')

def Replay(recFile: str, config: RunConfig) -> None:
  """按录制延时回放；节奏/热键/倍速由 config 决定（保留独立的冻结时钟调度，
  暂停期间冻结 t0，恢复后事件不会"追帧"快进，与 KeyPress/MouseClick 的通用调度不同）"""
  data = LoadRecording(recFile)
  events = data.get('events', [])
  if not events:
    print(f'No events found in {recFile}')
    return

  # 预计算每步延时（相邻事件时间差，除以倍速）
  delays = []
  for i, ev in enumerate(events):
    prevT = events[i - 1].get('t', 0.0) if i > 0 else 0.0
    delays.append(ev.get('t', 0.0) - prevT)

  # 后台监听停止热键，终端失焦时也能停止；等待开始阶段即生效（按停止键=放弃本次执行）
  stopControl = _StopControl(config.stopKey)
  print(f'Press [{config.stopKey}] to stop.')

  # 是否自动执行：-a 时 config.startKey 为 None 直接开始，否则等待开始热键（或按停止键放弃）
  if config.startKey is not None:
    if not _WaitStartHotkey(config.startKey, stopControl, 'replay'):
      stopControl.Stop()
      return

  # 开始键按下后的缓冲（-s），切入目标窗口用，结束前不执行任何操作
  if config.startDelay > 0:
    print(f'Replay will start in {config.startDelay} seconds...')
    time.sleep(config.startDelay)

  # 暂停/继续 切换监听（-k3，默认关闭）
  pauseControl = _PauseControl(config.pauseKey) if config.pauseKey is not None else None

  if config.repeat == 0:
    print('Replaying in infinite loop, Ctrl+C (terminal focused) to stop...')

  # target 跨轮连续累积，now 以同一时钟衡量：避免累计 sleep 的漂移，
  # 也保证第 2 轮起的每一轮都严格按录制节奏执行
  t0 = time.monotonic()
  target = 0.0
  roundCount = 0
  pausedAt: float | None = None

  def HandlePause() -> bool:
    """暂停期间冻结调度时钟（恢复后事件不会"追帧"快进）；返回 True 表示已按下停止键需退出"""
    nonlocal pausedAt, t0
    while pauseControl is not None and pauseControl.Paused():
      if stopControl.Stopped():
        return True
      if pausedAt is None:
        pausedAt = time.monotonic()
      time.sleep(PAUSE_POLL_INTERVAL)
    if pausedAt is not None:
      t0 += time.monotonic() - pausedAt
      pausedAt = None
    return False

  def _SleepResponsive(seconds: float) -> bool:
    """分片睡眠并响应暂停/停止（本地时钟冻结版，区别于模块级 _SleepResponsive）"""
    deadline = time.monotonic() - t0 + seconds
    while time.monotonic() - t0 < deadline:
      if HandlePause() or stopControl.Stopped():
        return True
      time.sleep(POLL_INTERVAL)
    return False

  while True:
    for ev, dly in zip(events, delays):
      if HandlePause() or stopControl.Stopped():
        break
      target += dly / config.speed
      if _SleepResponsive(target - (time.monotonic() - t0)):
        break
      if stopControl.Stopped():
        break
      DispatchEvent(ev)
    # 中途被停止键打断的未完成轮不计入轮数
    if stopControl.Stopped():
      break
    roundCount += 1
    if config.repeat > 0 and roundCount >= config.repeat:
      break
    # 轮间等待：并入同一个调度时钟，下一轮自动顺延；暂停同样冻结调度
    if config.wait > 0:
      target += config.wait
      if _SleepResponsive(config.wait):
        break
    if stopControl.Stopped():
      break
  stopControl.Stop()
  if pauseControl is not None:
    pauseControl.Stop()
  if stopControl.Stopped():
    print(f'Stopped by [{config.stopKey}] after {roundCount} round(s).')
  else:
    print(f'Replay finished: {roundCount} round(s)')

# 对外公开 API（脚本直接使用的符号）；RunLoop/LoadRecording/DispatchEvent/EVENT_TYPES 仅内部使用
__all__ = ['RunConfig', 'AddCommonArgs', 'CheckCommonArgs', 'GuardMain',
           'RunPress', 'RunClick', 'CLICK_OPTION', 'Record', 'Replay']
