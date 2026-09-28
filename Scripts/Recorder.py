# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
import sys
# 允许 Scripts/ 下脚本被直接运行时不破坏 Library 导入（repo 根目录入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse

# 公共逻辑全部在 Library/Include（各模块 __all__ 白名单限定，import * 不引入多余内容）
from Include.Base import *  # noqa: F403  常量（DEFAULT_*/EXIT_*/VERSION）
from Library.Base import *  # noqa: F403  键转换/热键/预设
from Library.Runner import *  # noqa: F403  RunConfig/调度/GuardMain

def ArgParseRecorderInit(parser: argparse.ArgumentParser | None) -> argparse.ArgumentParser:
  """参数解析初始化"""
  if parser is None:
    parser = argparse.ArgumentParser(description='Record and replay mouse & keyboard operations')

  parser.add_argument('-v', '--version', action='version', version=f'AutoGui {VERSION}')
  sub = parser.add_subparsers(dest='command', required=True, metavar='<command>')

  rec = sub.add_parser('record', help='Record user operations to a JSON file')
  rec.add_argument('-v', '--version', action='version', version=f'AutoGui {VERSION}')
  rec.add_argument('-o', '--output', type=str, default='recording.json',
                   help='Output recording file, default: recording.json')
  rec.add_argument('-a', '--auto', action='store_true', default=False,
                   help='Start recording immediately without waiting for the start key')
  rec.add_argument('-k1', '--start-key', type=str, default=DEFAULT_START_KEY,
                   help='Key to press to start recording (global hotkey), default: enter; ignored with -a/--auto')
  rec.add_argument('-s', '--start-delay', type=float, default=0,
                   help='Buffer time(seconds) after start before recording begins, default: 0')
  rec.add_argument('-k2', '--stop-key', type=str, default=DEFAULT_STOP_KEY,
                   help='Key to stop recording (pyautogui key name), default: esc')

  rep = sub.add_parser('replay', help='Replay a recorded JSON file')
  rep.add_argument('file', type=str, help='Recording JSON file')
  AddCommonArgs(rep)
  rep.add_argument('--speed', type=float, default=1.0,
                   help='Replay speed multiplier, e.g. 2 means 2x faster, default: 1.0')

  return parser

def ArgCheckRecorder(args: argparse.Namespace) -> None:
  """参数校验"""
  CheckCommonArgs(args)
  if args.command == 'replay':
    if args.speed <= 0:
      raise ValueError('Invalid replay speed (--speed)')

def main() -> int:
  """主函数"""
  argParse = ArgParseRecorderInit(None)
  args = argParse.parse_args()
  ArgCheckRecorder(args)
  if args.command == 'record':
    # 组装运行参数：-a 时 startKey=None 立即开始；stopKey 归一化后参与停止匹配
    config = RunConfig(startDelay=args.start_delay,
                       startKey=None if args.auto else args.start_key.lower(),
                       stopKey=CanonKey(args.stop_key.lower()))
    Record(args.output, config)
  else:
    # -w 未指定时为 None（AddCommonArgs 缺省，区分预设回退场景），Recorder 无预设直接归一为 0
    wait = args.wait if args.wait is not None else 0
    config = RunConfig(repeat=args.repeat, wait=wait, speed=args.speed,
                       startDelay=args.start_delay,
                       startKey=None if args.auto else args.start_key.lower(),
                       stopKey=CanonKey(args.stop_key.lower()),
                       pauseKey=args.pause_key.lower() if args.pause_key is not None else None)
    Replay(args.file, config)
  return EXIT_OK

if __name__ == '__main__':
  sys.exit(GuardMain(main))
