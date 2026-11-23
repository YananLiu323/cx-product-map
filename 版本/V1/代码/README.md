# 代码与资源

## 本次收录范围

- `frontend-ref-main/cx-ref/`：用户指定的 CX 参考构建资源。
- 同仓库根目录 `package.json`：产品与依赖声明，供来源核对。
- 原有文件中的 `build_site.py`、`site_template.html`、测试、依赖清单和发布工作流：产品报告的构建工具。

只收录 CX，不混入 `gb-ref`、`Jan-ref`。649 MiB 左右的参考资源不直接加入 Git 历史，放入阶段资料包的 `代码/cx-ref/`；每次打包重新计算大小与校验值。

## 来源与限制

原文档记录的参考仓库：[DreamSoul-AI/frontend-ref 的 cx-ref](https://github.com/DreamSoul-AI/frontend-ref/tree/main/cx-ref)。此地址仍是可变化的分支入口，本次没有凭它宣称锁定远端提交；资料包以本地捕获的文件与 SHA-256 清单为准。

这些文件含前端与桌面构建产物，不是完整开发源码。`package.json` 中还引用缺少的脚本、工作区包和服务端依赖，不能据此声称可以完整重新编译原产品或连接后台。

此前聊天流程预览、模拟服务和截图属于历史试验材料，不当作当前全产品 Figma 的运行源码。当前 Figma 设计的完整恢复文件应是 `.fig`，缺少它不能用历史预览工程或图层 JSON 替代。
