import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import os

# 生成随机噪声
def generate_random_noise(width, height, scale=1.0):
    print(f"生成随机噪声: {width}x{height}")
    noise = np.random.rand(height, width) * scale
    print(f"噪声范围: {noise.min()} - {noise.max()}")
    return noise

# 生成Perlin噪声（简化版）
def generate_perlin_noise(width, height, scale=10, octaves=1):
    print(f"生成Perlin噪声: {width}x{height}, scale={scale}, octaves={octaves}")
    noise = np.zeros((height, width))
    for octave in range(octaves):
        octave_scale = scale * (2 ** octave)
        x = np.linspace(0, octave_scale, width, endpoint=False)
        y = np.linspace(0, octave_scale, height, endpoint=False)
        x_grid, y_grid = np.meshgrid(x, y)
        
        # 使用正弦函数模拟Perlin噪声
        noise += np.sin(x_grid) * np.cos(y_grid) / (2 ** octave)
    
    # 归一化到0-1范围
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    print(f"噪声范围: {noise.min()} - {noise.max()}")
    return noise

# 生成分形噪声
def generate_fractal_noise(width, height, scale=10, octaves=4):
    print(f"生成分形噪声: {width}x{height}, scale={scale}, octaves={octaves}")
    noise = np.zeros((height, width))
    for octave in range(octaves):
        octave_scale = scale * (2 ** octave)
        x = np.linspace(0, octave_scale, width, endpoint=False)
        y = np.linspace(0, octave_scale, height, endpoint=False)
        x_grid, y_grid = np.meshgrid(x, y)
        
        # 生成随机噪声并平滑
        octave_noise = np.random.randn(height, width)
        octave_noise = gaussian_filter(octave_noise, sigma=2 ** octave)
        
        # 添加到总噪声中
        noise += octave_noise / (2 ** octave)
    
    # 归一化到0-1范围
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    print(f"噪声范围: {noise.min()} - {noise.max()}")
    return noise

# 保存噪声图
def save_noise_image(noise, filename):
    print(f"保存噪声图: {filename}")
    plt.figure(figsize=(10, 10))
    plt.imshow(noise, cmap='gray', vmin=0, vmax=1)
    plt.axis('off')
    plt.tight_layout()
    
    # 确保目录存在
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    plt.savefig(filename, dpi=150, bbox_inches='tight', pad_inches=0)
    plt.close()
    
    if os.path.exists(filename):
        print(f"成功保存: {filename}, 文件大小: {os.path.getsize(filename)} 字节")
    else:
        print(f"保存失败: {filename}")

# 主函数
if __name__ == "__main__":
    print("开始生成噪声图...")
    # 设置参数
    width, height = 512, 512
    
    # 生成并保存随机噪声
    random_noise = generate_random_noise(width, height)
    save_noise_image(random_noise, "random_noise.png")
    
    # 生成并保存Perlin噪声
    perlin_noise = generate_perlin_noise(width, height, scale=5, octaves=3)
    save_noise_image(perlin_noise, "perlin_noise.png")
    
    # 生成并保存分形噪声
    fractal_noise = generate_fractal_noise(width, height, scale=5, octaves=4)
    save_noise_image(fractal_noise, "fractal_noise.png")
    
    print("所有噪声图生成完成！")
    print(f"当前目录: {os.getcwd()}")
    print("目录内容:")
    for file in os.listdir('.'):
        if file.endswith('.png'):
            print(f"  - {file}")
