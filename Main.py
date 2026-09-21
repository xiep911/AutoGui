# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

import os
import subprocess
import sys

# 各功能 -> Scripts/ 下脚本 + 引导询问的参数模板（flag, 提示, 默认值, 类型）
#  - flag 为 None 表示位置参数（如 replay 的 file）；类型 bool 时只追加开关（y/yes 设置，否则忽略）
#  - 默认值 None 表示留空跳过该参数（用脚本自身的缺省，如 -d 由 KeyPress 回退到 0.1）
_FUNCTIONS = {
  'keypress': {
    'script': 'KeyPress.py',
    'desc': '键盘按键（-l 列表 / -r 重复 / 三态热键）',
    'prefix': [],
    'args': [
      ('-l', '按键列表，逗号分隔（如 a,d）', 'a,d', str),
      ('-r', '重复次数（0=无限循环）', '0', int),
      ('-d', '命令间隔秒（回车=脚本默认 0.1）', None, float),
      ('-w', '轮间等待秒', '0', float),
      ('-k1', '开始热键', 'enter', str),
      ('-k3', '暂停键（留空=禁用）', None, str),
      ('-k2', '结束热键', 'esc', str),
    ],
  },
  'mouseclick': {
    'script': 'MouseClick.py',
    'desc': '鼠标点击（1=左 2=双击 3=右）',
    'prefix': [],
    'args': [
      ('-l', '点击列表，逗号分隔（1=左 2=双击 3=右）', '1', str),
      ('-m', '点击前移动鼠标到坐标？(y/n)', False, bool),
      ('-r', '重复次数（0=无限循环）', '0', int),
      ('-d', '命令间隔秒（回车=脚本默认 0.1）', None, float),
      ('-w', '轮间等待秒', '0', float),
      ('-k1', '开始热键', 'enter', str),
      ('-k3', '暂停键（留空=禁用）', None, str),
      ('-k2', '结束热键', 'esc', str),
    ],
  },
  'record': {
    'script': 'Recorder.py',
    'desc': '录制真实操作到 JSON（Recorder record）',
    'prefix': ['record'],
    'args': [
      ('-o', '输出文件', 'recording.json', str),
      ('-a', '立即开始录制？(y/n)', False, bool),
      ('-k1', '开始热键', 'enter', str),
      ('-s', '开始后缓冲秒', '0', float),
      ('-k2', '停止录制热键', 'esc', str),
    ],
  },
  'replay': {
    'script': 'Recorder.py',
    'desc': '按录制 JSON 节奏回放',
    'prefix': ['replay'],
    'args': [
      (None, '录制文件', None, str),
      ('-r', '重复次数（0=无限循环）', '0', int),
      ('-w', '轮间等待秒', '0', float),
      ('--speed', '回放倍速', '1.0', float),
      ('-a', '立即开始回放？(y/n)', False, bool),
      ('-k1', '开始热键', 'enter', str),
      ('-k3', '暂停键（留空=禁用）', None, str),
      ('-k2', '结束热键', 'esc', str),
    ],
  },
}


def ScriptPath(script: str) -> str:
  """Scripts/ 下脚本的绝对路径"""
  return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Scripts', script)


def ParsePrompt(kind: type, raw: str, default):
  """把用户输入解析为参数值：空输入取默认；bool 只认 y/yes；非法数值返回 None 由调用方重试"""
  if raw == '':
    return default
  if kind is bool:
    return raw.strip().lower() in ('y', 'yes')
  try:
    return kind(raw)
  except ValueError:
    return None


def AskArgs(spec: dict) -> list[str]:
  """按模板引导式询问参数，组装成脚本 argv"""
  argv = []
  for flag, label, default, kind in spec['args']:
    while True:
      prompt = flag if flag is not None else 'file'
      if label:
        prompt += f' ({label})'
      if default is None:
        suffix = ''
      elif kind is bool:
        suffix = f' [默认 {"y" if default else "n"}]'
      else:
        suffix = f' [默认 {default}]'
      raw = input(f'{prompt}{suffix}: ').strip()
      value = ParsePrompt(kind, raw, default)
      if raw != '' and value is None:
        print('Invalid input, please retry.')
        continue
      break
    if value is None:
      continue
    if kind is bool:
      if value:
        argv.append(flag)
      continue
    if flag is None:
      argv.append(str(value))
    else:
      argv.append(flag)
      argv.append(str(value))
  return argv


def RunFunction(name: str, args: list[str]) -> int:
  """在子进程中执行选中脚本并透传参数（继承 stdio，子进程 input()/热键打印照常显示）"""
  spec = _FUNCTIONS[name]
  command = [sys.executable, ScriptPath(spec['script']), *spec['prefix'], *args]
  print('> ' + ' '.join(command))
  try:
    return subprocess.run(command).returncode
  except KeyboardInterrupt:
    print('\nTask interrupted.')
    return 130


def PrintFunctions() -> None:
  """打印功能列表"""
  for i, (name, spec) in enumerate(_FUNCTIONS.items(), 1):
    print(f'  {i}. {name:<10} {spec["desc"]}')


def MenuLoop() -> int:
  """交互菜单：选功能 → 引导填参 → 子进程执行 → 任务结束（真结束/自然结束/放弃）后回到菜单"""
  print('AutoGui Main — 支持子进程无限循环 + 开始/暂停/结束三态热键')
  while True:
    print()
    PrintFunctions()
    print('  0. 退出')
    try:
      choice = input(f'选择功能 (1-{len(_FUNCTIONS)}): ').strip()
    except EOFError:  # 管道输入耗尽（如 echo ... | python Main.py）
      print()
      break
    if choice.lower() in ('0', 'q', 'quit', 'exit'):
      break
    try:
      idx = int(choice)
    except ValueError:
      idx = 0
    if not 1 <= idx <= len(_FUNCTIONS):
      print('无效选择，请重试。')
      continue
    name = list(_FUNCTIONS.keys())[idx - 1]
    try:
      args = AskArgs(_FUNCTIONS[name])
    except EOFError:  # 参数询问阶段输入耗尽，放弃本次任务并结束
      print()
      break
    print()
    ret = RunFunction(name, args)
    if ret != 0:
      print(f'（任务退出码 {ret}）')
  return 0


def main() -> int:
  """无参数进交互菜单；首参数为功能名则直传剩余参数（CLI 模式，可供脚本/批处理调用）"""
  argv = sys.argv[1:]
  if not argv:
    return MenuLoop()
  if argv[0] in ('-h', '--help', '-l', '--list'):
    print('用法: python Main.py [功能] [脚本参数...]   （无参数时进入交互菜单）')
    print('功能列表:')
    PrintFunctions()
    return 0
  name = argv[0]
  if name not in _FUNCTIONS:
    print(f'未知功能: {name}')
    PrintFunctions()
    return 2
  return RunFunction(name, argv[1:])


if __name__ == '__main__':
  try:
    sys.exit(main())
  except KeyboardInterrupt:
    print('\nBye.')
    sys.exit(130)
