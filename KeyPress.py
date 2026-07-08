# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import argparse
import pyautogui

def ArgParseKeyPressInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Key press')

  parser.add_argument('-n', '--num', type=int, required=True, help='Number of commands')
  parser.add_argument('-r', '--repeat', type=int, required=True, help='Number of repeat times')
  parser.add_argument('-d', '--delay', type=float, default=0, help='Time(seconds) to wait between each command in commands list')
  parser.add_argument('-w', '--wait', type=float, default=0, help='Time(seconds) to wait after executing the commands list once')
  parser.add_argument('-a', '--auto', action='store_true', default=False, help='Auto start key press without waiting for Enter')
  parser.add_argument('-s', '--start-delay', type=float, default=0, help='Time(seconds) to wait before starting key press')

  return parser

def ArgCheckKeyPress(args: argparse.Namespace) -> None:
  """参数校验"""

  if args.num <= 0:
    raise ValueError('Invalid click command number (-n/--num)')
  if args.repeat <= 0:
    raise ValueError('Invalid repeat times (-r/--repeat)')
  if args.delay < 0:
    raise ValueError('Invalid delay time (-d/--delay)')
  if args.wait < 0:
    raise ValueError('Invalid wait time (-w/--wait)')
  if args.start_delay < 0:
    raise ValueError('Invalid start delay time (-s/--start-delay)')

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

def RunPress(keyList: list[str], autoStart: bool, startDelay: float, repeat: int, delay: float, wait: float) -> None:
  """运行点击命令"""
  import time

  # 是否自动执行
  if autoStart is False:
    print('Press enter to start the key press...')
    input()

  # 激活目标窗口: 部分窗口失焦后需要一次激活
  pyautogui.click()

  # 执行前等待
  pyautogui.sleep(startDelay)

  for i in range(repeat):
    for j in range(len(keyList)):
      pyautogui.press(keyList[j])
      time.sleep(delay)
    time.sleep(wait)
    print(f'Run {i+1}/{repeat} times')

def main():
  """主函数"""
  try:
    # 解析参数
    argParse = ArgParseKeyPressInit(None)
    args = argParse.parse_args()
    ArgCheckKeyPress(args)
    # 生成按键列表
    keyList = GetKeyList(args.num)
    # 开始执行按键命令
    RunPress(keyList, args.auto, args.start_delay, args.repeat, args.delay, args.wait)
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
