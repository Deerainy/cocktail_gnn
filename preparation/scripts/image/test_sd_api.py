import urllib.request
import json
import base64
import traceback

print("开始执行SD API测试脚本...")

url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

payload = {
    "prompt": "<lora:cocktail_lora_v1:0.6>, Flor de Amaras, realistic cocktail photography, tall highball glass, mezcal hibiscus soda cocktail, deep ruby red translucent drink, lots of clear ice cubes, visible carbonation, lime wheel garnish, marigold petals garnish, salted rim, metal straw, on a wooden bar counter, real bar background, natural indoor lighting, professional beverage photo, realistic, highly detailed, only one glass",
    "negative_prompt": "two glasses, martini glass, top-down view, flat lay, oversized flowers, fantasy drink, surreal, neon pink, glowing liquid, watercolor, illustration, painted, vase, bowl-shaped glass, stem glass, excessive petals, floating garnish, deformed glass, duplicate garnish, plastic texture, low quality, blurry, text, watermark, logo",
    "steps": 24,
    "width": 512,
    "height": 768,
    "cfg_scale": 6.5,
    "sampler_name": "DPM++ 2M Karras"
}

headers = {
    'Content-Type': 'application/json',
}

payload_json = json.dumps(payload).encode('utf-8')

req = urllib.request.Request(url, data=payload_json, headers=headers, method='POST')

try:
    print(f"正在请求SD API: {url}")
    with urllib.request.urlopen(req, timeout=300) as response:
        print(f"API响应状态码: {response.status}")
        response_data = response.read().decode('utf-8')
        print("成功获取API响应数据")
        r = json.loads(response_data)
        
    if "images" in r and len(r["images"]) > 0:
        print("从响应中提取到图片数据")
        image_b64 = r["images"][0]
        
        with open("flor_de_amaras.png", "wb") as f:
            f.write(base64.b64decode(image_b64))
        print("生成完成：flor_de_amaras.png")
    else:
        print(f"API响应中没有包含images字段或images列表为空: {r}")
        
except Exception as e:
    print(f"执行过程中发生错误: {e}")
    traceback.print_exc()