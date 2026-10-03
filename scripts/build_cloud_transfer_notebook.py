"""Create a self-contained Colab handoff; never invent execution output."""
import argparse
import hashlib
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    transfer = (ROOT / "scripts/transfer_training_data.py").read_text(encoding="utf-8")
    cloud = (ROOT / "scripts/cloud_training_transfer.py").read_text(encoding="utf-8")
    assert "'''" not in transfer and "'''" not in cloud
    notebook = nbformat.v4.new_notebook()
    notebook.metadata.update({"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}, "colab": {"name": output.name},
        "claim2value_validation": {"google_colab_execution": "NOT_RUN_REQUIRES_USER_GOOGLE_AUTH",
            "local_contract_tests": "12 passed", "no_raw_data_embedded": True,
            "code_modules_sha256": {"byte_transfer": hashlib.sha256(transfer.encode()).hexdigest(),
                                    "cloud_transfer": hashlib.sha256(cloud.encode()).hexdigest()}}})
    notebook.cells = [
        nbformat.v4.new_markdown_cell("""# Claim2Value：在云端分割训练文件并写回 Drive

在 **Google Colab** 中选择「运行时 → 全部运行」。所有数据读取、分割与上传都发生在 Google 云端，不需要把 623 MB 文件下载到你的电脑。

若 Google 提示登录/授权，请本人选择有赛事训练文件访问权的 Google 账号。Colab 的凭据与 ChatGPT 的 Drive 插件连接独立；我不能从插件取出或复用账号令牌。

此笔记本已做格式、语法和本地模拟接口验证，**尚未在你的 Colab 账号中执行**。成功标志是最后输出 `COMPLETE`，以及新文件夹内三个 part 文件和一个 manifest。
"""),
        nbformat.v4.new_markdown_cell("""## 1. 连接自己的 Google 账号

使用 Google 官方 Colab 认证与 Drive API。凭据只保留在当前 Colab 运行环境中，不写入 notebook 输出。依赖通常已安装；缺失时在这个云端运行环境安装 SDK。
"""),
        nbformat.v4.new_code_cell("""import sys, subprocess
try:
    import googleapiclient
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-api-python-client'], check=True)

from google.colab import auth
auth.authenticate_user()
import google.auth
from googleapiclient.discovery import build
credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
print('Google 账号已连接；下一步只处理指定训练文件和项目输出目录。')
"""),
        nbformat.v4.new_markdown_cell("""## 2. 加载已检查的传输代码

代码完整嵌入本 notebook，运行时不从 GitHub 拉取可变源码。官方训练文件 ID 和输出父目录已填好；原始文件内容及共享权限保持原样。
"""),
        nbformat.v4.new_code_cell("import types\nbyte_transfer = types.ModuleType('claim2value_byte_transfer')\n"
            + "BYTE_SOURCE = r'''" + transfer + "'''\nexec(compile(BYTE_SOURCE, 'byte_transfer.py', 'exec'), byte_transfer.__dict__)\n"
            + "cloud_transfer = types.ModuleType('claim2value_cloud_transfer')\n"
            + "CLOUD_SOURCE = r'''" + cloud + "'''\nexec(compile(CLOUD_SOURCE, 'cloud_transfer.py', 'exec'), cloud_transfer.__dict__)\n"
            + "print('原始字节传输工具已加载。')\n"),
        nbformat.v4.new_markdown_cell("""## 3. 在云端完成传输

先按 8 MiB 请求将原始数据读入 Colab 临时磁盘，核对官方 SHA-256，再按最多 200 MiB 分为三段，并在已有项目目录下创建新子文件夹。每段上传后检查服务器字节数与 MD5；全部成功才上传最终 manifest。

中断或错误不会标为完成，已生成的新文件夹保留现场。重复执行会另建文件夹；原文件不会被覆盖。这里不运行建模、不读取测试收益。
"""),
        nbformat.v4.new_code_cell("result = cloud_transfer.run_transfer(service, split_function=byte_transfer.split)\n"
                                 "assert result['status'] == 'COMPLETE'\n"),
        nbformat.v4.new_markdown_cell("""## 4. 成功后

看到 `COMPLETE` 后，把输出文件夹链接或名字发给助手。助手可通过已有 Drive 连接下载三段、拼回原文件，再核对完整官方指纹并执行既定技术题流程。若报错，把错误文字回传；`COMPLETE` 尚未出现的目录不能当成完整传输。

Google 官方参考：

- [Drive 下载与按字节读取](https://developers.google.com/workspace/drive/api/guides/manage-downloads)
- [Colab 外部数据与认证](https://colab.research.google.com/notebooks/io.ipynb)
"""),
    ]
    nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            compile(cell.source, "notebook-cell", "exec")
            assert cell.execution_count is None and not cell.outputs
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.out))
