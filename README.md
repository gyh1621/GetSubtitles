# GetSub



用getsub一步下载字幕。



## 下载



基于python3。

`pip install getsub`



## 使用



下载单视频字幕：

![single file](./pic/single.gif)



下载一个文件夹内的视频文件字幕：

![dir](./pic/dir.gif)



getsub默认为自动下载字幕压缩包并从中选取它认为最合适的字幕，一般是ass格式、双语字幕。
通过添加 `-q` 参数来手动选择下载的字幕压缩包：

![query](./pic/query.gif)



所有可选参数：

```
-h	帮助
-q	查询模式
-o	若视频存在同名字幕，替换已经存在的字幕
-m	保存原始下载字幕压缩包（通常一个字幕压缩包含有多个字幕）
-n	查询模式下显示最大候选字幕数
-d	选择下载器，现在支持subhd和zimuzu
--debug	显示报错详细信息
```

关于下载来源，现在首选是从[zimuzu](http://www.zimuzu.tv/)下载字幕，若搜索结果数太少，会继续搜索[subhd](http://subhd.com)的字幕。

关于下载频率，zimuzu目前没有明显的下载频率限制，拖入一个视频文件夹下载一般不会报错。而subhd有下载频率限制，一般每次只能下载一两个视频的字幕，之后需要滑动验证码验证。

若下载出现unknown error，可能就是下载频率过高，可以等一段时间再试。