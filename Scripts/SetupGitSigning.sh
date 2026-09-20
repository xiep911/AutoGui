#!/usr/bin/env bash
# =============================================================================
# SetupGitSigning.sh — 为新工作机一键配置 Git SSH 提交签名（GitHub 场景）
#
# 做什么：
#   1. 检查 git >= 2.34（SSH 签名最低要求）
#   2. 确认/生成 ed25519 SSH 密钥
#   3. 把公钥注册为 GitHub SSH Signing Key（需 gh 授权一次）
#   4. 配置 git 签名（默认 --global；可用 --local 仅作用于当前仓库）
#   5. 写入 ~/.ssh/allowed_signers（本地验证签名用）
#   6. 在临时仓库真实提交 + 验证签名（自动清理）
#
# 用法：
#   bash SetupGitSigning.sh [--global|--local] [--key <pub_key_path>]
#
#   参数：
#     --global        应用到 ~/.gitconfig（默认）
#     --local         仅写入当前仓库 .git/config（在目标仓库内运行）
#     --key <path>    指定已存在的公钥（默认 ~/.ssh/id_ed25519.pub）
#     --no-register   跳过 GitHub 注册步骤（已注册过时用）
#     --no-verify     跳过临时仓库签名验证（环境权限受限时用）
#
# 退出码：0 成功；非 0 失败
# =============================================================================

set -euo pipefail

# ---------- 默认值 ----------
SCOPE="--global"
KEY_PUB="${HOME}/.ssh/id_ed25519.pub"
DO_REGISTER=1
DO_VERIFY=1

# ---------- 解析参数 ----------
while (($#)); do
  case "$1" in
    --global)       SCOPE="--global"; shift ;;
    --local)        SCOPE="--local";  shift ;;
    --key)          KEY_PUB="$2"; shift 2 ;;
    --no-register)  DO_REGISTER=0;    shift ;;
    --no-verify)    DO_VERIFY=0;      shift ;;
    -h|--help)
      echo "用法: bash $0 [--global|--local] [--key <pub>] [--no-register] [--no-verify]"
      exit 0 ;;
    *)  echo "未知参数: $1"; exit 1 ;;
  esac
done

# ---------- 配色与输出 ----------
C_G="\033[32m"; C_Y="\033[33m"; C_R="\033[31m"; C_B="\033[1m"; C_0="\033[0m"
info() { echo -e "${C_G}[OK]${C_0} $*"; }
warn() { echo -e "${C_Y}[!!]${C_0} $*"; }
fail() { echo -e "${C_R}[XX]${C_0} $*"; exit 1; }
step() { echo; echo -e "${C_B}==> $*${C_0}"; }

# ---------- 1. 前置检查 ----------
step "检查 git 版本（SSH 签名需 >= 2.34）"
command -v git >/dev/null 2>&1 || fail "未安装 git"
GIT_V=$(git --version)
echo "   $GIT_V"
GIT_VNUM=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
MAJOR=${GIT_VNUM%%.*}; MINOR=${GIT_VNUM##*.}
if [ "$MAJOR" -lt 2 ] || { [ "$MAJOR" -eq 2 ] && [ "$MINOR" -lt 34 ]; }; then
  warn "SSH 签名需要 git >= 2.34，当前 $GIT_V。可直接提交但会失败，请升级。"
fi

step "检查用户身份"
GIT_NAME=$(git config user.name)
GIT_MAIL=$(git config user.email)
echo "   name : ${GIT_NAME:-<未配置>}"
echo "   email: ${GIT_MAIL:-<未配置>}"
[ -n "${GIT_MAIL}" ] || fail "未配置 user.email。先: git config --global user.email you@mail.com"
[ -n "${GIT_NAME}" ] || warn "未配置 user.name，建议: git config --global user.name '你的名字'"

# ---------- 2. 确认/生成 ed25519 密钥 ----------
step "检查 SSH 签名密钥: $KEY_PUB"
if [ -f "$KEY_PUB" ]; then
  info "已存在"
  ssh-keygen -lf "$KEY_PUB" | sed 's/^/   /'
else
  KEY_PRIV="${KEY_PUB%.pub}"
  warn "未找到 $KEY_PUB，现生成（无密码短语，回车到底）："
  ssh-keygen -t ed25519 -C "$GIT_MAIL" -f "$KEY_PRIV" -N ""
  info "已生成 $KEY_PUB"
fi

# ---------- 3. 注册 GitHub Signing Key ----------
if [ "$DO_REGISTER" = "1" ]; then
  step "注册 GitHub SSH Signing Key"
  KEY_B64=$(awk '{print $2}' "$KEY_PUB")
  if command -v gh >/dev/null 2>&1; then
    if ! gh auth status >/dev/null 2>&1; then
      warn "gh 未登录，先执行: gh auth login"
      warn "公钥如下，也可手动去 https://github.com/settings/ssh/new 注册（类型选 Signing Key）："
      cat "$KEY_PUB"
    else
      if gh api user/ssh_signing_keys --jq '.[].key' 2>/dev/null | grep -qF "$KEY_B64"; then
        info "该公钥已注册为 GitHub Signing Key，跳过"
      else
        if ! gh api user/ssh_signing_keys -f title="$(hostname)-ed25519" \
               -f key="$(cat "$KEY_PUB")" >/dev/null 2>&1; then
          warn "缺少 admin:ssh_signing_key scope，需要授权一次（复制设备码，浏览器确认）："
          gh auth refresh -h github.com -s admin:ssh_signing_key
          gh api user/ssh_signing_keys -f title="$(hostname)-ed25519" \
                 -f key="$(cat "$KEY_PUB")" >/dev/null \
            || fail "注册失败，请检查网络/已登录的 gh"
        fi
        info "已注册为 Signing Key"
      fi
    fi
  else
    warn "未安装 gh CLI，请手动注册："
    warn "   1. 打开 https://github.com/settings/ssh/new"
    warn "   2. 类型选 'Signing Key'，粘贴下面公钥，标题随意，Add"
    cat "$KEY_PUB"
  fi
else
  info "跳过 GitHub 注册（--no-register）"
fi

# ---------- 4. git 签名配置 ----------
step "配置 git 签名（${SCOPE}）"
git config "$SCOPE" gpg.format ssh
git config "$SCOPE" user.signingkey "$KEY_PUB"
git config "$SCOPE" commit.gpgsign true

AS="${HOME}/.ssh/allowed_signers"
touch "$AS"
PUB_FMT="$(awk '{print " ssh-ed25519 " $2}' "$KEY_PUB")"
if grep -qF "$PUB_FMT" "$AS"; then
  info "allowed_signers 已含本公钥"
else
  printf '%s%s\n' "$GIT_MAIL" "$PUB_FMT" >> "$AS"
  info "已追加 $AS"
fi
git config "$SCOPE" gpg.ssh.allowedSignersFile "$AS"

echo "   gpg.format         = $(git config "$SCOPE" gpg.format)"
echo "   user.signingkey    = $(git config "$SCOPE" user.signingkey)"
echo "   commit.gpgsign     = $(git config "$SCOPE" commit.gpgsign)"
echo "   allowedSignersFile = $AS"

# ---------- 5. 临时仓库签名验证 ----------
if [ "$DO_VERIFY" = "1" ]; then
  step "真实提交验证签名（临时仓库，完成后自动删除）"
  TMPD=$(mktemp -d)
  pushd "$TMPD" >/dev/null
  git init -q
  git config user.name "$GIT_NAME"
  git config user.email "$GIT_MAIL"
  git config gpg.format ssh
  git config user.signingkey "$KEY_PUB"
  git config commit.gpgsign true
  git config gpg.ssh.allowedSignersFile "$AS"
  echo "sign test" > f.txt
  git add f.txt
  git commit -q -m "sign test"
  OUT=$(git log --show-signature -1 2>&1)
  popd >/dev/null
  rm -rf "$TMPD"

  if echo "$OUT" | grep -q 'Good "git" signature'; then
    info "签名验证通过: Good 'git' signature"
  else
    warn "签名已生成，但本地验证输出异常（以 GitHub 页面 Verified 为准）："
    echo "$OUT" | sed 's/^/   /'
  fi
fi

step "全部完成 ✓"
echo "   今后本机提交将自动 SSH 签名。"
echo "   仓库级配置（仅本目录生效）方式：在目标仓库内用 --local 重跑一次即可。"
