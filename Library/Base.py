# Copyright (c) 2026 xiepeng. All rights reserved.
#
# SPDX-License-Identifier: MIT

"""公共基础库：按键名归一与参数预设存取（脚本直接使用的共享 API）。"""

import json
import os

from Include.Base import *  # noqa: F403

def CanonKey(name: str) -> str:
  """把键名归一到 KEY_ALIASES 定义的形式；未定义时原样返回"""
  return KEY_ALIASES.get(name, name)

# --- 参数预设文件（KeyPress/MouseClick 的录制与回放） ---

def LoadPreset(path: str, expectedType: str) -> dict:
  """加载参数预设文件，校验 version 与 type，返回数据 dict；非法时抛 ValueError。"""
  try:
    with open(path, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except OSError:
    raise ValueError(f'Cannot open preset file: {path}')
  except json.JSONDecodeError:
    raise ValueError(f'Invalid JSON in preset file: {path}')
  if not isinstance(data, dict) or data.get('version') != 1:
    raise ValueError(f'Unsupported preset file (version): {path}')
  if data.get('type') != expectedType:
    raise ValueError(f'Preset type mismatch in {path}: expected {expectedType}, got {data.get("type")!r}')
  return data

def SavePreset(path: str, data: dict) -> None:
  """保存参数预设文件，并提示保存的文件位置和名称"""
  with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  print(f'Preset saved to: {os.path.abspath(path)}')

def GetPresetNumber(data: dict, key: str, default: float = 0.0) -> float:
  """取预设中的数值参数（delay/wait 等）并校验合法性，非法时抛 ValueError。"""
  value = data.get(key, default)
  if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
    raise ValueError(f'Invalid preset value for {key}: {value!r}')
  return float(value)

__all__ = ['CanonKey', 'LoadPreset', 'SavePreset', 'GetPresetNumber']
