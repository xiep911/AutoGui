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

def ArgParseKeyPressInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Key press')

  parser.add_argument('file', nargs='?', type=str, default=None,
                      help='Preset JSON file to load (keys, delay, wait)')
  parser.add_argument('-n', '--num', type=int, help='Number of commands (interactive input mode)')
  parser.add_argument('-l', '--list', type=str, default='', help='Comma-separated key list, e.g. "up,down,left,right"')
  AddCommonArgs(parser, withDelay=True, withOutput=True)

  return parser

def ArgCheckKeyPress(args: argparse.Namespace) -> None:
  """参数校验"""

  num = args.num if args.num is not None else 0
  if args.file is not None:
    if num != 0 or args.list:
      raise ValueError('-n/--num and -l/--list are mutually exclusive with a preset file')
  else:
    if num < 0:
      raise ValueError('Invalid key command number (-n/--num)')
    if num == 0 and not args.list:
      raise ValueError('Either -n/--num or -l/--list must be provided')
    if num > 0 and args.list:
      raise ValueError('-n/--num and -l/--list are mutually exclusive')
  if args.list:
    for key in args.list.split(','):
      if not pyautogui.isValidKey(key):
        raise ValueError(f'Invalid key: {key}')
  CheckCommonArgs(args, withDelay=True)

def GetKeyList(num: int) -> list[str]:
  """获取命令列表"""

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

def main() -> int:
  """主函数"""
  argParse = ArgParseKeyPressInit(None)
  args = argParse.parse_args()
  ArgCheckKeyPress(args)
  # 生成按键列表：预设文件 > -l 列表 > 交互输入
  preset = {}
  if args.file is not None:
    preset = LoadPreset(args.file, 'keypress')
    keyList = preset.get('keys', [])
    if (not isinstance(keyList, list)
        or not all(isinstance(k, str) and pyautogui.isValidKey(k) for k in keyList)):
      raise ValueError(f'Invalid keys in preset file: {args.file}')
    print(f'Loaded preset from {os.path.abspath(args.file)}: {len(keyList)} key(s)')
  elif args.list:
    keyList = args.list.split(',')
  else:
    keyList = GetKeyList(args.num)
  if not keyList:  # 空列表 + -r 0 会无限空转，直接报错
    raise ValueError('Empty key list')
  # 节奏参数：CLI 显式值优先，否则取预设值，默认 0
  delay = args.delay if args.delay is not None else GetPresetNumber(preset, 'delay', DEFAULT_DELAY)
  wait = args.wait if args.wait is not None else GetPresetNumber(preset, 'wait', 0)
  # 仅显式指定 -o 时保存预设
  if args.output is not None:
    SavePreset(args.output, {
      'version': 1,
      'type': 'keypress',
      'keys': keyList,
      'delay': delay,
      'wait': wait,
    })
  # 组装运行参数：-a 时 startKey=None 立即开始，否则等 start-key（默认 enter）按下
  config = RunConfig(repeat=args.repeat, delay=delay, wait=wait, startDelay=args.start_delay,
                     startKey=None if args.auto else args.start_key.lower(),
                     stopKey=args.stop_key.lower(),
                     pauseKey=args.pause_key.lower() if args.pause_key is not None else None)
  return RunPress(config, keyList)

if __name__ == '__main__':
  sys.exit(GuardMain(main))
