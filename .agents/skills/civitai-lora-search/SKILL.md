---
name: civitai-lora-search
description: 搜索civitai的lora。如果用户不显式要求，请勿调用。
--- 

## 前置确认
显式向用户确认（如果用户未主动说明）
- 梯子端口。对应 HTTPS_PROXY="http://localhost:xxxx"
- 模型架构
- 是否下载
- 其他必要信息 例如关键词或画师名称（如果用户提供的不充分，请向用户确认）


## 发现搜索关键词
参考 skill:artist-name-search

lora的作者可能会以pixiv昵称（日文名），或者danbooru tag发布。
你需要正向或者反向地查询它的昵称或者danbooru tag，以达到不漏掉资源的目的.


## 搜全经验（踩坑总结）

### 1. 画师 lora 的模型名常用 pixiv 原名，先用 danbooru 查原名再搜
civitai 上画师 lora 的模型名多用画师的 **pixiv 原名**（日/中/韩文），例如「画風 館田ダン style」。如果你用罗马字 `kanda_dan` 搜，匹配不上模型名里的「館田ダン」，于是 0 结果——不是没有，是搜法不对。

正确流程：先查 danbooru 拿画师的 other_names（pixiv 原名），再用原名搜。

```bash
curl -g "https://danbooru.donmai.us/artists.json?search[name]=arata_(xin)"
# -> other_names: ["y3010607", "あらた"]   # 拿去搜 civitai
```

实例（真实踩坑）：

| danbooru tag | 原名（拿去搜） | 罗马字（搜不到） |
|---|---|---|
| arata_(xin) | あらた | arata |
| kanda_done | 館田ダン | kanda_dan |
| tianliang_duohe_fangdongye | 天凉多喝防冻液 | tianliang |
| sora_72-iro | そらなにいろ | sora |

### 2. 空格和下划线是不同的写法，搜不到彼此
civitai 按模型名字面匹配：模型名是 `torino_aqua`（下划线连写）时，你搜 `torino aqua`（带空格）匹配不上。同一画师的不同模型可能用不同写法，所以多写法都试一遍：`torino aqua` / `torino_aqua` / `torino`。

### 3. 0 结果要存疑
civitai 搜索服务会临时 overloaded，CLI 显示 "0 results" 无法区分"真没有"和"抽风"。重要画师的 0 结果要重试或换词确认。



## 搜索

civitai models search --type LORA --sort "Most Downloaded" --nsfw

不得剔除nsfw的lora。

Search commands paginate with --limit and either --page (shallow) or --cursor (deep paging — copy metadata.nextCursor from a previous response). See Pagination.

Pagination
Most list endpoints (/models, /images, /creators, /tags) support both page-based and cursor-based pagination. Choose cursor-based for anything beyond a handful of pages.






## 输出格式
search-xxx-date-time.md 这一类的。优先放到 .cache/lora_search 目录

- id
- version id
- 名称
- 对应version的downloadUrl (不要主动download) (可能有多个适合不同模型架构的lora version)
- 触发词
- 推荐权重
- 兼容性说明
- 其他你认为重要的信息
- 本地文件名（仅当用户主动要求download才下载）
  - 优先下载到当前仓库或目录下的 .cache/lora_search 目录
  - 命名: 模型架构_画师_合理后缀
  - 例如 noob_xxx_1
  - 合理后缀: 多个模型想不出合理后缀，可以 _1 _2 _3这样


## 筛选标准

数量: 按合理顺序列出给用户，数量尽量多，将决定权交给用户。但给用户的不能太多，每1名画师至多3个lora。

如果用户未说明想要什么模型架构的lora，则拒绝得出结论。

### noobai
```
case
  when (models get 中的某个version信息包含 noobai 或 wai-illustrious) then (适合noobai)
  when (models get 中的某个version信息包含 il 或 illustrious) then (大概率适合noobai) -- 具体得看--json里面的description
  when (models get 中的是sdxl或xl) then (小概率适合noobai) --有人乱标，以json的description为准
  when (models get 中的是sd1 pony sd1.5 anima flux anima) then (不适合noobai) -- 这些模型和noobai架构差别很大
  when (json中的description中明确说明是基于 noobai 或 wai-illustrious) then (适合noobai)
  when (json中的description中明确说明是基于 illustrious 0.1) then (适合noobai)
  when (json中的description中明确说明是基于 illustrious 1.0 2.0) then (保留，但告诉用户存在不兼容风险)
  else 排除
end
```

另外注意，model versions里面如果写了v1.0 illustrious，不是说是基于illustrious1.0训练的，而是这个lora作者本身的版本是v1.0

想要看看这个model是不是基于illustrious x.x训练的，只能看description中作者是否明确说明。

背景知识: illustrious 0.1版本是基础版本，noobai是基于它训练的，chenkin-noob是基于noobai训练的。人们训练的时候，noob内部的lora绝大部分情况下是通用的。而为了纯净或者收敛，人们可能会在illustrious 0.1中训练模型，也可以完美给noob使用。


### 其他模型
规则：待总结。请提示用户，告诉不是很精确。



## 查看详情和筛选

获取简要基本信息

civitai models get 2706335
```
anon betanonbeet style 【anima&il】 (id 2706335)
  type:      LoCon
  creator:   NXMZ
  nsfw:      false
  downloads: 796   thumbsUp: 96   comments: 0
  tags:      style
  versions (2):
    3039597  anima v1.0  Anima
    3039595  il v1.0     Illustrious
```


获取完整信息. 永远将json放到当前项目或仓库目录的.cache/.civitai-cache/*.json里面，避免多次访问网络浪费API。

*.json的文件名需要自己决定。没必要的使用model_id.json，有重复风险的的进行随机化。

civitai models get 2706335 --json > 1.json


```json
{
  "id": 2706335,
  "name": "...",
  "description": "<p>...",
  "modelVersions": [
    {
      "id": 1762339,
      "index": 0,
      "name": "v1.0",
      "baseModel": "Illustrious",
      "baseModelType": "Standard",
      "createdAt": "2025-05-08T12:52:03.292Z",
      "publishedAt": "2025-05-08T13:00:22.002Z",
      "status": "Published",
      "flags": 0,
      "availability": "Public",
      "nsfwLevel": 7,
      "trainedWords": [
        "sush1spin"
      ],
      "covered": true,
      "stats": {
        "downloadCount": 1115,
        "thumbsUpCount": 155,
        "thumbsDownCount": 1
      },
      "files": [
        {
          "id": 1663074,
          "hashes": {
          },
          "downloadUrl": "https://civitai.com/api/download/models/1762339?fileId=1663074",
          "primary": true
        }
      ]
    }
  ]
}
```

触发词
- 来源1: 元数据 (trainedWords)
- 来源2: description. (看看作者怎么写的)

推荐lora权重: description里面找


## 如何下载

civitai download --version=1762339 # model version

值得注意的是，如果遇上这个bug，则需要去掉https proxy进行尝试。如果还是不行，就提醒用户开启梯子的TUN模式。
```
Error: download sush1spin-000018.safetensors: Get "https://civitai.com/api/download/models/1762339?fileId=1663074": proxyconnect tcp: dial tcp 127.0.0.1:7897: refusing to download from a private/loopback address (127.0.0.1) — the download URL resolved to a non-public IP
```

### 兜底：curl + token（CLI 直连失败时）
TUN 没开、直连超时、CLI 又走不了代理时：
1. token 可能过期。让 CLI 走代理跑一次 API（`civitai models get <id>`）触发 refresh，然后读新 token：
   `grep access_token "$APPDATA/civitai/config.yaml"`
2. 用 curl 走代理下载（curl 的 UA 不会被 Cloudflare 拦）：
   ```bash
   curl -x http://127.0.0.1:7897 -sL --fail -H "Authorization: Bearer <token>" \
     "https://civitai.com/api/download/models/<versionId>?fileId=<fileId>" -o out.safetensors
   ```
   注意：urllib（python）的默认 UA 会被 CF 403 拦，别用。下载后无自动 SHA256，需自行核验大小或手动比对。


