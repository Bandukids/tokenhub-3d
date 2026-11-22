# Tripo-3D（腾讯 TokenHub）

使用附带的 Python 标准库客户端 `scripts/tripo_3d.py`，无需额外安装依赖。通过 TokenHub 的 `POST /v1/api/3d/submit` 提交任务，用 `POST /v1/api/3d/query` 查询状态。

## 模型一览

| 模型 ID | 用途 | 输入 |
|---|---|---|
| `tripo-3d-3.1` | 高保真 3D 生成，最高约 200 万面，适合 3D 打印、核心资产 | 文本（≤1024 字）、图片、多视图 |
| `tripo-3d-p1` | 低多边形优化的 3D 生成，适合游戏和风格化资产 | 文本、图片、多视图 |
| `tripo-3d-rigging` | 为任意 3D 模型自动添加骨骼 | GLB / GLTF / FBX / OBJ / STL，≤150MB |
| `tripo-3d-rigging-check` | 检查模型能否绑骨，并返回推荐骨骼类型 | GLB，≤150MB |
| `tripo-3d-animation` | 把预设动画应用到已绑骨的模型 | 已绑骨模型的任务 ID |
| `tripo-3d-format` | 模型格式转换，可选网格处理、贴图烘焙、导出设置 | GLB / GLTF / FBX / OBJ / STL，≤150MB |

额度和计费以 TokenHub 控制台为准。

## 快速上手

客户端从进程环境读取 `TOKENHUB_API_KEY`。以下命令从本指南所在目录展示，实际调用使用绝对路径。

```powershell
python scripts/tripo_3d.py generate --model 3.1 --prompt "一只可爱的小猫" --dry-run
python scripts/tripo_3d.py generate --model 3.1 --prompt "一只可爱的小猫" --wait --output-dir out
```

## 常用操作

**文本生成 3D**（默认 3.1；低多边形用 `--model p1`）：

```powershell
python skills/tripo-3d/scripts/tripo_3d.py generate --model p1 --prompt "低多边形木箱" --wait --output-dir out
```

**图片生成 3D**：图片必须是公开的 https 链接（JPEG 或 PNG，256×256 以上，≤20MB）。

```powershell
python skills/tripo-3d/scripts/tripo_3d.py generate --image https://example.com/cat.jpg --wait --output-dir out
```

**多视图生成 3D**：视角可选 `front`、`left`、`back`、`right`，每个都是公开 https 链接。

```powershell
python skills/tripo-3d/scripts/tripo_3d.py generate --views front=https://e.com/f.jpg left=https://e.com/l.jpg back=https://e.com/b.jpg right=https://e.com/r.jpg --wait
```

**检查能否绑骨**（只允许 GLB）：

```powershell
python skills/tripo-3d/scripts/tripo_3d.py rig-check --input https://example.com/char.glb --wait
```

**绑骨**：

```powershell
python skills/tripo-3d/scripts/tripo_3d.py rig --input https://example.com/char.fbx --wait --output-dir out
```

**预设动画**：用绑骨任务的 ID。`--preset` 的默认值是 `walk`，控制台示例只给出了这一个预设名，其他预设名需要以控制台文档为准。

```powershell
python skills/tripo-3d/scripts/tripo_3d.py animate --rigged-task-id 1234567890 --preset walk --wait --output-dir out
```

**格式转换**（输出格式：GLTF、GLB、FBX、OBJ、STL）：

```powershell
python skills/tripo-3d/scripts/tripo_3d.py format --input https://example.com/model.fbx --format GLB --wait --output-dir out
```

**查询已有任务**（任务超时或断线后使用，不要重新提交）：

```powershell
python skills/tripo-3d/scripts/tripo_3d.py query --model rigging --id 1234567890
```

`query` 返回任务响应。任务完成后从响应提取结果链接，下载到用户的输出目录。它会直接联网，离线校验只用于生成和处理命令。

`--model` 可用的值：`3.1`、`p1`、`rigging`、`rigging-check`、`animation`、`format`。

## 工作流建议

1. 先用 `generate` 得到 3D 模型，或准备一个已有的 GLB/FBX 模型。
2. 用 `rig-check` 判断能否绑骨，再用 `rig` 绑骨。
3. 绑骨完成后，用绑骨任务的 ID 调用 `animate` 添加动画。
4. 需要其他格式时用 `format` 转换。

## 注意事项

- **密钥**：只从 `TOKENHUB_API_KEY` 环境变量读取，不会打印，也不接受命令行参数。不要把 Key 粘贴到聊天里或提交到仓库。
- **Dry-run**：`--dry-run` 只打印将要发送的请求，不联网、不消耗积分。正式提交前先用它检查参数。
- **格式大小写**：`format` 的 `--format` 会自动转为大写，因为服务端只接受大写。
- **输入链接**：所有输入都必须是公开可访问的 https 链接。本地文件需要先上传到你自己的公开存储。
- **断线恢复**：`--wait` 超时后，客户端会打印任务 ID 和恢复命令。用 `query` 查询，不要重新提交。
- **返回结构**：TokenHub 页面只给出了请求示例，没有写明返回字段。客户端会递归查找 `url` 或 `download_url` 字段来下载结果。第一次真实调用时请检查输出，如果字段不同，需要调整 `_download_urls`。

更多接口细节见 [references/api.md](references/api.md)。
