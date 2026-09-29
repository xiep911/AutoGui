# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

"""AutoGui 统一入口：交互菜单或 CLI 直传，功能与参数模板动态发现自 Scripts/ 各脚本的 argparse 定义。"""

import argparse
import importlib.util
import os
import subprocess
import sys

# 常量来自 Include 数据层（__all__ 白名单限定，import * 不引入多余内容）
from Include.Base import *  # noqa: F403
# 导入整个 Library
from Library.Base import *  # noqa: F403
from Library.Runner import *  # noqa: F403

# 功能发现的脚本集合：每个脚本必须导出 ArgParseInit(parser) 构建其 argparse 定义
# （参数模板、功能描述均由该定义动态提取，加参数/加脚本零同步）
_SCRIPTS = ('KeyPress', 'MouseClick', 'Recorder')

# 功能模板表（由 main() 调 BuildFunctions() 动态构建；None 表示尚未构建）
_FUNCTIONS: dict | None = None


def ScriptPath(script: str) -> str:
  """Scripts/ 下脚本的绝对路径"""
  return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Scripts', script)


def LoadScriptModule(script: str):
  """加载 Scripts/ 下脚本为模块（spec_from_file_location 隔离执行，不污染 sys.modules，
  也不触发脚本的 __main__ 入口）。frozen 模式下 Scripts/ 已作为数据文件打包，同样可加载。"""
  spec = importlib.util.spec_from_file_location(script, ScriptPath(f'{script}.py'))
  if spec is None or spec.loader is None:
    raise ImportError(f'Cannot load script module: {script}')
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


def ActionKind(action) -> type:
  """从 argparse action 判定引导参数类型（bool 开关 / int / float / str）"""
  if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
    return bool
  if action.type is int:
    return int
  if action.type is float:
    return float
  return str


def ExtractArgs(parser: argparse.ArgumentParser) -> list:
  """从 argparse 定义提取引导参数模板（flag, label, default, kind, required）；
  -h/-v 不参与引导；子命令由 BuildFunctions 递归展开。"""
  args = []
  for action in parser._actions:
    if isinstance(action, (argparse._HelpAction, argparse._VersionAction)):
      continue
    args.append({
      'flag': action.option_strings[0] if action.option_strings else None,
      'label': action.help,
      'default': action.default,
      'kind': ActionKind(action),
      # 位置参数（如 file）的 required 属性为 False，引导时允许留空跳过，与脚本缺省行为一致
      'required': bool(action.required),
    })
  return args


def ModuleDesc(mod, parser: argparse.ArgumentParser) -> str:
  """脚本模块 docstring 首行作为功能描述；缺失时退回 argparse description"""
  doc = (mod.__doc__ or '').strip().splitlines()
  return doc[0] if doc else (parser.description or mod.__name__)


def BuildFunctions() -> dict:
  """动态扫描 Scripts/：无子命令的脚本 = 一个功能；有子命令（Recorder）按子命令展开。
  参数模板、默认值、功能描述全部来自各脚本的 ArgParseInit 定义（单一来源）。"""
  funcs = {}
  for script in _SCRIPTS:
    mod = LoadScriptModule(script)
    parser = mod.ArgParseInit(None)
    subs = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
    if not subs:
      funcs[script.lower()] = {
        'script': f'{script}.py',
        'desc': ModuleDesc(mod, parser),
        'prefix': [],
        'args': ExtractArgs(parser),
      }
    else:
      for sub in subs:
        # 子命令 help 存在 _choices_actions 条目（主 help 显示用），子 parser 自身无 .help
        for entry in sub._choices_actions:
          name = entry.dest
          funcs[name] = {
            'script': f'{script}.py',
            'desc': entry.help or name,
            'prefix': [name],
            'args': ExtractArgs(sub.choices[name]),
          }
  return funcs


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
  """按 argparse 提取的模板引导式询问参数，组装成脚本 argv"""
  argv = []
  for a in spec['args']:
    flag, label, default, kind, required = a['flag'], a['label'], a['default'], a['kind'], a['required']
    # 必填项（required 或空字符串默认如 -l）：留空须重输；可选缺省项（如 -d）留空则跳过用脚本默认
    mustInput = required or (isinstance(default, str) and default == '')
    while True:
      prompt = flag if flag is not None else 'file'
      if label:
        prompt += f' ({label})'
      if default is None:
        suffix = '' if mustInput else ' (回车=脚本默认)'
      elif kind is bool:
        suffix = f' [默认 {"y" if default else "n"}]'
      else:
        suffix = f' [默认 {default}]'
      raw = input(f'{prompt}{suffix}: ').strip()
      if mustInput and raw == '':
        print('必填项，请重新输入。')
        continue
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


def RunScriptInProcess(spec: dict, args: list[str]) -> int:
  """frozen（PyInstaller onefile）模式下无独立解释器，于当前进程运行 Scripts 脚本。

  runpy 以 run_name='__main__' 运行，保留脚本的 __main__ 入口语义；argparse 读 sys.argv，
  需临时替换为脚本视角的 argv。
  """
  import runpy
  script = ScriptPath(spec['script'])
  saved_argv = sys.argv
  sys.argv = [script, *spec['prefix'], *args]
  try:
    runpy.run_path(script, run_name='__main__')
    return 0
  except SystemExit as e:
    return e.code if isinstance(e.code, int) else 1
  except OSError as e:
    print(f'Error: {e}')
    return 1
  except KeyboardInterrupt:
    print('\nTask interrupted.')
    return 130
  finally:
    sys.argv = saved_argv


def RunFunction(name: str, args: list[str]) -> int:
  """在子进程中执行选中脚本并透传参数（继承 stdio，子进程 input()/热键打印照常显示）"""
  assert _FUNCTIONS is not None  # main() 已调 BuildFunctions()
  spec = _FUNCTIONS[name]
  command = [sys.executable, ScriptPath(spec['script']), *spec['prefix'], *args]
  print('> ' + ' '.join(command))
  if getattr(sys, 'frozen', False):
    # PyInstaller 单文件打包后 sys.executable 即本程序，子进程方案失效，改为进程内运行
    return RunScriptInProcess(spec, args)
  try:
    return subprocess.run(command).returncode
  except KeyboardInterrupt:
    print('\nTask interrupted.')
    return 130


def PrintFunctions() -> None:
  """打印功能列表"""
  assert _FUNCTIONS is not None  # main() 已调 BuildFunctions()
  for i, (name, spec) in enumerate(_FUNCTIONS.items(), 1):
    print(f'  {i}. {name:<10} {spec["desc"]}')


def MenuLoop() -> int:
  """交互菜单：选功能 → 引导填参 → 子进程执行 → 任务结束（真结束/自然结束/放弃）后回到菜单"""
  assert _FUNCTIONS is not None  # main() 已调 BuildFunctions()
  print(f'AutoGui Main v{VERSION} — 支持子进程无限循环 + 开始/暂停/结束三态热键')
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
  global _FUNCTIONS
  argv = sys.argv[1:]
  if argv and argv[0] in ('-v', '--version'):
    print(f'AutoGui {VERSION}')
    return 0
  try:
    _FUNCTIONS = BuildFunctions()
  except Exception as e:
    print(f'Error: {e}')
    return EXIT_ERROR
  if not argv:
    return MenuLoop()
  if argv[0] in ('-h', '--help'):
    print('用法: python Main.py [功能] [脚本参数...]   （无参数时进入交互菜单）')
    print('  -v/--version  打印版本号')
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
