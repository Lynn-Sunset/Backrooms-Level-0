# P3: Godot 4 独立工程架构设计

## 目标
把当前 Three.js 网页版完整迁移为 Godot 4 独立游戏工程，保留现有 Level 0/1/2 内容并提升画面、物理、编辑体验。

## 阶段拆分

### Phase 3.1 基础工程（已完成骨架）
- [x] Godot 4 工程创建
- [x] 第一人称控制器：移动/跳跃/冲刺/体力/鼠标视角
- [x] 关卡 JSON 加载
- [x] 程序化生成地面/墙体/天花板碰撞
- [x] 基础 UI（体力条）

### Phase 3.2 关卡内容迁移
- 将 Web 版 GLB 模型放入 `assets/models/`
  - `pillar.glb`
  - `light_panel.glb`
  - `exit_door.glb`
  - `door_industrial.glb`
  - `almond_water.glb`
  - `pavilion.glb`
- 用 Godot 场景（`.tscn`）替换 JSON 中的程序化物件：
  - 仓库：货架、叉车、托盘、月台门
  - 园林：亭子、假山、池塘、竹林、灯笼
- 材质迁移到 `StandardMaterial3D` / `ORMMaterial3D`，启用实时阴影、SSAO、GI。

### Phase 3.3 游戏系统
- 关卡切换：`LevelManager.gd`
- 出口触发与胜利/失败
- 杏仁水拾取、体力计时
- 排行榜（本地 / 云端）
- 音效与背景音乐
- 交互提示（E 键拾取、开门）

### Phase 3.4 编辑器与数据格式
- 使用 Godot 内置编辑器搭建关卡
- 定义自定义 Resource：
  - `LevelData`（Resource 类，替代 JSON）
  - `PropSpawner`
  - `ExitTrigger`
- 场景预览 / 调试工具 / 性能监控

## 数据格式建议

最终不直接使用 JSON 作运行格式，而是：
1. 在编辑器里用 `.tscn` 搭建大场景
2. 程序化部分（迷宫、随机货架、竹林）用 GDScript 生成
3. 数据层保留 JSON 作为“配置”：尺寸、体力、拾取点、出口等

## 性能策略
- 静态网格使用 Godot `MultiMeshInstance3D`（等同 InstancedMesh）
- 动态物体使用 `Rid` / `PhysicsServer3D` 批量处理
- 光照烘焙：`LightmapGI` + 静态全局光照
- 使用 `MeshOptimizer` / Blender 减面后导入
- LOD：Godot `GeometryInstance3D` LOD / `ImporterMesh` LOD

## 后续任务
- [ ] 将 GLB 导入并绑定碰撞
- [ ] 完成三个关卡完整搭建
- [ ] 添加游戏循环与 UI
- [ ] 发布到 Windows / Linux / macOS / Web
