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

def ArgParseKeyPressInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Key press')

  parser.add_argument('file', nargs='?', type=str, default=None,
                      help='Preset JSON file to load (keys, delay, wait)')
  parser.add_argument('-n', '--num', type=int, help='Number of commands (interactive input mode)')
  parser.add_argument('-l', '--list', type=str, default='', help='Comma-separated key list, e.g. "up,down,left,right"')
  parser.add_argument('-r', '--repeat', type=int, required=True, help='Number of repeat times, 0 for infinite loop')
  parser.add_argument('-d', '--delay', type=float, default=None,
                      help='Time(seconds) between commands, default: 0.1 or preset value if not given')
  parser.add_argument('-w', '--wait', type=float, default=None,
                      help='Time(seconds) after one round, default: 0 or preset value if not given')
  parser.add_argument('-a', '--auto', action='store_true', default=False,
                      help='Start key press immediately without waiting for the start key')
  parser.add_argument('-s', '--start-delay', type=float, default=0, help='Time(seconds) to wait before starting key press')
  parser.add_argument('-k1', '--start-key', type=str, default=DEFAULT_START_KEY,
                      help='Key to press to start the key press (global hotkey), default: enter; ignored with -a/--auto')
  parser.add_argument('-k2', '--stop-key', type=str, default=DEFAULT_STOP_KEY, help='Key to stop and end the key press (global hotkey), default: esc')
  parser.add_argument('-k3', '--pause-key', type=str, default=None,
                      help='Key to toggle pause/resume during the loop (global hotkey), default: disabled')
  parser.add_argument('-o', '--output', type=str, default=None,
                      help='Save the command list (+delay/wait) to a preset JSON file')

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

def RunPress(keyList: list[str], startDelay: float, startKey: str | None, repeat: int, delay: float, wait: float, stopKey: str, pauseKey: str | None = None) -> None:
  """运行按键命令"""
  # 后台监听停止热键，终端失焦时也能停止；等待开始阶段即生效（按停止键=放弃本次执行）
  stopControl = StopControl(stopKey)
  print(f'Press [{stopKey}] to stop.')

  # 是否自动执行：-a 时传入的 startKey 为 None 直接开始，否则等待开始热键（或按停止键放弃）
  if startKey is not None:
    if not WaitStartHotkey(startKey, stopControl, 'key press'):
      return

  # 执行前等待
  pyautogui.sleep(startDelay)

  # 暂停/继续 切换监听（-k3，默认关闭）
  pauseControl = PauseControl(pauseKey) if pauseKey is not None else None

  if repeat == 0:
    print('Pressing keys in infinite loop, Ctrl+C (terminal focused) to stop...')

  roundCount = 0
  while True:
    for j in range(len(keyList)):
      # 暂停期间阻塞等待恢复或结束
      if WaitResumeOrStop(stopControl, pauseControl):
        break
      # delay 注入 pyautogui interval（轮末最后一条 interval=0 以消除 delay+wait 叠加，wait 为纯轮间间隔）
      # 依赖 pyautogui 0.9.52+ 每次调用后必 sleep(interval)（requirements.txt 已锁最低版本）
      pyautogui.press(keyList[j], presses=1, interval=0.0 if j == len(keyList) - 1 else delay)
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
    print(f'Key press finished: {roundCount} round(s).')

def main():
  """主函数"""
  try:
    # 解析参数
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
    # 开始执行按键命令：-a 时关闭开始热键等待，否则等 start-key（默认 enter）按下
    startKey = None if args.auto else args.start_key.lower()
    pauseKey = args.pause_key.lower() if args.pause_key is not None else None
    RunPress(keyList, args.start_delay, startKey, args.repeat, delay, wait, args.stop_key.lower(), pauseKey)
  except KeyboardInterrupt:
    print('\nInterrupted by user.')
  except Exception as e:
    print(f'Error: {e}')

if __name__ == '__main__':
  main()
