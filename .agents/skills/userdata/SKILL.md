---
name: userdata
description: 定义 <userdata>（仓库根的用户数据目录）：lora 库、episodes、workflows、cache、app_config.yaml 都放在这里。其他 skill 提到 <userdata> 时以本文为准。
---

用户自己产生的数据全在 `<userdata>` 里 —— 默认是**仓库根下的 `./userdata`**，被本仓库 git 忽略
（用户可在里面自己 `git init`，本仓库不管它怎么备份）。

不要假设它就在仓库根：用户可在仓库根放 `userdata_pointer`（一行绝对路径）把它改到别处。想知道实际取值：

```bash
python entropy/cli/locate_userdata.py
```

stdout 只有一行：`<userdata>` 的绝对路径；stderr 是判断过程与各子路径（含 exists/missing）。
**需要读写用户的文件时就跑它、用它的输出**，不要自己拼路径。
仓库自带的东西（`library/artists.md`、`entropy/conf/tag_datasets/danbooru.txt` 等）不在 userdata 里。
