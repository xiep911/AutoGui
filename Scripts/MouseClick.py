# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
import sys
import time
# 允许 Scripts/ 下脚本被直接运行时不破坏 Library 导入（repo 根目录入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

import pyautogui
from Library.Base import (DEFAULT_DELAY, DEFAULT_START_KEY, DEFAULT_STOP_KEY, GetPresetNumber,
                          LoadPreset, PauseControl, SavePreset, SleepResponsive, StopControl,
                          ValidateDistinctHotkeys, ValidateHotkey, ValidatePauseKey,
                          WaitResumeOrStop, WaitStartHotkey)

CLICK_OPTION = {
  1: pyautogui.click,
  2: pyautogui.doubleClick,
  3: pyautogui.rightClick
}

def ArgParseMouseClickInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Click mouse')

  parser.add_argument('file', nargs='?', type=str, default=None,
                      help='Preset JSON file to load (clicks, positions, delay, wait)')
  parser.add_argument('-n', '--num', type=int, help='Number of click commands (interactive input mode)')
  parser.add_argument('-l', '--list', type=str, default='', help='Comma-separated click list, e.g. "1,2,3" (1=left, 2=double, 3=right)')
  parser.add_argument('-r', '--repeat', type=int, required=True, help='Number of repeat times, 0 for infinite loop')
  parser.add_argument('-m', '--move', action='store_true', default=False, help='Move mouse to position before clicking')
  parser.add_argument('-a', '--auto', action='store_true', default=False,
                      help='Start clicks immediately without waiting for the start key')
  parser.add_argument('-s', '--start-delay', type=float, default=0, help='Time(seconds) to wait before starting clicks')
  parser.add_argument('-d', '--delay', type=float, default=None,
                      help='Time(seconds) between clicks, default: 0.1 or preset value if not given')
  parser.add_argument('-w', '--wait', type=float, default=None,
                      help='Time(seconds) after one round, default: 0 or preset value if not given')
  parser.add_argument('-k1', '--start-key', type=str, default=DEFAULT_START_KEY,
                      help='Key to press to start the clicks (global hotkey), default: enter; ignored with -a/--auto')
  parser.add_argument('-k2', '--stop-key', type=str, default=DEFAULT_STOP_KEY, help='Key to stop and end the clicks (global hotkey), default: esc')
  parser.add_argument('-k3', '--pause-key', type=str, default=None,
                      help='Key to toggle pause/resume during the loop (global hotkey), default: disabled')
  parser.add_argument('-o', '--output', type=str, default=None,
                      help='Save the click commands (+positions/delay/wait) to a preset JSON file')

  return parser

def ArgCheckMouseClick(args: argparse.Namespace) -> None:
  """参数校验"""

  num = args.num if args.num is not None else 0
  if args.file is not None:
    if num != 0 or args.list:
      raise ValueError('-n/--num and -l/--list are mutually exclusive with a preset file')
    if args.move:
      raise ValueError('-m/--move and a preset file are mutually exclusive (preset provides positions)')
  else:
    if num < 0:
      raise ValueError('Invalid click command number (-n/--num)')
    if num == 0 and not args.list:
      raise ValueError('Either -n/--num or -l/--list must be provided')
    if num > 0 and args.list:
      raise ValueError('-n/--num and -l/--list are mutually exclusive')
  if args.list:
    for c in args.list.split(','):
      if c not in ('1', '2', '3'):
        raise ValueError(f'Invalid click command: {c}. Must be 1 (left), 2 (double), or 3 (right).')
  if args.repeat < 0:
    raise ValueError('Invalid repeat times (-r/--repeat), 0 for infinite loop')
  if args.delay is not None and args.delay < 0:
    raise ValueError('Invalid delay time (-d/--delay)')
  if args.wait is not None and args.wait < 0:
    raise ValueError('Invalid wait time (-w/--wait)')
  if args.start_delay < 0:
    raise ValueError('Invalid start delay time (-s/--start-delay)')
  ValidateHotkey(args.start_key.lower(), 'start')
  ValidateHotkey(args.stop_key.lower(), 'stop')
  ValidateDistinctHotkeys(args.start_key.lower(), args.stop_key.lower())
  ValidatePauseKey(args.pause_key.lower() if args.pause_key is not None else None,
                   args.start_key.lower(), args.stop_key.lower())

def GetClickList(num: int) -> list:
  """获取点击命令列表（返回 1/2/3 数字，运行时映射到点击函数）"""

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
        clickList.append(click)
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

def RunClick(clickList: list, positionList: list | None, startDelay: float, startKey: str | None, repeat: int, delay: float, wait: float, stopKey: str, pauseKey: str | None = None) -> None:
  """运行点击命令"""
  # 后台监听停止热键，终端失焦时也能停止；等待开始阶段即生效（按停止键=放弃本次执行）
  stopControl = StopControl(stopKey)
  print(f'Press [{stopKey}] to stop.')

  # 是否自动执行：-a 时传入的 startKey 为 None 直接开始，否则等待开始热键（或按停止键放弃）
  if startKey is not None:
    if not WaitStartHotkey(startKey, stopControl, 'clicks'):
      return

  # 执行前等待
  pyautogui.sleep(startDelay)

  # 暂停/继续 切换监听（-k3，默认关闭）
  pauseControl = PauseControl(pauseKey) if pauseKey is not None else None

  if repeat == 0:
    print('Clicking in infinite loop, Ctrl+C (terminal focused) to stop...')

  roundCount = 0
  while True:
    for j in range(len(clickList)):
      # 暂停期间阻塞等待恢复或结束
      if WaitResumeOrStop(stopControl, pauseControl):
        break
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
    # 中途被停止键打断的未完成轮不计入轮数
    if stopControl.Stopped():
      break
    roundCount += 1
    # 轮间等待：分片睡眠并响应 -k2 停止 / -k3 暂停（全局热键，失焦也能按）
    if wait > 0 and SleepResponsive(wait, stopControl, pauseControl):
      break
    if repeat > 0 and roundCount >= repeat:
      break
  stopControl.Stop()
  if pauseControl is not None:
    pauseControl.Stop()
  if stopControl.Stopped():
    print(f'Stopped by [{stopKey}] after {roundCount} round(s).')
  else:
    print(f'Clicks finished: {roundCount} round(s).')

def main():
  """主函数"""
  try:
    # 解析参数
    argParse = ArgParseMouseClickInit(None)
    args = argParse.parse_args()
    ArgCheckMouseClick(args)
    # 生成鼠标操作列表：预设文件 > -l 列表 > 交互输入
    preset = {}
    if args.file is not None:
      preset = LoadPreset(args.file, 'mouseclick')
      clickList = preset.get('clicks', [])
      if (not isinstance(clickList, list)
          or not all(isinstance(c, int) and not isinstance(c, bool) and c in CLICK_OPTION for c in clickList)):
        raise ValueError(f'Invalid click commands in preset file: {args.file}')
      positions = preset.get('positions', [])
      positionList = None
      if positions:
        if (not isinstance(positions, list) or len(positions) != len(clickList)
            or not all(isinstance(p, list) and len(p) == 2 for p in positions)):
          raise ValueError(f'Invalid positions in preset file: {args.file}')
        positionList = [(int(p[0]), int(p[1])) for p in positions]
      print(f'Loaded preset from {os.path.abspath(args.file)}: {len(clickList)} click(s)')
    else:
      if args.list:
        clickList = [int(c) for c in args.list.split(',')]
      else:
        clickList = GetClickList(args.num)
      if not clickList:  # 空列表 + -r 0 会无限空转，直接报错
        raise ValueError('Empty click list')
      # 生成鼠标点击的位置列表
      positionList = GetPositionList(len(clickList)) if args.move else None
    # 节奏参数：CLI 显式值优先，否则取预设值，默认 0
    delay = args.delay if args.delay is not None else GetPresetNumber(preset, 'delay', DEFAULT_DELAY)
    wait = args.wait if args.wait is not None else GetPresetNumber(preset, 'wait', 0)
    # 仅显式指定 -o 时保存预设
    if args.output is not None:
      SavePreset(args.output, {
        'version': 1,
        'type': 'mouseclick',
        'clicks': clickList,
        'positions': [list(p) for p in positionList] if positionList else [],
        'delay': delay,
        'wait': wait,
      })
    # 开始执行点击命令：-a 时关闭开始热键等待，否则等 start-key（默认 enter）按下
    startKey = None if args.auto else args.start_key.lower()
    pauseKey = args.pause_key.lower() if args.pause_key is not None else None
    RunClick(clickList, positionList, args.start_delay, startKey, args.repeat, delay, wait, args.stop_key.lower(), pauseKey)
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
