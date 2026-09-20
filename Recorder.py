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

from Library.Base import CanonKey, StartControl, StopControl, ToKeyName, ValidateStartKey, ValidateStopKey

def ArgParseRecorderInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Record and replay mouse & keyboard operations')
  sub = parser.add_subparsers(dest='command', required=True, metavar='<command>')

  rec = sub.add_parser('record', help='Record user operations to a JSON file')
  rec.add_argument('-o', '--output', type=str, default='recording.json',
                   help='Output recording file, default: recording.json')
  rec.add_argument('-a', '--auto', action='store_true', default=False,
                   help='Start recording immediately without waiting for the start key')
  rec.add_argument('-k1', '--start-key', type=str, default='enter',
                   help='Key to press to start recording (global hotkey), default: enter; ignored with -a/--auto')
  rec.add_argument('-s', '--start-delay', type=float, default=0,
                   help='Buffer time(seconds) after start before recording begins, default: 0')
  rec.add_argument('-k2', '--stop-key', type=str, default='esc',
                   help='Key to stop recording (pyautogui key name), default: esc')

  rep = sub.add_parser('replay', help='Replay a recorded JSON file')
  rep.add_argument('file', type=str, help='Recording JSON file')
  rep.add_argument('-r', '--repeat', type=int, required=True,
                   help='Times to replay, 0 for infinite loop (required)')
  rep.add_argument('-a', '--auto', action='store_true', default=False,
                   help='Start replay immediately without waiting for the start key')
  rep.add_argument('-k1', '--start-key', type=str, default='enter',
                   help='Key to press to start replay (global hotkey), default: enter; ignored with -a/--auto')
  rep.add_argument('-s', '--start-delay', type=float, default=0,
                   help='Buffer time(seconds) after start before replaying, default: 0')
  rep.add_argument('-w', '--wait', type=float, default=0,
                   help='Time(seconds) to wait between each replay round, default: 0')
  rep.add_argument('-k2', '--stop-key', type=str, default='esc',
                   help='Key to stop the replay (global hotkey), default: esc')
  rep.add_argument('--speed', type=float, default=1.0,
                   help='Replay speed multiplier, e.g. 2 means 2x faster, default: 1.0')

  return parser

def ArgCheckRecorder(args: argparse.Namespace) -> None:
  """参数校验"""
  if args.command == 'record':
    ValidateStartKey(args.start_key.lower())
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
    ValidateStartKey(args.start_key.lower())
    ValidateStopKey(args.stop_key.lower())

def Record(outFile: str, autoStart: bool, startKey: str, startDelay: float, stopKey: str) -> None:
  """录制用户操作"""
  # 是否自动执行：-a 时直接开始，否则等待开始热键（全局监听，终端失焦也能触发）
  if not autoStart:
    startControl = StartControl(startKey)
    print(f'Press [{startKey}] to start recording.')
    startControl.WaitStarted()
    startControl.Stop()

  # 开始键按下后的缓冲（-s），就绪用
  if startDelay > 0:
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

def Replay(recFile: str, repeat: int, autoStart: bool, startKey: str, startDelay: float, wait: float, speed: float, stopKey: str) -> None:
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

  # 是否自动执行：-a 时直接开始，否则等待开始热键（全局监听，终端失焦也能触发）
  if not autoStart:
    startControl = StartControl(startKey)
    print(f'Press [{startKey}] to start replay.')
    startControl.WaitStarted()
    startControl.Stop()

  # 开始键按下后的缓冲（-s），切入目标窗口用，结束前不执行任何操作
  if startDelay > 0:
    print(f'Replay will start in {startDelay} seconds...')
    time.sleep(startDelay)

  # 后台监听停止热键，终端失焦时也能停止
  stopControl = StopControl(stopKey)
  print(f'Press [{stopKey}] to stop.')

  if repeat == 0:
    print('Replaying in infinite loop, Ctrl+C to stop...')

  # target 跨轮连续累积，now 以同一时钟衡量：避免累计 sleep 的漂移，
  # 也保证第 2 轮起的每一轮都严格按录制节奏执行
  t0 = time.monotonic()
  target = 0.0
  roundCount = 0
  while True:
    for ev, dly in zip(events, delays):
      if stopControl.Stopped():
        break
      target += dly / speed
      now = time.monotonic() - t0
      if target > now:
        time.sleep(target - now)
      DispatchEvent(ev)
    roundCount += 1
    if stopControl.Stopped():
      break
    if repeat > 0 and roundCount >= repeat:
      break
    # 轮间等待：并入同一个调度时钟，下一轮自动顺延
    if wait > 0:
      target += wait
      now = time.monotonic() - t0
      if target > now:
        time.sleep(target - now)
    if stopControl.Stopped():
      break
  stopControl.Stop()
  if stopControl.Stopped():
    print(f'Stopped by [{stopKey}] after {roundCount} round(s).')
  else:
    print(f'Replay finished: {roundCount} round(s)')

def main() -> None:
  """主函数"""
  try:
    argParse = ArgParseRecorderInit(None)
    args = argParse.parse_args()
    ArgCheckRecorder(args)
    if args.command == 'record':
      Record(args.output, args.auto, args.start_key.lower(), args.start_delay, CanonKey(args.stop_key.lower()))
    else:
      Replay(args.file, args.repeat, args.auto, args.start_key.lower(), args.start_delay, args.wait, args.speed, CanonKey(args.stop_key.lower()))
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
