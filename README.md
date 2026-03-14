

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