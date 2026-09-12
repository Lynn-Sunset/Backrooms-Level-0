# Backrooms Godot 4 独立工程

这是从 Three.js 网页版迁移到 Godot 4 的独立工程骨架。

## 运行要求
- Godot 4.2+（推荐 4.4）
- 打开 `project.godot` 后运行主场景 `scenes/Main.tscn`

## 当前包含
- 第一人称玩家控制器（WASD / 鼠标 / 跳跃 / 冲刺 / 体力）
- 出口触发与关卡切换（Area3D）
- 杏仁水拾取恢复体力
- 程序化关卡构建器（基于 JSON 配置生成地面、天花板、墙体碰撞）
- 关卡数据格式：`data/levels/level0.json`、`level1.json`、`level2.json`
- 简单 UI：体力条 + 拾取提示
- 出口触发与关卡切换
- 杏仁水拾取恢复体力
- 可替换材质与光照环境

## 目录
```
BackroomsGodot/
├─ project.godot
├─ scenes/
│  ├─ Main.tscn
│  └─ UI.tscn
├─ scripts/
│  ├─ Main.gd
│  ├─ Player.gd
│  ├─ LevelBuilder.gd
│  ├─ LevelData.gd
│  └─ UI.gd
├─ data/levels/
│  ├─ level0.json
│  ├─ level1.json
│  └─ level2.json
├─ assets/models/   # 待放入 GLB/glTF 模型
└─ docs/
   └─ P3_GODOT_ARCHITECTURE.md
```

## 下一步
- 把 Web 版 GLB 导入 Godot（Godot 原生支持 glTF 2.0）
- 用 StandardMaterial3D/ORMMaterial3D 重做材质
- 实现迷宫生成、出口/拾取、NPC/敌人、交互系统
- 使用 Godot 场景格式替代 JSON 作为最终关卡格式
