# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
import sys
# 允许 Scripts/ 下脚本被直接运行时不破坏 Library 导入（repo 根目录入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

import pyautogui
# 公共逻辑全部在 Library/Include（各模块 __all__ 白名单限定，import * 不引入多余内容）
from Include.Base import *  # noqa: F403  常量（DEFAULT_*/EXIT_*/VERSION）
from Library.Base import *  # noqa: F403  键转换/热键/预设
from Library.Runner import *  # noqa: F403  RunConfig/调度/GuardMain

def ArgParseMouseClickInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Click mouse')

  parser.add_argument('file', nargs='?', type=str, default=None,
                      help='Preset JSON file to load (clicks, positions, delay, wait)')
  parser.add_argument('-n', '--num', type=int, help='Number of click commands (interactive input mode)')
  parser.add_argument('-l', '--list', type=str, default='', help='Comma-separated click list, e.g. "1,2,3" (1=left, 2=double, 3=right)')
  parser.add_argument('-m', '--move', action='store_true', default=False, help='Move mouse to position before clicking')
  AddCommonArgs(parser, withDelay=True, withOutput=True)

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
  CheckCommonArgs(args, withDelay=True)

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

def main() -> int:
  """主函数"""
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
  # 组装运行参数：-a 时 startKey=None 立即开始，否则等 start-key（默认 enter）按下
  config = RunConfig(repeat=args.repeat, delay=delay, wait=wait, startDelay=args.start_delay,
                     startKey=None if args.auto else args.start_key.lower(),
                     stopKey=args.stop_key.lower(),
                     pauseKey=args.pause_key.lower() if args.pause_key is not None else None)
  return RunClick(config, clickList, positionList)

if __name__ == '__main__':
  sys.exit(GuardMain(main))
