import numpy as np
from PIL import Image
import os

# 生成随机噪声
def generate_random_noise(width, height):
    print(f"生成随机噪声: {width}x{height}")
    noise = np.random.rand(height, width) * 255
    noise = noise.astype(np.uint8)
    print(f"噪声范围: {noise.min()} - {noise.max()}")
    return noise

# 生成Perlin噪声（简化版）
def generate_perlin_noise(width, height, scale=10, octaves=3):
    print(f"生成Perlin噪声: {width}x{height}, scale={scale}, octaves={octaves}")
    noise = np.zeros((height, width))
    for octave in range(octaves):
        octave_scale = scale * (2 ** octave)
        x = np.linspace(0, octave_scale, width, endpoint=False)
        y = np.linspace(0, octave_scale, height, endpoint=False)
        x_grid, y_grid = np.meshgrid(x, y)
        
        # 使用正弦函数模拟Perlin噪声
        noise += np.sin(x_grid) * np.cos(y_grid) / (2 ** octave)
    
    # 归一化到0-255范围
    noise = (noise - noise.min()) / (noise.max() - noise.min()) * 255
    noise = noise.astype(np.uint8)
    print(f"噪声范围: {noise.min()} - {noise.max()}")
    return noise

# 保存噪声图
def save_noise_image(noise, filename):
    print(f"保存噪声图: {filename}")
    img = Image.fromarray(noise, mode='L')
    img.save(filename)
    
    if os.path.exists(filename):
        print(f"成功保存: {filename}, 文件大小: {os.path.getsize(filename)} 字节")
    else:
        print(f"保存失败: {filename}")

# 主函数
if __name__ == "__main__":
    print("开始生成噪声图...")
    # 设置参数
    width, height = 256, 256
    
    # 生成并保存随机噪声
    random_noise = generate_random_noise(width, height)
    save_noise_image(random_noise, "random_noise_pil.png")
    
    # 生成并保存Perlin噪声
    perlin_noise = generate_perlin_noise(width, height, scale=5, octaves=3)
    save_noise_image(perlin_noise, "perlin_noise_pil.png")
    
    print("所有噪声图生成完成！")
    print(f"当前目录: {os.getcwd()}")
    print("目录内容:")
    for file in os.listdir('.'):
        if file.endswith('.png'):
            print(f"  - {file}")
