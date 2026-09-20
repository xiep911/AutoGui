# Git SSH 提交签名 — 配置指南

本仓库要求 `main` 分支的提交带有**已验证签名**（见仓库保护规则 "Commits must have verified signatures"）。新工作机上开发前，按本文配好 SSH 提交签名。整套流程约 3 分钟。

采用 **SSH 签名**（而非 GPG）：直接用已有的 `ed25519` SSH 密钥，零额外安装，GitHub 支持良好。

---

## 一、一键脚本（推荐）

仓库内已提供脚本 [Scripts/SetupGitSigning.sh](../Scripts/SetupGitSigning.sh)，自动完成全部配置并在临时仓库实际提交验证。

```bash
# 1. 在本仓库内（或任意仓库内）执行，默认全局配置
cd <你的工作目录>
bash Scripts/SetupGitSigning.sh

# 只给当前仓库配（不影响其他仓库）
bash Scripts/SetupGitSigning.sh --local
```

脚本会：
1. 检查 git ≥ 2.34
2. 复用或生成 `~/.ssh/id_ed25519`
3. 把公钥注册为 GitHub **Signing Key**（若无 `gh` 或权限，会打印公钥让你手动操作）
4. 写 git 配置：`gpg.format=ssh`、`user.signingkey`、`commit.gpgsign=true`、本地验证文件
5. 临时仓库真实提交 + `Good "git" signature` 自检（完成即自动清理）

参数：

| 参数 | 说明 |
|------|------|
| `--global` | 写入 `~/.gitconfig`（默认，所有仓库生效） |
| `--local` | 仅写入当前仓库 `.git/config` |
| `--key <path>` | 指定已有公钥（默认 `~/.ssh/id_ed25519.pub`） |
| `--no-register` | 跳过 GitHub 注册步骤（已注册过时用） |
| `--no-verify` | 跳过临时仓库验证（环境限制时用） |

---

## 二、纯手动步骤（脚本不可用/想看细节时）

### 1. 准备 ed25519 密钥

```bash
# 若 ~/.ssh/id_ed25519 不存在则生成（无密码短语）
ssh-keygen -t ed25519 -C "you@example.com" -f ~/.ssh/id_ed25519 -N ""
```

### 2. 注册 GitHub Signing Key

打开 https://github.com/settings/ssh/new ，填写：

- **Key type**：`Signing Key`（注意：不是 Authentication Key）
- **Key**：`cat ~/.ssh/id_ed25519.pub` 的内容

或用 gh CLI（需 `admin:ssh_signing_key` scope，会引导授权一次）：

```bash
gh api user/ssh_signing_keys -f title="$(hostname)-ed25519" -f key="$(cat ~/.ssh/id_ed25519.pub)"
# 若缺 scope：gh auth refresh -h github.com -s admin:ssh_signing_key
```

> 同一把公钥可同时既作 Authentication Key（推送鉴权）又作 Signing Key（提交签名），互不影响。

### 3. 配置 git 使用 SSH 签名

```bash
# 全局所有仓库生效，或换成 --local 只对当前仓库生效
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true          # 以后每次提交自动签名
```

### 4. 配置本地签名校验文件（可选但推荐）

不配也能推送，GitHub 端会自行验证；配了本地 `git log` 也能显示 `Good`：

```bash
echo "you@example.com $(awk '{print "ssh-ed25519 " $2}' ~/.ssh/id_ed25519.pub)" >> ~/.ssh/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
```

### 5. 验证

```bash
# 在任意目录建个临时仓库提交测试
tmp=$(mktemp -d); cd "$tmp"; git init
git config user.name "you"; git config user.email "you@example.com"
echo test > f; git add f; git commit -m test
git log --show-signature -1    # 应显示: Good "git" signature ... ED25519
cd -; rm -rf "$tmp"
```

推送后到 GitHub 查看该提交是否出现 **Verified** 徽标。

---

## 三、常见问题与踩坑

| 现象 | 原因 / 处理 |
|------|------------|
| 推送被拒提示 commits must have signed signatures | 保护规则拦截，重新提交已签名的 commit（重做提交或按本文配置后 amend） |
| 本地 `git log --show-signature` 报 `allowedSignersFile needs to be configured` | 漏了第 4 步，或该文件里没有你的邮箱+公钥行 |
| 本地报 `Good "git" signature` 但 GitHub 不显示 Verified | 公钥没注册为 **Signing Key**，或注册成了 Authentication Key（要补注册 Signing Key） |
| 改了 `core.sshCommand` 后 push/拉取异常 | 不要为签名去配 `core.sshCommand`。SSH 签名不依赖它，误配会强制全部 SSH 走指定密钥，破坏鉴权。若误配：`git config --global --unset-all core.sshCommand` |
| 提交邮箱与签名 principal 不一致导致本地校验警告 | `allowed_signers` 按邮箱匹配，若仓库提交用 GitHub noreply 邮箱（形如 `12345678+username@users.noreply.github.com`），配置时 `user.email` 也应用同一邮箱，保持链条一致 |
| 提交无自动签名（commit 不出现 gpgsig） | 检查 `commit.gpgsign` 是否为 `true`，且签名密钥路径写对 |

---

## 四、为什么用 SSH 而非 GPG

| | SSH 签名 | GPG 签名 |
|---|---|---|
| 额外安装 | 无需，复用 SSH 密钥 | 需安装 GPG 并管理密钥/agent |
| 配置量 | 3 条 git config | 密钥生成 + 导出 + GitHub 注册 + git config |
| Windows 支持 | 好（git ≥ 2.34 内置） | 一般（需配 gpg 路径与 agent） |
| 维护成本 | 低 | 中（换机要导出/导入密钥） |

---

## 五、签名策略说明

- 本仓库 `main` 保护规则要求签名提交，但 `enforce_admins` 关闭（管理员可绕过）。
- 仓库级/全局是否强制签名由各工作机自定；正式提交建议全部签名以保证合规。
- 已合入的无签名历史提交**不回写**（保持简单；如需彻底合规可另走 rebase，**需 force push，慎用**）。
