# -*- coding: utf-8 -*-
"""
根据 ingredient canonical 的名字检索图片并抠图

功能：
1. 从数据库获取 ingredient canonical 信息
2. 根据 canonical 名字搜索网络图片
3. 下载图片
4. 使用 PaddlePaddle 进行抠图
5. 保存抠图后的图片
6. 更新数据库中的图片路径
"""

import os
import sys
import json
import requests
import paddle
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine

# 尝试导入 OpenCV 进行抠图
try:
    import cv2
    print("[INFO] 成功导入 OpenCV")
except ImportError:
    print("[ERROR] 未安装 OpenCV，请先运行：pip install opencv-python")
    import sys
    sys.exit(1)

# 导入大模型相关库
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
import os
_script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts/image
_scripts_dir = os.path.dirname(_script_dir)  # scripts
_root = os.path.dirname(_scripts_dir)  # 项目根目录
_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

# 确保 _root 在 Python 路径中
if _root not in sys.path:
    sys.path.insert(0, _root)

# 大模型配置
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.3"))

class Config:
    """配置类"""
    # 图片保存路径
    IMAGE_DIR = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "canonical_images")
    # 抠图输出路径
    SEGMENTATION_DIR = os.path.join(IMAGE_DIR, "segmented")

def ensure_directories():
    """
    确保图片保存目录存在
    """
    os.makedirs(Config.IMAGE_DIR, exist_ok=True)
    os.makedirs(Config.SEGMENTATION_DIR, exist_ok=True)

def get_canonical_info():
    """
    从数据库获取 canonical 信息，包括对应的 ingredient_id、type 和 recipe 信息
    """
    engine = get_engine()
    sql = text("""
    SELECT lcm.canonical_id, lcm.canonical_name, lcm.src_ingredient_id, 
           it.type_tag, ri.recipe_id, ri.raw_text, r.name as recipe_name
    FROM llm_canonical_map lcm
    LEFT JOIN ingredient_type it ON lcm.src_ingredient_id = it.ingredient_id
    LEFT JOIN recipe_ingredient ri ON lcm.src_ingredient_id = ri.ingredient_id
    LEFT JOIN recipe r ON ri.recipe_id = r.recipe_id
    WHERE lcm.src_image_path IS NULL
    LIMIT 100
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql)
        canonical_info = []
        for row in result:
            canonical_info.append({
                'canonical_id': row.canonical_id,
                'canonical_name': row.canonical_name,
                'src_ingredient_id': row.src_ingredient_id,
                'type_tag': row.type_tag or 'other',
                'recipe_id': row.recipe_id,
                'recipe_name': row.recipe_name,
                'raw_text': row.raw_text
            })
    
    print(f"[INFO] 从数据库获取了 {len(canonical_info)} 个需要图片的 canonical")
    return canonical_info

def get_image_name_from_llm(client, canonical_name, type_tag, recipe_name=None, raw_text=None):
    """
    调用大模型获取图片名称
    
    参数:
    client: OpenAI 客户端
    canonical_name: canonical 名称
    type_tag: 原料类型
    recipe_name: 配方名称
    raw_text: 原始原料文本
    
    返回:
    图片名称
    """
    # 构建提示词，结合 recipe 信息
    recipe_context = ""
    if recipe_name and raw_text:
        recipe_context = f"该原料在以下鸡尾酒配方中使用：\n配方名称：{recipe_name}\n原始原料文本：{raw_text}\n"
    
    prompt = f"""请为以下鸡尾酒原料生成一个合适的图片名称，用于在网络上搜索该原料的图片：

原料名称：{canonical_name}
原料类型：{type_tag}
{recipe_context}
要求：
1. 图片名称应准确描述该原料的外观和特征
2. 图片名称应与原料类型相符（例如，如果是 juice，应该包含果汁相关的描述）
3. 图片名称应简洁明了，适合作为搜索关键词
4. 请只返回图片名称，不要返回任何其他文字或解释

示例输出：
mezcal bottle and glass
fresh lime juice in a glass
whiskey on the rocks
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "你是一个专业的鸡尾酒原料图片检索助手，能够为各种鸡尾酒原料生成合适的图片名称。"},
                {"role": "user", "content": prompt}
            ],
        )
        
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"[ERROR] 大模型生成图片名称失败: {e}")
        return canonical_name

def search_images(query, num=5):
    """
    搜索网络图片
    
    参数:
    query: 搜索关键词
    num: 搜索数量
    
    返回:
    图片 URL 列表
    """
    try:
        # 使用 bing 图片搜索
        url = "https://www.bing.com/images/search"
        params = {
            "q": query,
            "count": num * 2,  # 多获取一些结果，以便过滤
            "form": "HDRSC2",  # 高级搜索形式
            "first": 1
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        # 解析 HTML 页面，提取图片 URL
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        image_urls = []
        # 查找图片标签，优先选择高质量图片
        for img in soup.find_all("img"):
            if "src" in img.attrs:
                src = img["src"]
                # 过滤掉 base64 编码的图片、小图标和占位符
                if (
                    not src.startswith("data:") and 
                    (src.lower().endswith(".jpg") or src.lower().endswith(".jpeg") or src.lower().endswith(".png")) and
                    not "cart" in src.lower() and
                    not "placeholder" in src.lower() and
                    not "icon" in src.lower() and
                    "http" in src
                ):
                    # 确保 URL 完整
                    if not src.startswith("http"):
                        continue
                    image_urls.append(src)
                    if len(image_urls) >= num:
                        break
        
        # 如果没有找到足够的图片，尝试从其他标签中提取
        if len(image_urls) < num:
            for a in soup.find_all("a"):
                if "href" in a.attrs:
                    href = a["href"]
                    if (
                        (href.lower().endswith(".jpg") or href.lower().endswith(".jpeg") or href.lower().endswith(".png")) and
                        "http" in href
                    ):
                        image_urls.append(href)
                        if len(image_urls) >= num:
                            break
        
        return image_urls
    except Exception as e:
        print(f"[ERROR] 搜索图片失败: {e}")
        # 如果搜索失败，返回空列表
        return []

def download_image(url, save_path):
    """
    下载图片
    
    参数:
    url: 图片 URL
    save_path: 保存路径
    
    返回:
    是否下载成功
    """
    try:
        # 发送 HEAD 请求获取文件信息
        head_response = requests.head(url, timeout=5)
        
        # 检查 Content-Type 是否为图片
        content_type = head_response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"[WARNING] 不是图片类型: {content_type}")
            return False
        
        # 检查文件大小，过滤掉小图标
        content_length = head_response.headers.get('Content-Length')
        if content_length:
            size_in_bytes = int(content_length)
            if size_in_bytes < 10000:  # 过滤小于 10KB 的图片
                print(f"[WARNING] 图片太小: {size_in_bytes} bytes")
                return False
        
        # 下载图片
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            # 再次检查内容类型
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                print(f"[WARNING] 不是图片类型: {content_type}")
                return False
            
            # 保存图片
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            # 检查保存后的文件大小
            if os.path.getsize(save_path) < 10000:
                print(f"[WARNING] 保存的图片太小: {os.path.getsize(save_path)} bytes")
                os.remove(save_path)
                return False
            
            return True
        else:
            print(f"[WARNING] 下载失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] 下载图片失败: {e}")
        return False

def segment_image(image_path, output_path):
    """
    使用 OpenCV 进行简单抠图
    
    参数:
    image_path: 原始图片路径
    output_path: 抠图结果保存路径
    
    返回:
    是否抠图成功
    """
    try:
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            print(f"[ERROR] 无法读取图片: {image_path}")
            return False
        
        # 转换为 HSV 颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 定义背景颜色范围（这里假设背景是白色或浅色）
        lower_white = cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))
        
        # 创建掩码
        mask = cv2.bitwise_not(lower_white)
        
        # 应用掩码
        result = cv2.bitwise_and(image, image, mask=mask)
        
        # 保存结果
        cv2.imwrite(output_path, result)
        return True
    except Exception as e:
        print(f"[ERROR] 抠图失败: {e}")
        return False

def update_database(canonical_id, image_path):
    """
    更新数据库中的图片路径
    
    参数:
    canonical_id: canonical ID
    image_path: 图片相对路径
    """
    engine = get_engine()
    sql = text("""
    UPDATE llm_canonical_map
    SET src_image_path = :image_path
    WHERE canonical_id = :canonical_id
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            'canonical_id': canonical_id,
            'image_path': image_path
        })
    
    print(f"[INFO] 更新数据库成功，canonical_id: {canonical_id}, image_path: {image_path}")

def main():
    """
    主函数
    """
    print("开始检索和抠图...")
    
    # 确保目录存在
    ensure_directories()
    
    # 获取 API Key
    print(f"[DEBUG] 环境变量文件路径: {_llm_env}")
    print(f"[DEBUG] 环境变量文件是否存在: {os.path.exists(_llm_env)}")
    
    # 尝试直接读取文件内容
    if os.path.exists(_llm_env):
        with open(_llm_env, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[DEBUG] 环境变量文件内容: {content}")
    
    # 加载环境变量
    load_dotenv(_llm_env, override=True)
    
    # 检查环境变量
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"[DEBUG] DEEPSEEK_API_KEY: {deepseek_key}")
    print(f"[DEBUG] OPENAI_API_KEY: {openai_key}")
    
    api_key = deepseek_key or openai_key
    if not api_key:
        print("[ERROR] 缺少 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        return
    
    # 创建 OpenAI 客户端
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    
    # 获取 canonical 信息
    canonical_info = get_canonical_info()
    
    # 处理每个 canonical
    for item in canonical_info:
        canonical_id = item['canonical_id']
        canonical_name = item['canonical_name']
        type_tag = item['type_tag']
        
        print(f"[INFO] 处理 canonical: {canonical_name} (ID: {canonical_id}, Type: {type_tag})")
        
        # 使用大模型获取图片名称
        image_name = get_image_name_from_llm(
            client, 
            canonical_name, 
            type_tag,
            recipe_name=item.get('recipe_name'),
            raw_text=item.get('raw_text')
        )
        print(f"[INFO] 生成的图片名称: {image_name}")
        
        # 使用图片名称搜索图片
        image_urls = search_images(image_name)
        
        if not image_urls:
            print(f"[WARNING] 未找到 {canonical_name} 的图片")
            continue
        
        # 尝试下载图片，直到成功
        image_path = None
        for url in image_urls:
            image_filename = f"{canonical_id}_{canonical_name.replace(' ', '_')}.jpg"
            temp_path = os.path.join(Config.IMAGE_DIR, image_filename)
            
            if download_image(url, temp_path):
                print(f"[INFO] 下载图片成功: {temp_path}")
                image_path = temp_path
                break
            else:
                print(f"[WARNING] 下载图片失败: {url}")
        
        if not image_path:
            print(f"[ERROR] 所有图片 URL 都下载失败")
            continue
        
        # 抠图
        segmented_filename = f"{canonical_id}_{canonical_name.replace(' ', '_')}_segmented.jpg"
        segmented_path = os.path.join(Config.SEGMENTATION_DIR, segmented_filename)
        
        if segment_image(image_path, segmented_path):
            print(f"[INFO] 抠图成功: {segmented_path}")
            
            # 计算相对路径
            relative_path = os.path.relpath(segmented_path, str(Path(__file__).resolve().parents[2]))
            
            # 更新数据库
            update_database(canonical_id, relative_path)
        else:
            print(f"[ERROR] 抠图失败")
        
        # 避免请求过于频繁
        import time
        time.sleep(SLEEP_SEC)
    
    print("检索和抠图完成！")

if __name__ == "__main__":
    main()
