# TokenHub Tripo-3D API 参考

数据来源：腾讯云 TokenHub 模型广场中各模型详情页的「调用指南」（区域 `regionId=1`，需要登录控制台查看）。

## 通用

- 基础地址：`https://tokenhub.tencentmaas.com`
- 鉴权：`Authorization: Bearer <API_KEY>`，`Content-Type: application/json`
- 提交：`POST /v1/api/3d/submit`，请求体含 `model` 字段，其余字段因模型而异
- 查询：`POST /v1/api/3d/query`，请求体为 `{"model": "...", "id": "<任务ID>"}`
- 调用协议：OpenAPI；默认并发数 1；后付费已开启；无免费体验包

## 各模型请求体

### tripo-3d-3.1 / tripo-3d-p1

文本生成：

```json
{"model": "tripo-3d-3.1", "prompt": "一只可爱的小猫"}
```

图片生成（`input` 为图片 URL）：

```json
{"model": "tripo-3d-3.1", "input": "https://example.com/test.jpg"}
```

多视图生成（`inputs` 为对象数组，每个对象一个视角）：

```json
{"model": "tripo-3d-3.1", "inputs": [
  {"front": "https://example.com/test.jpg"},
  {"left": "https://example.com/test_left.jpg"},
  {"back": "https://example.com/test_back.jpg"},
  {"right": "https://example.com/test_right.jpg"}
]}
```

输入限制：文本小于 1024 字符；图片分辨率大于 256×256，支持 JPEG、PNG，最大 20MB。

### tripo-3d-rigging

```json
{"model": "tripo-3d-rigging", "input": "https://example.com/test.glb"}
```

输入：GLB、GLTF、FBX、OBJ、STL，最大 150MB。

### tripo-3d-rigging-check

```json
{"model": "tripo-3d-rigging-check", "input": "https://example.com/test.glb"}
```

输入：仅 GLB，最大 150MB。用途：检查模型能否绑骨，并返回推荐骨骼类型。积分为 0。

### tripo-3d-animation

```json
{"model": "tripo-3d-animation", "input": "<已绑骨模型的任务ID>", "animation": "preset:walk"}
```

输入是已绑骨模型的 task_id，不是 URL。控制台示例只给出 `preset:walk`，其他预设名未在页面中列出。

### tripo-3d-format

```json
{"model": "tripo-3d-format", "format": "GLTF", "input": "https://example.com/test.fbx"}
```

输入：GLB、GLTF、FBX、OBJ、STL，最大 150MB。支持可选网格处理、贴图烘焙和导出设置；页面按分辨率区分「基础版」和「高级版」计价，但没有列出对应的请求字段。

## 查询示例

```json
{"model": "tripo-3d-rigging", "id": "1471412548539613666"}
```

## 已知未确认的内容

- 提交和查询的**返回结构**（任务 ID 字段名、状态字段、结果下载链接字段）页面没有给出，客户端按通用规则解析（`id`/`task_id`/`job_id`，状态字段 `status`，下载链接 `url`/`download_url`）。首次真实调用时需要核对。
- 动画预设列表、格式转换的高级选项（烘焙、导出设置）的字段名未公开。
- 多视图的视角个数上限和顺序要求未说明。
- 控制台显示的积分范围是否与实际计费一致，以控制台账单为准。
