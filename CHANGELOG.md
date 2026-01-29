# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-28

### Added
- ✨ 新增语音播报工具：支持中英混搭文字转语音
- 🔧 实现了文本长度判断逻辑：≤50字自动发声，>50字不发声
- 🎯 智能体自动语音播报：短文本回复自动触发语音播报
- 📝 完善了工具定义和系统提示词

### Changed
- 🔄 优化了工具注册表：支持异步工具执行
- 🎨 更新了 README.md：添加语音工具相关信息

### Fixed
- 🐛 修复了语音工具参数名不一致问题
- 🐛 解决了工具调用后回复不触发语音播报的问题

## [0.1.0] - 2026-01-27

### Added
- 🚀 项目初始化：基于 Ollama 的本地大模型智能体
- 🔧 工具系统：支持基础工具（时间、计算、问候）
- 💬 交互式对话：支持多轮对话、历史记录管理
- ⚙️ 配置系统：通过配置文件调整模型参数

### Changed
- 📝 完善了项目文档

[Unreleased]: https://github.com/yourusername/yourproject/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/yourproject/releases/tag/v1.0.0
[0.1.0]: https://github.com/yourusername/yourproject/releases/tag/v0.1.0
