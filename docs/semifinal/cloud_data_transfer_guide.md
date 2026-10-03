# 让云端继续训练：在 Colab 分割训练文件并写回 Drive

2026-10-03后续：用户已回传Colab输出目录，助手成功下载三个分段、逐段核验并还原622965149字节原件，完整SHA-256与官方一致。训练数据已取得，首次三阶段真实建模也已完成。无需再次分割；下面保留复现及备用传输方法。

2026-10-03更新：云端已成功下载官方test.parquet（144652201字节），并核验官方SHA-256、结构、1212个交易日、每日400公司和信息日期。此前测试下载403已解除。尚未训练或生成真实名单。

原件直接下载仍受268435456字节上限限制，但分段路径已解除数据获取阻塞。原始Drive数据及既有共享方式保持不变。

## 推荐：全程在 Google 云端处理

已在项目 Drive 目录创建并通过元数据读回核验：[Claim2Value 云端分割笔记本](https://colab.research.google.com/drive/1aJy2_gPvAbkBhqJIYmwBomMDMJvLac-P)。不需要将训练文件下载到自己的电脑。

1. 打开以上笔记本，选择「运行时 → 全部运行」。
2. 若 Google 提示登录或授权，选择有训练文件访问权的 Google 账号。Colab 登录与 ChatGPT 的 Drive 插件授权独立，这一步需要本人完成。
3. 等待最后输出 `COMPLETE`，将输出的新文件夹链接或名字发给助手。正常结果是三个 part 文件和一个 `parts_manifest.json`；未出现 `COMPLETE` 时不能当作完成。

笔记本通过官方 Drive SDK 以 8 MiB 请求读取原件到 Colab 临时磁盘，核验完整官方 SHA-256，分割成最多 200 MiB 的原始字节段，再写入现有项目目录的新子文件夹。上传后逐段核对服务器字节数和 MD5，全部通过才上传最终 manifest。原文件及其共享权限保持原样；重跑会另建文件夹。

初版上传前，笔记本格式、语法、嵌入代码及12项本地传输检查通过。随后用户回传真实输出目录`1u5jlP6wQlEjxJ_LLNJbb-vDLjV82hHtK`，助手完成逐段及全件官方指纹核验，见`evidence/train_acquisition_20261003.json`。插件仍不能启动Colab；未来需再次运行时，登录和运行由本人完成。

代码与验证见 `scripts/cloud_training_transfer.py`、`scripts/build_cloud_transfer_notebook.py`、`notebooks/Claim2Value_Drive云端分割.ipynb` 和 `evidence/cloud_transfer_review_20261003.json`。Notebook 自带传输源码，运行时不拉取可变 GitHub 源码，也不包含原始数据或凭据。

## 备用：在自己的电脑分段后上传

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
