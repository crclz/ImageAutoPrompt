

# install dependencies

TODO: no version restriction

# run server

flask --app server run

json file: comfyui_template.json

base url:
```pwsh
$env:COMFY_BASE_URL="http://localhost:8188" # windows powershell

export COMFY_BASE_URL="http://localhost:8188" # linux
```

开发的时候，加--debug以享受hot reload


## datasets

10w: https://gist.githubusercontent.com/pythongosssss/1d3efa6050356a08cea975183088159a/raw/a18fb2f94f9156cf4476b0c24a09544d6c0baec6/danbooru-tags.txt