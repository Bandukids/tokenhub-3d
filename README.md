# TokenHub 3D Skill

通过腾讯 TokenHub 使用 Tripo 3D 和腾讯混元 3D。在 Codex 中发起生成时，如果没有指定模型，Skill 会先询问你要用哪一个。

| 系列 | 生成模型 | 部分后处理能力 |
|---|---|---|
| Tripo | Tripo 3.1、Tripo P1 | 绑骨检查、绑骨、预设动画、格式转换 |
| 腾讯混元 | 专业版 3.1 / 3.0、Express | 组件拆分、减面、重拓扑、格式转换、纹理、UV、绑骨、文生动作 |

两套客户端均支持文字和图片生成。Tripo 使用可访问的 HTTPS 图片链接。混元可直接读取本地参考图，多视图使用专业版。

## 安装到 Codex

需要 Python 3.10 或更高版本。客户端仅依赖 Python 标准库。

```powershell
git clone https://github.com/Bandukids/tokenhub-3d.git
Set-Location tokenhub-3d

$skillRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $env:USERPROFILE '.codex/skills'
}
$target = Join-Path $skillRoot 'tokenhub-3d'
if (Test-Path -LiteralPath $target) {
    throw "技能已存在：$target。更新时请先备份原目录。"
}
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
Copy-Item -LiteralPath 'skills/tokenhub-3d' -Destination $target -Recurse
```

将 TokenHub API Key 配置到运行 Codex 的进程环境变量 `TOKENHUB_API_KEY` 中。开启新对话后，可以这样调用：

> `$tokenhub-3d` 把这张参考图生成 3D 模型。

> `$tokenhub-3d` 用 Tripo P1 生成一个低多边形木箱。

完整路由和模型说明见 [SKILL.md](skills/tokenhub-3d/SKILL.md)。

## 离线预检

```powershell
python skills/tokenhub-3d/references/tripo-3d/scripts/tripo_3d.py generate --model p1 --prompt "一只原创卡通小猫" --dry-run
python skills/tokenhub-3d/references/hunyuan-3d-generator/scripts/hunyuan_3d.py generate --model 3.1 --prompt "一只原创卡通小猫" --dry-run
```

预检不需要密钥，也不提交云端任务。实际调用的额度和计费以 TokenHub 控制台为准。

运行随附的离线测试：

```powershell
Get-ChildItem -LiteralPath 'skills/tokenhub-3d/references' -Directory | ForEach-Object {
    python -B -X utf8 -m unittest discover -s (Join-Path $_.FullName 'scripts') -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw "测试失败：$($_.Name)" }
}
```
