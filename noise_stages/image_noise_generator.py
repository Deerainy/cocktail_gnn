from PIL import Image
import numpy as np
import os

# 加载原始图像
def load_image(image_path):
    print(f"加载图像: {image_path}")
    img = Image.open(image_path)
    img = img.convert('RGB')  # 确保图像为RGB模式
    print(f"图像尺寸: {img.size}")
    return img

# 添加高斯噪声
def add_gaussian_noise(img, mean=0, std=25):
    img_array = np.array(img)
    noise = np.random.normal(mean, std, img_array.shape).astype(np.uint8)
    noisy_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_array)

# 添加椒盐噪声
def add_salt_pepper_noise(img, salt_prob=0.01, pepper_prob=0.01):
    img_array = np.array(img)
    noisy_array = img_array.copy()
    height, width, _ = img_array.shape
    
    # 添加盐噪声（白色像素）
    salt = np.random.rand(height, width) < salt_prob
    noisy_array[salt] = 255
    
    # 添加椒噪声（黑色像素）
    pepper = np.random.rand(height, width) < pepper_prob
    noisy_array[pepper] = 0
    
    return Image.fromarray(noisy_array)

# 添加泊松噪声
def add_poisson_noise(img):
    img_array = np.array(img)
    # 泊松噪声基于图像强度
    noisy_array = np.random.poisson(img_array / 255.0 * 255).astype(np.uint8)
    return Image.fromarray(noisy_array)

# 生成不同阶段的噪声图
def generate_noise_stages(image_path, output_dir):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 加载原始图像
    original_img = load_image(image_path)
    
    # 保存原始图像
    original_path = os.path.join(output_dir, "original.png")
    original_img.save(original_path)
    print(f"保存原始图像: {original_path}")
    
    # 生成高斯噪声不同阶段
    for i, std in enumerate([10, 25, 50, 75]):
        noisy_img = add_gaussian_noise(original_img, std=std)
        output_path = os.path.join(output_dir, f"gaussian_noise_{i+1}.png")
        noisy_img.save(output_path)
        print(f"保存高斯噪声图像 (std={std}): {output_path}")
    
    # 生成椒盐噪声不同阶段
    for i, prob in enumerate([0.01, 0.05, 0.1, 0.2]):
        noisy_img = add_salt_pepper_noise(original_img, salt_prob=prob, pepper_prob=prob)
        output_path = os.path.join(output_dir, f"salt_pepper_noise_{i+1}.png")
        noisy_img.save(output_path)
        print(f"保存椒盐噪声图像 (prob={prob}): {output_path}")
    
    # 生成泊松噪声
    noisy_img = add_poisson_noise(original_img)
    output_path = os.path.join(output_dir, "poisson_noise.png")
    noisy_img.save(output_path)
    print(f"保存泊松噪声图像: {output_path}")

# 主函数
if __name__ == "__main__":
    # 图像路径
    image_path = "d:\\spring_boot_content\\graduation-sys\\frontend\\src\\assets\\recipe_image\\2.png"
    
    # 输出目录
    output_dir = "noise_stages"
    
    # 生成噪声图
    generate_noise_stages(image_path, output_dir)
    
    print("所有噪声图生成完成！")
