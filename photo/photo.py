from PIL import Image
import os

def create_icons(source_image_path, output_dir):
    """
    将源图片转换为不同尺寸的图标
    
    Args:
        source_image_path: 源图片路径
        output_dir: 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 需要的图标尺寸
    sizes = [16, 32, 48, 128]
    
    try:
        # 检查源文件是否存在
        if not os.path.exists(source_image_path):
            raise FileNotFoundError(f"源图片不存在: {source_image_path}")
            
        print(f"正在处理源图片: {source_image_path}")
        
        # 打开源图片
        with Image.open(source_image_path) as img:
            # 确保图片有透明通道
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 为每个尺寸创建图标
            for size in sizes:
                # 调整图片大小，使用高质量的重采样
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # 保存调整后的图片
                output_path = os.path.join(output_dir, f'hoxino{size}.png')
                resized.save(output_path, 'PNG')
                print(f'已创建 {size}x{size} 图标: {output_path}')
                
        print('所有图标创建完成！')
        
    except Exception as e:
        print(f'创建图标时出错: {str(e)}')

if __name__ == '__main__':
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 源图片路径
    source_image = os.path.join(current_dir, 'app_icon.png')
    
    # 输出目录（浏览器扩展的icons文件夹）
    output_directory = os.path.join(current_dir, '..', '浏览器js', 'browser_extension', 'icons')
    
    print(f"源图片路径: {source_image}")
    print(f"输出目录: {output_directory}")
    
    create_icons(source_image, output_directory)
