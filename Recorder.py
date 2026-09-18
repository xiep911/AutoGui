# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import argparse
import json
import sys
import time

try:
  import pyautogui
  from pynput import keyboard as pynput_keyboard
  from pynput import mouse as pynput_mouse
except ImportError as e:
  print(f'Missing dependency: {e}')
  print('Run: pip install -r requirements.txt')
  sys.exit(1)

# pynput 特殊键枚举 -> pyautogui 按键名（仅保留 pyautogui.isValidKey 能识别的名字）
KEY_MAP = {
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
}
for _i in range(1, 21):
  KEY_MAP[getattr(pynput_keyboard.Key, f'f{_i}')] = f'f{_i}'

# pyautogui 同一键有多种写法 -> 归一到同一形式（用于停止键匹配）
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
  """把 pynput 收到的按键转换成 pyautogui 按键名，无法识别时返回 None。"""
  if isinstance(key, pynput_keyboard.Key):
    return KEY_MAP.get(key)
  char = getattr(key, 'char', None)
  if char is None or len(char) != 1:
    return None
  if pyautogui.isValidKey(char):
    return char if char.isdigit() else char.lower()
  return SHIFT_MAP.get(char)

def ValidateStopKey(stopKey: str) -> None:
  """校验停止录制热键"""
  if stopKey.isdigit():  # 允许单个数字字符键（如 "9"）
    if len(stopKey) != 1:
      raise ValueError(f'Invalid stop key: {stopKey}')
    return
  if not pyautogui.isValidKey(stopKey):
    raise ValueError(f'Invalid stop key: {stopKey}')

def ArgParseRecorderInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Record and replay mouse & keyboard operations')
  sub = parser.add_subparsers(dest='command', required=True, metavar='<command>')

  rec = sub.add_parser('record', help='Record user operations to a JSON file')
  rec.add_argument('-o', '--output', type=str, default='recording.json',
                   help='Output recording file, default: recording.json')
  rec.add_argument('-s', '--start-delay', type=float, default=3,
                   help='Time(seconds) to wait before recording starts, default: 3')
  rec.add_argument('-k', '--stop-key', type=str, default='esc',
                   help='Key to stop recording (pyautogui key name), default: esc')

  rep = sub.add_parser('replay', help='Replay a recorded JSON file')
  rep.add_argument('file', type=str, help='Recording JSON file')
  rep.add_argument('-r', '--repeat', type=int, default=1,
                   help='Times to replay, 0 for infinite loop, default: 1')
  rep.add_argument('-s', '--start-delay', type=float, default=0,
                   help='Time(seconds) to wait before starting replay, default: 0')
  rep.add_argument('-w', '--wait', type=float, default=0,
                   help='Time(seconds) to wait between each replay round, default: 0')
  rep.add_argument('--speed', type=float, default=1.0,
                   help='Replay speed multiplier, e.g. 2 means 2x faster, default: 1.0')

  return parser

def ArgCheckRecorder(args: argparse.Namespace) -> None:
  """参数校验"""
  if args.command == 'record':
    ValidateStopKey(args.stop_key.lower())
    if args.start_delay < 0:
      raise ValueError('Invalid start delay time (-s/--start-delay)')
  elif args.command == 'replay':
    if args.repeat < 0:
      raise ValueError('Invalid repeat times (-r/--repeat)')
    if args.start_delay < 0:
      raise ValueError('Invalid start delay time (-s/--start-delay)')
    if args.wait < 0:
      raise ValueError('Invalid wait time (-w/--wait)')
    if args.speed <= 0:
      raise ValueError('Invalid replay speed (--speed)')

def Record(outFile: str, startDelay: float, stopKey: str) -> None:
  """录制用户操作"""
  print(f'Recording will start in {startDelay} seconds...')
  pyautogui.sleep(startDelay)

  events = []
  stopped = False

  def onClick(x: int, y: int, button, pressed: bool) -> None:
    events.append({
      't': time.perf_counter(),
      'type': 'down' if pressed else 'up',
      'button': getattr(button, 'name', str(button)),
      'x': x, 'y': y
    })

  def onScroll(x: int, y: int, dx: int, dy: int) -> None:
    events.append({'t': time.perf_counter(), 'type': 'scroll',
                   'dx': dx, 'dy': dy, 'x': x, 'y': y})

  def onPress(key) -> None:
    nonlocal stopped
    name = ToKeyName(key)
    if name is not None and CanonKey(name) == stopKey:
      print(f'\nStop key ({stopKey}) pressed, stopping recording...')
      stopped = True
      kbListener.stop()
      mouseListener.stop()
      return
    if not stopped and name is not None:
      events.append({'t': time.perf_counter(), 'type': 'keydown', 'key': name})

  def onRelease(key) -> None:
    if stopped:
      return
    name = ToKeyName(key)
    if name is not None:
      events.append({'t': time.perf_counter(), 'type': 'keyup', 'key': name})

  kbListener = pynput_keyboard.Listener(on_press=onPress, on_release=onRelease)
  mouseListener = pynput_mouse.Listener(on_click=onClick, on_scroll=onScroll)

  kbListener.start()
  mouseListener.start()
  print(f'Recording... Press [{stopKey}] to stop.')

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
    'stop_key': stopKey,
    'events': events
  }
  with open(outFile, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f'Saved {len(events)} events to {outFile}')

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

def Replay(recFile: str, repeat: int, startDelay: float, wait: float, speed: float) -> None:
  """按录制延时回放"""
  with open(recFile, 'r', encoding='utf-8') as f:
    data = json.load(f)
  events = data.get('events', [])
  if not events:
    print(f'No events found in {recFile}')
    return

  # 预计算每步延时（相邻事件时间差，除以倍速）
  delays = []
  for i, ev in enumerate(events):
    prevT = events[i - 1].get('t', 0.0) if i > 0 else 0.0
    delays.append(ev.get('t', 0.0) - prevT)

  # 启动延时：切入目标窗口的缓冲，结束前不执行任何操作
  if startDelay > 0:
    print(f'Replay will start in {startDelay} seconds...')
    time.sleep(startDelay)

  if repeat == 0:
    print('Replaying in infinite loop, Ctrl+C to stop...')

  # target 跨轮连续累积，now 以同一时钟衡量：避免累计 sleep 的漂移，
  # 也保证第 2 轮起的每一轮都严格按录制节奏执行
  t0 = time.monotonic()
  target = 0.0
  roundCount = 0
  while True:
    for ev, dly in zip(events, delays):
      target += dly / speed
      now = time.monotonic() - t0
      if target > now:
        time.sleep(target - now)
      DispatchEvent(ev)
    roundCount += 1
    if repeat > 0 and roundCount >= repeat:
      break
    # 轮间等待：并入同一个调度时钟，下一轮自动顺延
    if wait > 0:
      target += wait
      now = time.monotonic() - t0
      if target > now:
        time.sleep(target - now)
  print(f'Replay finished: {roundCount} round(s)')

def main() -> None:
  """主函数"""
  try:
    argParse = ArgParseRecorderInit(None)
    args = argParse.parse_args()
    ArgCheckRecorder(args)
    if args.command == 'record':
      Record(args.output, args.start_delay, CanonKey(args.stop_key.lower()))
    else:
      Replay(args.file, args.repeat, args.start_delay, args.wait, args.speed)
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()