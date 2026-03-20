import toml

# 读取并解析
data = toml.load("pyproject.toml")

# 提取并保存
with open("requirements.txt", "w") as f:
    f.write("\n".join(data["project"]["dependencies"]))
