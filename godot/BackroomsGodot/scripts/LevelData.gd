class_name LevelData
extends RefCounted

## 关卡数据加载器：从 res://data/levels/{id}.json 读取 JSON 配置。
static func load_level(id: String) -> Dictionary:
	var path := "res://data/levels/%s.json" % id
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("无法加载关卡: " + path)
		return {}
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	if err != OK:
		push_error("关卡 JSON 解析失败: %s, error: %s" % [path, json.get_error_message()])
		return {}
	return json.data
