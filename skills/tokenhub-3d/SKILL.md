---
name: tokenhub-3d
description: Generate 3D models from text, images, or multiple views using Tencent TokenHub's Tripo 3D or Hunyuan 3D models. Ask which model the user wants before starting a new generation when their choice is unclear. Also use for TokenHub 3D task recovery and supported mesh, material, UV, rigging, animation, and format conversion operations.
---

# TokenHub 3D 生成

## 生成前选择模型

用户要开始新的 3D 生成任务时，先确定这次任务的模型。用户已明确选择时直接沿用。同一个任务的后续回复、轮询或恢复沿用已确认的选择。

用户未选模型时，主动提问，并等待答复后再执行模型命令或提交任务。宿主有可用的选择工具时使用它，也可以直接在对话中提问。例如：“这次想用 **Tripo 3.1**、**Tripo P1**，还是 **腾讯混元 3D**（专业版 3.1 / 3.0、Express）？”

按任务显示适用选项，并简要解释差异。有建议时可以放在首位，仍由用户选择。

| 模型 | 选择依据 | 脚本参数 |
|---|---|---|
| Tripo 3.1 | 高保真。文字、HTTPS 图片或多视图 | `--model 3.1` |
| Tripo P1 | 针对低多边形优化。文字、HTTPS 图片或多视图 | `--model p1` |
| 混元专业版 3.1 | 支持本地参考图、HTTPS 图片、多视图和面数控制 | `--model 3.1` |
| 混元专业版 3.0 | 支持 LowPoly、Sketch，兼顾专业版输入 | `--model 3.0` |
| 混元 Express | 支持文字、单图和白模 | `--model express` |

- 用户只选“Tripo”或“混元”时，对应系列的默认版本是 3.1。若该版本不满足已知需求，向用户说明可用版本并请对方选择。只回复“3.1”且没有明确系列时，追问是 Tripo 还是混元。
- 只有本地参考图时，说明混元可以直接接收文件。用户仍可选 Tripo，但需要提供 TokenHub 可访问的 HTTPS 图片链接。把本地素材上传到存储服务前须有用户授权。
- 用户选择的模型与输入或参数不兼容时，说明冲突并请用户选择怎么调整。保持原选择，直到用户明确改选。

## 调用所选客户端

按选定系列阅读对应指南，并使用指南所在目录下的客户端。两个系列的 `--model 3.1` 对应不同模型，调用时同时确认脚本和参数。

- [Tripo 生成与处理](references/tripo-3d/guide.md)涵盖文字、图片和多视图生成、绑骨检查、绑骨、预设动画、格式转换及任务查询。
- [混元生成](references/hunyuan-3d-generator/guide.md)涵盖专业版、Express、任务查询、下载和显式选择的旧版 AI3D 兼容。
- [混元网格](references/hunyuan-3d-mesh/guide.md)涵盖组件拆分、减面、重拓扑和格式转换。
- [混元材质](references/hunyuan-3d-material/guide.md)涵盖纹理生成和 UV 展开。
- [混元动画](references/hunyuan-3d-animation/guide.md)涵盖绑骨蒙皮、动作模板和文生动作。

用户只要求处理已有资产时，按操作、输入和已明确的偏好路由。如果 Tripo 和混元都支持该操作且用户没选系列，先问用哪一个。恢复已有任务时使用原系列、模型、任务 ID 和适用的地域或接口。缺少关键信息时只询问缺失项。

客户端需要 Python 3.10+。TokenHub 的共同凭据为运行进程中的 `TOKENHUB_API_KEY`。使用绝对路径执行脚本，并为下载指定实际输出目录。

先用对应指南里的 `--dry-run` 预检生成或处理参数。用户要求实际生成或处理且参数齐全时，按所选模型提交一次。仅讨论、修改技能或预检时，停在离线步骤。收到任务 ID 后告知用户。超时、断线或下载失败后查询原任务。提交结果不确定且没有任务 ID 时先检查控制台记录。完成后返回实际下载文件的绝对路径。
