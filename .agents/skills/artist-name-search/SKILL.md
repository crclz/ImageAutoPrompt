---
name: artist-name-search
description: 对画师正向(danbooru->pixiv)或者反向(pixiv->danbooru)查找画师名称
---

## 与用户交互
- 如果http请求失败且梯子端口不可用请询问用户，不要自己处理
- 如果用户给了超出你能力范围的，请明确告诉用户本skill的能力


## 基础知识
用户可能知道某个画师的pixiv链接例如 https://www.pixiv.net/users/123456 但不知道danbooru tag (danbooru tag有时和pixiv的昵称或者罗马音或拼音完全沾不上边，有时是有改名情况)

用户也可能知道画师的danbooru tag例如 torino_aqua, 但不知道 pixiv的昵称或者链接


## 反向

```bash
❯ curl --proxy=http://localhost:7897 -g https://danbooru.donmai.us/artists.json?search[url_matches]=https://www.pixiv.net/users/1960050

[{"id":48560,"created_at":"2010-05-19T13:59:41.626-04:00","name":"torino_aqua","updated_at":"2026-02-02T22:03:53.984-05:00","is_deleted":false,"group_name":"","is_banned":false,"other_names":["TA","torino","torino_akua","とりの","とりのあくあ"]}]
```

其中 "name":"torino_aqua" 就是https://www.pixiv.net/users/1960050 这个用户的标准danbooru tag

## 正向

查询画师的基础数据、标准名称（例如日文名）。标准名称可能会被其他任务，例如lora搜索，用于搜寻。
```bash
curl --proxy=http://localhost:7897 -g https://danbooru.donmai.us/artists.json?search[name]=torino_aqua

[{"id":48560,"created_at":"2010-05-19T13:59:41.626-04:00","name":"torino_aqua","updated_at":"2026-02-02T22:03:53.984-05:00","is_deleted":false,"group_name":"","is_banned":false,"other_names":["TA","torino","torino_akua","とりの","とりのあくあ"]}]
```


查询artist url(如果用户有查询各大平台跳转链接的需求，才查. 如果用户未明确，优先给pixiv的)
```bash
curl --proxy=http://localhost:7897 -g "https://danbooru.donmai.us/artist_urls.json?search[artist_id]=48560"
[
...
    {
        "id": 2919929,
        "artist_id": 48560,
        "url": "https://seiga.nicovideo.jp/user/illust/21687613",
        "created_at": "2022-03-16T21:37:42.793-04:00",
        "updated_at": "2022-03-16T21:37:42.793-04:00",
        "is_active": true
    },
    {
        "id": 2775112,
        "artist_id": 48560,
        "url": "https://www.pixiv.net/users/1960050",
        "created_at": "2022-03-14T23:24:45.175-04:00",
        "updated_at": "2022-03-14T23:24:45.175-04:00",
        "is_active": true
    }
]
curl --proxy=http://localhost:7897 -g "https://danbooru.donmai.us/artist_urls.json?search[artist][name]=torino_aqua"
```

