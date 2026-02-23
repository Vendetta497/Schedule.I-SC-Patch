# Schedule-I-Simplified-Chinese-Patch
Schedule I简中汉化补丁

[安装教程视频](https://www.bilibili.com/video/BV1WL22BQE33)



## 汉化补丁的安装
[下载release](https://github.com/Vendetta497/Schedule.I-SC-Patch/releases)的Schedule.I_SC.7z

**解压缩汉化补丁到游戏根目录，安装即完成**


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
