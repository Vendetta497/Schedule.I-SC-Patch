# Schedule-I-Simplified-Chinese-Patch
Schedule I简中汉化补丁

[安装教程视频](https://www.bilibili.com/video/BV1WL22BQE33)



## 汉化补丁的安装
[下载release](https://github.com/Vendetta497/Schedule.I-SC-Patch/releases)的Schedule.I_SC.7z

**解压缩汉化补丁到游戏根目录，安装即完成**

### 汉化词库源码

词库沿用发布包的目录和文件名，位于 `AutoTranslator/Translation/zh-CN/Text/`：

- `中文.txt`：普通文本的简体中文译文。
- `SChinese2.txt`：动态文本的 `r:` 正则规则和 `sr:` 递归拆分规则。
- `Beta-0.4.7.txt`：在 beta `0.4.7f11` 的实际游戏资源中确认的界面、任务、对白、道具名称及描述漏译，以及特殊顾客到访提示。
- `Mods-Drivers-TimeStuff.txt`：Drivers `2.13.38` 的手机界面及司机人数动态标题，并提供 TimeStuffMod 的固定按钮词条。

已安装原汉化补丁的玩家，退出游戏后，将本仓库的 `AutoTranslator` 文件夹合并复制到游戏根目录，复制全部词库文件即可（保留原有两份文件，同时加入补充文件）。打包新 Release 时也包含这些词库文件。动态文本的递归处理建议将 `AutoTranslator/Config.ini` 中 `[Behaviour]` 下的 `MaxTextParserRecursion` 设置为 `3`。

本次词库覆盖 `v0.4` 发布包的正式版 `v0.4.6f13`，并补充 Steam **beta 分支（Windows x64 / IL2CPP）的 `v0.4.7f11`**。两份 0.4.6 词库保持原样，beta 与模组补充独立成文件，不替换旧键值或改写旧规则。保留原词库署名启铭star、夜行者和原补丁作者署名。翻译及复核使用 AI 辅助，并对照实际资源和已有术语。仍需要持续的实机反馈；尚未确定上下文的动态片段和图片内英文不作完整覆盖保证。

游戏升级后，应在**该版本原始 `sharedassets0.assets`** 上处理中文字体；不要把 0.4.6 的整份资产文件覆盖到 beta。词库补充不包含游戏二进制、字体资产或模组 DLL，也不改变 Drivers / TimeStuffMod 的行为、快捷键或定制逻辑。TimeStuffMod 的部分按钮使用 IMGUI，XUnity.AutoTranslator 5.4.5 在 IL2CPP 下不支持其钩子；存在词条不代表这些按钮能在该环境自动显示中文。

### 词库检查

使用 PowerShell 7，在仓库目录运行：

```powershell
pwsh -NoProfile -File ./validate_translations.ps1
```

脚本首次运行会下载并校验固定提交的 XUnity.AutoTranslator 5.4.5 原版解析和替换代码，随后检查词库行、正则捕获组和 `translation-regression.json` 中的用例。下载内容缓存在临时目录；可用 `-SourceCachePath` 指定位置，或用 `-ReportPath` 保存检查结果。检查涵盖静态词条、动态金额、数量、收据、任务地点和生成的变量模板；它不模拟 Unity 界面钩子、数字模板化或在线翻译端点。原有配置已在正式版游戏的菜单及存档载入画面检查过。本次 beta 本机启动日志确认 MelonLoader 0.7.3、Drivers 2.13.38、TimeStuffMod 1.1.3 与 XUnity.AutoTranslator 5.4.5 加载成功；词库回归不等于逐场景显示验证。

本次独立补充 212 条静态词条与 3 条动态规则，共 215 条；全部 11,200 行通过原版解析器检查，182 个回归用例通过（包含原有 170 个用例）。两份 0.4.6 词库与补充前提交逐字节相同。来源对照 Unity 场景、资源、IL2CPP 字符串以及模组 UI 方法，不把内部标识、日志或未经确认的动态片段作为译文。部分漏译可能也存在于旧版本，因此不声称每条均为 beta 独有新增文本。


## 常见错误问题解决方案
 demo不能用，需要正式版，steamdeck请自行加命令行，盗版不能保证补丁有效
 
### 字体问题
汉化出现**口口口的，粉屏，闪退的（均为缺字体错误）**， 请先验证游戏完整性再下载字体替换工具替换字体（**该工具仅仅是解决字体问题的，不能解决melonloader问题**）

如果汉化失败（口口口的，粉屏，闪退的（均为缺字体））则还原备份使用原sharedassets0.assets文件，再运行字体替换工具Font.exe,确保字体替换成功（出现“字体替换完成 操作成功完成”提示），检查schedule 1_data文件夹的sharedassets0.assets文件是否替换成功（看文件大小和文件日期是否改变）

这个字体替换工具会备份游戏原文件里的sharedassets0.asset文件（生成.bak文件），如果出问题要还原的话把替换好的sharedassets0.asset文件删掉，再把备份文件的.bak后缀删掉就可以

如果字体替换失败等问题，删掉font_SC.exe生成的sharedassets0.assets（也有可能发生错误导致没有），将font_SC.exe生成的sharedassets0.assets.bak文件的.bak后缀去掉，再次运行Font_SC.exe

### Melonloader/Cpp2IL报错
 打了补丁仍然是英文的，多半是插件问题，进游戏按Alt+0能不能调出插件UI，（数字0，不是字母O）
 建议去[Melonloader](https://github.com/LavaGang/MelonLoader)提个Issue
 
1.如果显示 Downloading the .NET Runtime installer...卡住了或者失败，防火墙/网络的问题，去下载[Net6.0](https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/6.0.36/windowsdesktop-runtime-6.0.36-win-x64.exe)

2.Melonloader其他报错的，Mod无法加载的就直接进入游戏但是没有汉化的，或者直接Cpp2IL报错的，是Cpp2IL.exe的问题（文件路径：Schedule I\MelonLoader\Dependencies\Il2CppAssemblyGenerator\Cpp2IL\Cpp2IL.exe），打上网盘里的schedule I.7z文件，
如果还是没用，目前已知的可行的办法：

1）卸载重装Net6.0

2）找个玩这个游戏而且打补丁有效的人 让其把游戏文件（除了schedule 1 data的文件）给自己

3)到Github下载[最新版Melonloader](https://github.com/LavaGang/MelonLoader/releases/download/v0.7.1/MelonLoader.x64.zip)安装


3..Mod显示加载成功但是仍然报错的，多半是因为下的是盗版或者demo，换成正式版

## 说明
目前的游戏更新并不影响旧汉化补丁的使用（补丁更新就是更新汉化文本和资产字体文件），仅仅是影响游戏Unity资产文件的字体导致缺字，所以游戏更新Melonloader报错并不是补丁没更新的原因是其他原因导致的（特别是以前没安装过补丁的）

Schedule 1_data文件夹的sharedassets0.assets文件是Unity游戏资产文件，包含游戏字体文件，但是英文字体和中文字体（包括简中和繁中）是不一样的，xuntiy-translator插件若要翻译英文成中文就需要中文字体文件，否则就会字体缺失出现仍然是英文或者口口口的情况，这也就是为什么**每次游戏更新旧汉化补丁都会失效**，游戏更新也更新了sharedassets0.assets文件，又变回英文字体了，这个字体替换程序就能把资产文件的英文字体替换成中文字体了，并且简繁中都适用！

替换资产字体文件也可以用这个[工具](https://github.com/HanFengRuYue/XUnityToolkit)


## 参考
繁中补丁原帖：https://forum.gamer.com.tw/C.php?page=1&bsn=82540&snA=6

繁中补丁链接：https://github.com/XoF-eLtTiL/Tang-Family-Server/releases/tag/SI

链接2：https://thunderstore.io/c/schedule-i/p/GrandDuchyOfGames/GDG_ScheduleI_Traditional_Chinese_Translation

翻译插件：https://github.com/bbepis/XUnity.AutoTranslator

字体替换提出方案：https://forum.gamer.com.tw/Co.php?bsn=82540&sn=35

繁中字体替换工具及源代码：https://drive.google.com/drive/folders/1YUBnhHULnlY8l48rvEkuJR_zOGbtH9WT
