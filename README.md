# CX 产品文档

[在线阅读产品文档](https://yananliu259-coder.github.io/cx-product-map/)

[全产品预览（模拟）](https://www.figma.com/proto/kLidtlg6DvuSM9u1D6F6rm/CX?page-id=1970%3A85593&node-id=2624-6427&starting-point-node-id=2624%3A6427&content-scaling=responsive&hide-ui=1) · [UI 组件分类目录](https://www.figma.com/design/kLidtlg6DvuSM9u1D6F6rm?node-id=3956-4463)

2026-11-19：产品文档已补充完整播放起点、15 类组件链接和复用说明；功能目录原编号和历史验证状态保持不变。

## 以后怎样更新

1. 修改根目录的 [产品全貌.md](产品全貌.md)：产品说明、用户流程和验收记录。
2. 修改根目录的 [功能目录.csv](功能目录.csv)：功能编号、描述、Figma 链接和验证状态。功能表以 CSV 为准，不必手工同步 Markdown 中旧的表格。
3. 将修改提交到 main 分支。一次修改涉及两个文件时，建议一起提交。
4. 在 [Actions](https://github.com/yananliu259-coder/cx-product-map/actions/workflows/publish.yml) 看到绿色成功标志后，刷新原分享链接。

网页会自动重建并发布，分享地址保持不变。不需要手动生成或上传 HTML。只有电脑里改了但没有提交到 GitHub 的文件，不会触发线上更新。

需要更新图表时，一并提交对应 SVG 文件。构建会检查重复编号、缺少列、图表文件和文内跳转；失败时不部署，线上继续保留上一版。

## 自动生成的范围

自动生成只整理你提交的文档和 CSV，不重新分析 CX 原始代码，不改变已验证/未验证状态，不会自动更新 Figma 画布。Figma 原型为模拟演示，仍需要对应查看权限。

build_site.py 与 site_template.html 负责生成网页，.github/workflows/publish.yml 负责自动发布。根目录 index.html 是第一次手动发布的历史快照；正式网站使用工作流生成的 _site/index.html，不必维护该快照。

[查看文档更新历史](https://github.com/yananliu259-coder/cx-product-map/commits/main/)
