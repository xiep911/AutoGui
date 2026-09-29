# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

"""数据定义层：常量与按键名归一数据（零依赖，供 Library 与脚本引用）。"""

# 未指定 -d 且无预设时的每命令间隔（秒）
DEFAULT_DELAY = 0.1

# 开始/结束热键默认值（脚本 argparse 与 Main.py 模板共用）
DEFAULT_START_KEY = 'enter'
DEFAULT_STOP_KEY = 'esc'

# 热键轮询/分片睡眠间隔（秒），暂停与等待阶段用
POLL_INTERVAL = 0.05
# 暂停冻结调度时钟时的细粒度轮询间隔（秒），Recorder 回放专用
PAUSE_POLL_INTERVAL = 0.02

# 统一进程退出码（Scripts/ 与 Main.py 共用，供 CLI 与 CI 区分成功/失败/用户中断）
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INTERRUPTED = 130

# 统一版本号（Main.py 与 Scripts/ 共用，发布时统一递增）
VERSION = '1.1.0'

# pyautogui 同一键有多种写法 -> 归一到同一形式（用于停止键/停止录制键匹配）
KEY_ALIASES = {
  'esc': 'esc', 'escape': 'esc',
  'pageup': 'pageup', 'pgup': 'pageup',
  'pagedown': 'pagedown', 'pgdn': 'pagedown',
  'ctrl': 'ctrl', 'ctrlleft': 'ctrl', 'ctrlright': 'ctrl',
  'shift': 'shift', 'shiftleft': 'shift', 'shiftright': 'shift',
  'alt': 'alt', 'altleft': 'alt', 'altright': 'alt',
  'cmd': 'win', 'command': 'win', 'win': 'win',
  'enter': 'enter', 'return': 'enter',
  'numlock': 'numlock', 'capslock': 'capslock', 'scrolllock': 'scrolllock',
  'printscreen': 'printscreen', 'up': 'up', 'down': 'down',
  'left': 'left', 'right': 'right', 'space': 'space', 'tab': 'tab',
}

# 需要 Shift 组合的符号 -> 基础键（Shift 状态由独立的 keydown/keyup 事件表达）
SHIFT_MAP = {
  '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6',
  '&': '7', '*': '8', '(': '9', ')': '0', '_': '-', '+': '=',
  '{': '[', '}': ']', '|': '\\', '"': "'", ':': ';', '<': ',',
  '>': '.', '?': '/', '~': '`'
}

__all__ = ['DEFAULT_DELAY', 'DEFAULT_START_KEY', 'DEFAULT_STOP_KEY',
           'POLL_INTERVAL', 'PAUSE_POLL_INTERVAL',
           'EXIT_OK', 'EXIT_ERROR', 'EXIT_INTERRUPTED', 'VERSION',
           'KEY_ALIASES', 'SHIFT_MAP']
