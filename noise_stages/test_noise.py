import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# 生成简单的随机噪声
print("开始生成噪声...")
width, height = 256, 256
noise = np.random.rand(height, width)
print(f"噪声生成完成，范围: {noise.min()} - {noise.max()}")

# 保存噪声图
filename = "test_noise.png"
print(f"保存噪声图到: {filename}")

plt.figure(figsize=(5, 5))
plt.imshow(noise, cmap='gray', vmin=0, vmax=1)
plt.axis('off')
plt.tight_layout()
plt.savefig(filename, dpi=100)
plt.close()

# 检查文件是否存在
if os.path.exists(filename):
    print(f"成功保存: {filename}, 大小: {os.path.getsize(filename)} 字节")
else:
    print(f"保存失败: {filename}")

print("测试完成！")
