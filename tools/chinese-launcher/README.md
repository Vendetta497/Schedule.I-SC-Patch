# Steam 中文字体自动修复启动器

游戏更新或验证完整性可能把 `Schedule I_Data/sharedassets0.assets` 中的中文字体换回英文字体。词库仍能加载，但缺少汉字字形时会显示“口口口”。这个启动器会在 Steam 完成更新后检查字体，必要时先修复，再启动原本的游戏程序。

它只处理字体，不安装或覆盖汉化词库、MelonLoader、游戏模组及存档。新版本新增的英文仍需要补译。请先安装游戏、汉化和需要的模组。

## 已拿到启动器 ZIP：安装到另一台电脑

1. 解压 ZIP，得到 `ScheduleI-ChineseLauncher` 文件夹。将它放在游戏目录以外的固定位置，例如用户的“文档”文件夹。
2. 双击里面的 **`生成Steam启动选项.cmd`**。记事本会打开适配当前电脑路径的一行命令，完整复制这一行。
3. 在 Steam 库右键 **Schedule I → 属性 → 通用 → 启动选项**，粘贴该行，关闭属性窗口即可。
4. 以后直接在 Steam 点 **开始游戏**。Steam 原有的游戏快捷方式也会走同一启动流程。

已经打包的 ZIP 带有独立的 Python 运行库和依赖，不需要另一台电脑再安装 Python。游戏可以安装在不同盘符；启动器根据 Steam 传入的游戏路径定位资源。

**接入后请保留启动器的固定位置。** 移动文件夹后需要重新运行生成工具，并更新 Steam 启动选项。启动选项包含绝对路径，迁移时应在另一台电脑重新生成，不能直接照搬旧电脑那一行。

命令的形状如下，其中路径以生成工具的实际输出为准：

```text
"D:\Tools\ScheduleI-ChineseLauncher\runtime\pythonw.exe" "D:\Tools\ScheduleI-ChineseLauncher\launcher.py" -- %command%
```

保留 `%command%`，它会让 Steam 传入实际游戏程序及原有参数。如果已有游戏参数，可把它们保留在 `%command%` 后面；若已有其他启动器包装命令，应先确认两者如何组合，不要直接叠加两份包装命令。

## 从仓库构建启动器

仓库提供源码和构建脚本，不提交运行库、字体、游戏资产或个人配置。可使用本节自行生成 ZIP；维护者发布预构建包时，也应使用同一脚本。

下载本仓库源码并解压后，在仓库目录的 PowerShell 中运行：

```powershell
.\tools\chinese-launcher\build_launcher.ps1
```

脚本会联网下载并校验 Python 3.13.5 x64 的嵌入式运行库，用固定版本依赖构建独立环境。它默认读取这台电脑已有的微软雅黑或黑体，将所需字体放入启动器。不会安装系统 Python，也不会修改游戏或 Steam 设置。

默认输出：

- “文档”中的 `ScheduleI-ChineseLauncher` 文件夹。
- 同一目录下的 `ScheduleI-ChineseLauncher.zip`，可传到另一台电脑。

输出目录或 ZIP 已存在时，脚本会停止，避免覆盖已经接入 Steam 的启动器。可以指定新位置及自己选择的中文字体：

```powershell
.\tools\chinese-launcher\build_launcher.ps1 `
  -OutputDirectory 'D:\Tools\ScheduleI-ChineseLauncher' `
  -FontPath 'D:\Fonts\ChineseFont.ttf' `
  -ZipPath 'D:\Transfer\ScheduleI-ChineseLauncher.zip'
```

支持 TTF、OTF，以及 TTC 中由 `-FontNumber` 指定的字体（默认第 0 个）。如果本机没有默认中文字体，请传入 `-FontPath`。构建后的 ZIP 包含该字体，分享前请确认所选字体允许相应分发；仓库本身不分发系统字体。

构建完成后，按上一节运行生成工具并接入 Steam。汉化和模组仍按原有安装方法单独安装。

## 更新后会发生什么

- **文件未变化：** 检查资源摘要，直接跳过修复，不重写资产。
- **更新覆盖字体：** 检查新版资源内的 OpenSans / LiberationSans 字体。缺汉字时备份该版本原文件，仅替换字体字节数组。
- **校验通过：** 比较全部资源对象的编号、类型及内容摘要，确认其他对象未变，再替换文件并启动游戏。
- **无法识别的新格式或修复失败：** 停止启动并显示错误。不会把旧版本整份资产覆盖回去。

游戏已经运行时会拒绝修复；请正常退出后再启动。Steam 正在修改资源、存在另一个修复进程或词库/模组发生外部变化时，也会停止本次修复。

无需在 Steam 每次更新后手动重新导入翻译。字体自动修复不表示未来所有游戏版本或所有新增文本都已验证。

## 日志、备份和撤销

启动器目录中：

- `logs/latest.log`：最近一次字体检查、修复结果和游戏启动日志。
- `backups/<原文件摘要>/sharedassets0.original.assets`：每次修复前的新版原始资源。
- `backups/<原文件摘要>/repair-report.json`：对应版本的资源摘要和修复记录。
- `state/`：已验证字体的摘要缓存。

撤销自动启动：在 Steam 游戏属性的 **启动选项** 中删除包装命令，恢复原来的启动选项即可。之后可以移动或删除启动器文件夹。

需要恢复资产时，先退出游戏，核对相应 `repair-report.json` 中的 `installed_sha256` 与当前资源是否一致，再恢复那一次修复的原文件。游戏已经再次更新时，不要恢复其他版本的整份资产；可以让 Steam 验证完整性取得当前版本原文件。

## 验证范围

启动流程已在 Windows x64、Steam beta / IL2CPP `0.4.7f12`、MelonLoader `0.7.3` 和 XUnity.AutoTranslator `5.4.5` 上实测：Steam 传入原游戏程序及 `-beta` 参数，自动修复 13 个界面字体，校验 108,199 个资源对象后启动成功，玩家确认中文显示恢复。

回归检查覆盖更新覆盖字体后再次修复、普通启动不重写资源、独立字体解析与元数据保留、坏字体拒绝写入，以及模组/词库保持原样。其他 Unity 资源结构、字体及运行环境需另行核对；本工具仅支持 Windows x64，不适用于 Steam Deck、Linux 或 macOS。

开发者可用构建出的运行库运行测试。以下命令中的原始资产应来自对应版本的修复前备份，字体使用构建后的 `fonts/chinese.ttf`：

```powershell
& 'D:\Tools\ScheduleI-ChineseLauncher\runtime\python.exe' `
  '.\tools\chinese-launcher\test_launcher.py' `
  --original-asset 'D:\Backups\sharedassets0.original.assets' `
  --font 'D:\Tools\ScheduleI-ChineseLauncher\fonts\chinese.ttf'
```

不传资产和字体参数时，只运行启动参数、错误阻止启动和路径生成的单元检查。资产回归只在临时目录复制文件，不修改正在玩的游戏；没有游戏资产或字体被提交到仓库。
