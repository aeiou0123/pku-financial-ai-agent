# 让云端继续训练：只传训练文件的三个原始字节分段

2026-10-03更新：云端已成功下载官方test.parquet（144652201字节），并核验官方SHA-256、结构、1212个交易日、每日400公司和信息日期。此前测试下载403已解除。尚未训练或生成真实名单。

唯一数据获取阻塞是train.parquet：622965149字节超出当前插件单文件268435456字节上限，413不是重新授权能解决的。原始Drive数据及既有共享方式保持不变。

## 你只需要完成一次小操作

1. 从已共享Drive下载原始train.parquet到自己电脑，例如C:\FEL_MARKET\train.parquet。
2. 解压分段工具包，Python3运行下面命令（仅使用Python标准库，无需安装依赖）：

```powershell
python transfer_training_data.py split --input "C:\FEL_MARKET\train.parquet" --out "C:\FEL_train_parts"
```

命令在仓库根目录执行时，脚本路径改为scripts/transfer_training_data.py。输出目录第一次必须不存在；脚本先核对官方原始训练SHA-256，再分段，不修改源文件。

3. 将C:\FEL_train_parts整个文件夹上传到你们已有私人Drive共享项目目录。里面是train.parquet.part001、part002、part003与parts_manifest.json四个文件；请全部上传。各段最多200MiB，最后一段较小。

收到分段后，云端将逐段下载、核对指纹、按字节拼接，再核对完整官方SHA-256和数据结构，随后运行既定开发/留出/最终预测流程。无需在你本机训练模型，测试文件本轮已经取得。

## 边界

分段只是传输方式：不是改写Parquet、切取训练样本或改变比赛数据。完整拼接结果必须保持官方SHA-256，不能把分段独立当成训练集。原始数据保留私人Drive，公共GitHub仅放工具代码和不含原始数据的校验记录。

工具Review：8项回归通过，包括边界长度、逐字节复原、拒绝覆盖、错误原件、分段篡改和顺序错乱。仅对传输工具作验证，不代表真实训练已完成，也不代替Windows真机运行。
