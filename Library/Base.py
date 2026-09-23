# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import json
import os
import threading
import time

import pyautogui

# 消除 pyautogui 每次调用后自带的隐性 0.1s（PAUSE），让延时完全由 delay/wait/interval 决定
pyautogui.PAUSE = 0

# 未指定 -d 且无预设时的每命令间隔（秒）
DEFAULT_DELAY = 0.1

try:
  from pynput import keyboard as pynput_keyboard
except ImportError:
  pynput_keyboard = None

# pynput 特殊键枚举 -> pyautogui 按键名（Recorder 录制时直接存这个名字，
# 停止键匹配时再经 KEY_ALIASES 归一化；仅保留 pyautogui.isValidKey 能识别的名字）
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

# pyautogui 同一键有多种写法 -> 归一到同一形式（用于停止键/停止录制键匹配）
KEY_ALIASES = {
  'esc': 'esc', 'escape': 'esc',
  'pageup': 'pageup', 'pgup': 'pageup',
  'pagedown': 'pagedown', 'pgdn': 'pagedown',
  'ctrl': 'ctrl', 'ctrlleft': 'ctrl', 'ctrlright': 'ctrl',
  'shift': 'shift', 'shiftleft': 'shift', 'shiftright': 'shift',
  'alt': 'alt', 'altleft': 'alt', 'altright': 'alt',
  'cmd': 'win', 'command': 'win', 'win': 'win',
  'enter': 'enter', 'return': 'enter',
  'numlock': 'numlock', 'capslock': 'capslock', 'scrolllock': 'scrolllock',
  'printscreen': 'printscreen', 'up': 'up', 'down': 'down',
  'left': 'left', 'right': 'right', 'space': 'space', 'tab': 'tab',
}

def CanonKey(name: str) -> str:
  """把键名归一到 KEY_ALIASES 定义的形式；未定义时原样返回"""
  return KEY_ALIASES.get(name, name)

# 需要 Shift 组合的符号 -> 基础键（Shift 状态由独立的 keydown/keyup 事件表达）
SHIFT_MAP = {
  '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6',
  '&': '7', '*': '8', '(': '9', ')': '0', '_': '-', '+': '=',
  '{': '[', '}': ']', '|': '\\', '"': "'", ':': ';', '<': ',',
  '>': '.', '?': '/', '~': '`'
}

def ToKeyName(key: object) -> str | None:
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

def ToStopKeyName(key: object) -> str | None:
  """把 pynput 收到的按键转换成停止键名（热键匹配用），无法识别时返回 None。"""
  if pynput_keyboard is None:
    return None
  if isinstance(key, pynput_keyboard.Key):
    return KEY_MAP.get(key)
  char = getattr(key, 'char', None)
  if char is not None and len(char) == 1:
    return char.lower()
  return None

class StopControl:
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
    name = ToStopKeyName(key)
    if name is not None and CanonKey(name) == CanonKey(self.key):
      self._Event.set()

  def Stopped(self) -> bool:
    """是否已按下热键"""
    return self._Event.is_set()

  def Stop(self) -> None:
    """停止后台监听"""
    if self._listener is not None:
      self._listener.stop()

def ValidateStopKey(stopKey: str) -> None:
  """校验停止热键"""
  if stopKey.isdigit():  # 允许单个数字字符键（如 "9"）
    if len(stopKey) != 1:
      raise ValueError(f'Invalid stop key: {stopKey}')
    return
  if not pyautogui.isValidKey(stopKey):
    raise ValueError(f'Invalid stop key: {stopKey}')

class StartControl(StopControl):
  """后台全局热键监听：等待开始热键按下后开始执行（复用 StopControl 的监听逻辑）"""

  def __init__(self, startKey: str) -> None:
    super().__init__(startKey, label='start')

  def Started(self) -> bool:
    """是否已按下开始热键"""
    return self.Stopped()

  def WaitStarted(self, timeout: float | None = None) -> bool:
    """阻塞直到开始热键按下（事件驱动，无需轮询）"""
    return self._Event.wait(timeout)

  def Available(self) -> bool:
    """开始热键是否可用（依赖 pynput 全局监听）"""
    return self._listener is not None

def ValidateStartKey(startKey: str) -> None:
  """校验开始热键"""
  if startKey.isdigit():  # 允许单个数字字符键（如 "9"）
    if len(startKey) != 1:
      raise ValueError(f'Invalid start key: {startKey}')
    return
  if not pyautogui.isValidKey(startKey):
    raise ValueError(f'Invalid start key: {startKey}')

class PauseControl:
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
    name = ToStopKeyName(key)
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

def ValidatePauseKey(pauseKey: str | None, startKey: str, stopKey: str) -> None:
  """校验暂停热键：合法键名，且不得与开始键/终止键相同（-k3 撞 -k1/-k2 会导致行为混乱）"""
  if pauseKey is None:
    return
  if pauseKey.isdigit():  # 允许单个数字字符键（如 "9"）
    if len(pauseKey) != 1:
      raise ValueError(f'Invalid pause key: {pauseKey}')
  elif not pyautogui.isValidKey(pauseKey):
    raise ValueError(f'Invalid pause key: {pauseKey}')
  if (CanonKey(pauseKey) == CanonKey(startKey) or CanonKey(pauseKey) == CanonKey(stopKey)):
    raise ValueError(f'Pause key ({pauseKey}) must differ from start key ({startKey}) and stop key ({stopKey})')

def ValidateDistinctHotkeys(startKey: str, stopKey: str) -> None:
  """校验开始热键与结束热键必须不同（归一化比较，能识别 esc/escape 等别名）；
  相同键会同时触发开始与结束，导致行为混乱，故禁止"""
  if CanonKey(startKey) == CanonKey(stopKey):
    raise ValueError(f'Start key ({startKey}) and stop key ({stopKey}) must differ')

def SleepResponsive(seconds: float, stopControl: StopControl, pauseControl: PauseControl | None) -> bool:
  """分片睡眠并响应暂停/停止热键（-k3/-k2 全局热键，失焦也能按）；
  暂停期间继续分片等待（仍响应停止键）；返回 True 表示应退出循环"""
  deadline = time.monotonic() + seconds
  while time.monotonic() < deadline:
    while pauseControl is not None and pauseControl.Paused():
      if stopControl.Stopped():
        return True
      time.sleep(0.05)
    if stopControl.Stopped():
      return True
    time.sleep(0.05)
  return False

# --- 参数预设文件（KeyPress/MouseClick 的录制与回放） ---

def LoadPreset(path: str, expectedType: str) -> dict:
  """加载参数预设文件，校验 version 与 type，返回数据 dict；非法时抛 ValueError。"""
  try:
    with open(path, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except OSError:
    raise ValueError(f'Cannot open preset file: {path}')
  except json.JSONDecodeError:
    raise ValueError(f'Invalid JSON in preset file: {path}')
  if not isinstance(data, dict) or data.get('version') != 1:
    raise ValueError(f'Unsupported preset file (version): {path}')
  if data.get('type') != expectedType:
    raise ValueError(f'Preset type mismatch in {path}: expected {expectedType}, got {data.get("type")!r}')
  return data

def SavePreset(path: str, data: dict) -> None:
  """保存参数预设文件，并提示保存的文件位置和名称"""
  with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  print(f'Preset saved to: {os.path.abspath(path)}')

def GetPresetNumber(data: dict, key: str, default: float = 0.0) -> float:
  """取预设中的数值参数（delay/wait 等）并校验合法性，非法时抛 ValueError。"""
  value = data.get(key, default)
  if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
    raise ValueError(f'Invalid preset value for {key}: {value!r}')
  return float(value)
