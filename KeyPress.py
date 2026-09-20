# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import argparse

import pyautogui
from Library.Base import StopControl, ValidateStopKey

def ArgParseKeyPressInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Key press')

  parser.add_argument('-n', '--num', type=int, default=0, help='Number of commands (interactive input mode)')
  parser.add_argument('-l', '--list', type=str, default='', help='Comma-separated key list, e.g. "up,down,left,right"')
  parser.add_argument('-r', '--repeat', type=int, required=True, help='Number of repeat times, 0 for infinite loop')
  parser.add_argument('-d', '--delay', type=float, default=0, help='Time(seconds) to wait between each command in commands list')
  parser.add_argument('-w', '--wait', type=float, default=0, help='Time(seconds) to wait after executing the commands list once')
  parser.add_argument('-a', '--auto', action='store_true', default=False, help='Auto start key press without waiting for Enter')
  parser.add_argument('-s', '--start-delay', type=float, default=0, help='Time(seconds) to wait before starting key press')
  parser.add_argument('-k', '--stop-key', type=str, default='esc', help='Key to stop the key press (global hotkey), default: esc')

  return parser

def ArgCheckKeyPress(args: argparse.Namespace) -> None:
  """参数校验"""

  if args.num < 0:
    raise ValueError('Invalid key command number (-n/--num)')
  if args.num == 0 and not args.list:
    raise ValueError('Either -n/--num or -l/--list must be provided')
  if args.num > 0 and args.list:
    raise ValueError('-n/--num and -l/--list are mutually exclusive')
  if args.list:
    for key in args.list.split(','):
      if not pyautogui.isValidKey(key):
        raise ValueError(f'Invalid key: {key}')
  if args.repeat < 0:
    raise ValueError('Invalid repeat times (-r/--repeat), 0 for infinite loop')
  if args.delay < 0:
    raise ValueError('Invalid delay time (-d/--delay)')
  if args.wait < 0:
    raise ValueError('Invalid wait time (-w/--wait)')
  if args.start_delay < 0:
    raise ValueError('Invalid start delay time (-s/--start-delay)')
  ValidateStopKey(args.stop_key.lower())

def GetKeyList(num: int) -> list[str]:
  """获取命令列表"""

  print('Input your command:')

  keyList = []

  for i in range(num):
    while True:
      try:
        print(f'Input your {i+1} command:')
        key = input()
        if pyautogui.isValidKey(key) is False:
          raise ValueError('Invalid key command!')
        keyList.append(key)
        break
      except ValueError as e:
        print(f'Error: {e}')

  return keyList

def RunPress(keyList: list[str], autoStart: bool, startDelay: float, repeat: int, delay: float, wait: float, stopKey: str) -> None:
  """运行按键命令"""
  import time

  # 是否自动执行
  if autoStart is False:
    print('Press enter to start the key press...')
    input()

  # 激活目标窗口: 部分窗口失焦后需要一次激活
  pyautogui.click()

  # 执行前等待
  pyautogui.sleep(startDelay)

  # 后台监听停止热键，终端失焦时也能停止
  stopControl = StopControl(stopKey)
  print(f'Press [{stopKey}] to stop.')

  if repeat == 0:
    print('Pressing keys in infinite loop, Ctrl+C to stop...')

  roundCount = 0
  while True:
    roundCount += 1
    for j in range(len(keyList)):
      if stopControl.Stopped():
        break
      pyautogui.press(keyList[j])
      time.sleep(delay)
    if stopControl.Stopped():
      break
    time.sleep(wait)
    if stopControl.Stopped():
      break
    if repeat > 0:
      print(f'Run {roundCount}/{repeat} times')
      if roundCount >= repeat:
        break
    else:
      print(f'Run {roundCount} times')
  stopControl.Stop()
  if stopControl.Stopped():
    print(f'Stopped by [{stopKey}] after {roundCount} round(s).')

def main():
  """主函数"""
  try:
    # 解析参数
    argParse = ArgParseKeyPressInit(None)
    args = argParse.parse_args()
    ArgCheckKeyPress(args)
    # 生成按键列表
    if args.list:
      keyList = args.list.split(',')
    else:
      keyList = GetKeyList(args.num)
    # 开始执行按键命令
    RunPress(keyList, args.auto, args.start_delay, args.repeat, args.delay, args.wait, args.stop_key.lower())
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
