# 创世核心

## 简介

基于大语言模型（比如Deepseek，Claude）驱动Blender自动化制作的插件.
使用MCP协议标准化接口, 支持多种大模型提供商, 如DeepSeek, OpenAI, Anthropic, OpenRouter, 硅基流动等.

## 手册 / Manuals

* [中文](./README_CN.md)
* [English](./README.md)

## 特性

* 内置MCP Client实现, 无须借助外部MCP Host
* 支持多个大模型提供商, 如DeepSeek, OpenAI, Anthropic, OpenRouter, 硅基流动等
* 接入Polyhaven在线资产系统(模型、HDRI)
* 支持本地模型库
* 支持历史消息记录控制
* 一键切换模型提供商, 配置自动加载
* 支持sse外部MCP Host连接
* Tools工具模块化, 可扩展
* Client对接模块化, 可扩展

## 安装

### Blender

> 下载并安装 [Blender](https://www.blender.org/download/)(建议版本 4.0+).

### WINDOWS

* 方式1: 使用zip压缩包
  1. 下载压缩包: <https://github.com/AIGODLIKE/GenesisCore.git>
  2. Blender -> 偏好设置 -> 插件: 从zip安装
  3. 或者直接将压缩包拖拽到blender窗口中, 并根据提示完成安装

* 方式2: 手动安装(确保你已经安装了git)
  ```shell
  cd %USERPROFILE%\AppData\Roaming\Blender Foundation\blender\%blender_version%\scripts\addons
  git clone https://github.com/AIGODLIKE/GenesisCore.git
  ```
  * 然后你可以在Blender的插件菜单中看到插件，在节点分类下搜索`GenesisCore`并启用

### Linux

> 如果你是Linux用户，假设你有一些经验：

```bash
cd /home/**YOU**/.config/blender/**BLENDER.VERSION**/scripts/addons
git clone https://github.com/AIGODLIKE/GenesisCore.git
```

* 然后你可以在Blender的插件菜单中看到插件，在节点分类下搜索`GenesisCore`并启用

## 使用

### 基本使用

1. 在3DVeiewport中打开UI面板(N面板), 进入创世核心面板
2. 选择大模型提供商(如DeepSeek, OpenAI, Anthropic等)
3. 获取对应的API Key
4. 在插件设置中输入API Key
5. 获取支持的模型列表
6. 选择模型
7. 选择使用的工具模块(若无自定义资产建议关闭`资产工具模块`)
   1. 按住 shift 点击, 可以选择多个工具模块
8. 输入命令
9. 运行命令

### 高级

1. 历史消息
   1. 当开启历史记录功能时会消耗更多tokens, 但AI能够结合上次的对话做出响应
   2. 当关闭历史记录功能时, token消耗更少, 但每次对话将是独立的(AI会忘记自己说过什么及做过什么)
   3. 使用`清理历史消息`可以在下一次对话时清空历史消息
2. 配置存储
   1. 每次刷新模型列表时会默认保存配置一次
   2. 当调整模型时, 可以点击`保存配置`按钮保存当前配置
   3. 切换大模型服务时, 不同的大模型服务配置独立存储(无须切换模型时重新配置api及选择模型)
3. polyhaven
   1. 需要开启polyhaven资产模块
   2. AI会智能分析任务并决定是否使用polyhaven
   3. polyhaven下载的资产会缓存到`临时目录/polyhaven_{资产类型}` 文件夹中
      1. 临时目录对于于windows用户是`C:\Users\{用户名}\AppData\Local\Temp`
      2. 临时目录对于于linux用户是`/tmp`
      3. 资产类型包括`models`, `hdris`
   4. 已缓存的资产会自动加载, 不会重复下载
4. 外部MCP Host连接, 使用端口45677即可
   ```json
    {
    "mcpServers": {
        "BlenderGenesis": {
        "url": "http://localhost:45677"
        }
    }
    }
   ```
5. 编写自定义工具模块
   1. 参考 `src/tools/` 下的 `common_tools` 等模块
   2. 注意, 编写完成后需要在`src/tools/__init__.py` 中导入, 导入顺序会影响UI显示的工具模块的顺序
6. 编写自定义Client
   1. 参考 `src/client/openai.py` 下的 `MCPClientOpenAI` 模块

## 链接

### 致谢

灵感来自 [BlenderMCP - Blender Model Context Protocol Integration](https://github.com/ahujasid/blender-mcp)

### Our AI website

[AIGODLIKE Community](https://www.aigodlike.com/)
