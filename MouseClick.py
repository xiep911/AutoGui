# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import argparse

import pyautogui
from Library.Base import StopControl, ValidateStopKey

CLICK_OPTION = {
  1: pyautogui.click,
  2: pyautogui.doubleClick,
  3: pyautogui.rightClick
}

def ArgParseMouseClickInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Click mouse')

  parser.add_argument('-n', '--num', type=int, default=0, help='Number of click commands (interactive input mode)')
  parser.add_argument('-l', '--list', type=str, default='', help='Comma-separated click list, e.g. "1,2,3" (1=left, 2=double, 3=right)')
  parser.add_argument('-r', '--repeat', type=int, required=True, help='Number of repeat times, 0 for infinite loop')
  parser.add_argument('-m', '--move', action='store_true', default=False, help='Move mouse to position before clicking')
  parser.add_argument('-a', '--auto', action='store_true', default=False, help='Auto start clicks without waiting for Enter')
  parser.add_argument('-s', '--start-delay', type=float, default=0, help='Time(seconds) to wait before starting clicks')
  parser.add_argument('-d', '--delay', type=float, default=0, help='Time(seconds) to wait between each click command')
  parser.add_argument('-w', '--wait', type=float, default=0, help='Time(seconds) to wait after executing the click commands list once')
  parser.add_argument('-k', '--stop-key', type=str, default='esc', help='Key to stop the clicks (global hotkey), default: esc')

  return parser

def ArgCheckMouseClick(args: argparse.Namespace) -> None:
  """参数校验"""

  if args.num < 0:
    raise ValueError('Invalid click command number (-n/--num)')
  if args.num == 0 and not args.list:
    raise ValueError('Either -n/--num or -l/--list must be provided')
  if args.num > 0 and args.list:
    raise ValueError('-n/--num and -l/--list are mutually exclusive')
  if args.list:
    for c in args.list.split(','):
      if c not in ('1', '2', '3'):
        raise ValueError(f'Invalid click command: {c}. Must be 1 (left), 2 (double), or 3 (right).')
  if args.repeat < 0:
    raise ValueError('Invalid repeat times (-r/--repeat), 0 for infinite loop')
  if args.delay < 0:
    raise ValueError('Invalid delay time (-d/--delay)')
  if args.wait < 0:
    raise ValueError('Invalid wait time (-w/--wait)')
  if args.start_delay < 0:
    raise ValueError('Invalid start delay time (-s/--start-delay)')
  ValidateStopKey(args.stop_key.lower())

def GetClickList(num: int) -> list:
  """获取点击命令列表"""

  print('Select your click command:')
  print('1: click left')
  print('2: click left double')
  print('3: click right')

  clickList = []

  for i in range(num):
    while True:
      try:
        print(f'Input your {i+1} click command (1/2/3):')
        click = int(input())
        if click not in CLICK_OPTION:
          raise ValueError('Invalid click command! Please input 1, 2, or 3.')
        clickList.append(CLICK_OPTION[click])
        break
      except ValueError as e:
        print(f'Error: {e}')

  return clickList

def GetPositionList(num: int) -> list:
  """获取点击位置列表"""

  positionList = []
  for i in range(num):
    print(f'Get your {i+1} click position: Press Enter to capture the current mouse position.')
    input()
    x, y = pyautogui.position()
    positionList.append((x, y))
    print(f'Captured position: ({x}, {y})')
  return positionList

def RunClick(clickList: list, positionList: list | None, autoStart: bool, repeat: int, startDelay: float, delay: float, wait: float, stopKey: str) -> None:
  """运行点击命令"""
  import time

  # 是否自动执行
  if autoStart is False:
    print('Press enter to start the clicks...')
    input()

  # 移动到目标位置，防止激活时处于窗口外
  if positionList is not None and len(positionList) > 0:
    pyautogui.moveTo(positionList[0][0], positionList[0][1])

  # 激活目标窗口: 部分窗口失焦后需要一次激活
  pyautogui.click()

  # 执行前等待
  pyautogui.sleep(startDelay)

  # 后台监听停止热键，终端失焦时也能停止
  stopControl = StopControl(stopKey)
  print(f'Press [{stopKey}] to stop.')

  if repeat == 0:
    print('Clicking in infinite loop, Ctrl+C to stop...')

  roundCount = 0
  while True:
    roundCount += 1
    for j in range(len(clickList)):
      if stopControl.Stopped():
        break
      if positionList is not None:
        pyautogui.moveTo(positionList[j][0], positionList[j][1])
      clickList[j]()
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
    argParse = ArgParseMouseClickInit(None)
    args = argParse.parse_args()
    ArgCheckMouseClick(args)
    # 生成鼠标操作列表
    if args.list:
      clickList = [CLICK_OPTION[int(c)] for c in args.list.split(',')]
    else:
      clickList = GetClickList(args.num)
    # 生成鼠标点击的位置列表
    positionList = GetPositionList(len(clickList)) if args.move else None
    # 开始执行点击命令
    RunClick(clickList, positionList, args.auto, args.repeat, args.start_delay, args.delay, args.wait, args.stop_key.lower())
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
