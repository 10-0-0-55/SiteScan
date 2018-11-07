# SiteScan

## 简介

CTF用web扫描工具

## usage

`./SiteScan.py [目标url]`

参数：

* -d 字典目录（建议不要改）
* -m 模式（目前就framework和其他）
* -t 线程数（没啥用）

# feature

* 根据已扫到的文件扫描相应的文件备份（`.bak`、`~`等）
* 扫描web备份文件（`www.zip`）
* 使用HEAD操作
* 自动从Server和X-Powered-By分析数据，给出建议

## TODO

* [ ] 自定义header
* [ ] 加入爬虫功能，动态分析页面连接
* [ ] 更完善的字典
* [x] 自动识别php
* [x] 自动识别nodejs
* [x] 自动识别flask
* [ ] 自动识别java

如果有这个工具扫不出来的题目请提交issue！