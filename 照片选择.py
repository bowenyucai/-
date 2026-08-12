import os
import shutil
import re

def copy_numbered_photos(txt_file_path, source_photo_dir, target_dir, prefixes=None):
    """
    根据文本文档中的数字序号复制对应照片
    
    参数:
    txt_file_path: 包含数字序号的文本文档路径
    source_photo_dir: 源照片文件夹路径
    target_dir: 目标文件夹路径
    prefixes: 照片文件名前缀列表，默认为["DSCN"]，后续可在此处增加其他格式前缀
    """
    
    # 照片文件名前缀，默认为DSCN，后续可在此列表中添加其他格式前缀
    if prefixes is None:
        prefixes = ["DSCN"]  # 可以添加其他前缀如["DSCN", "IMG", "PICTURE"]等
    
    # 检查文本文档是否存在
    if not os.path.exists(txt_file_path):
        raise FileNotFoundError(f"找不到文本文档: {txt_file_path}")
    
    # 检查源照片文件夹是否存在
    if not os.path.exists(source_photo_dir):
        raise FileNotFoundError(f"找不到源照片文件夹: {source_photo_dir}")
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"文本文档: {txt_file_path}")
    print(f"源照片文件夹: {source_photo_dir}")
    print(f"目标文件夹: {target_dir}")
    
    # 读取文本文档并提取所有数字
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        # 如果UTF-8编码失败，尝试GBK编码
        try:
            with open(txt_file_path, 'r', encoding='gbk') as file:
                content = file.read()
        except:
            # 如果GBK也失败，尝试latin-1编码
            with open(txt_file_path, 'r', encoding='latin-1') as file:
                content = file.read()
    
    print(f"文本文档内容长度: {len(content)} 字符")
    
    # 使用正则表达式提取所有数字（包括整数和带前导零的数字）
    # 匹配模式：可选的零填充 + 数字序列
    numbers = re.findall(r'\b0*\d+\b', content)
    
    if not numbers:
        print("文本文档中未找到数字序号")
        return
    
    print(f"从文本文档中提取到 {len(numbers)} 个数字序号")
    
    # 转换为集合去重
    unique_numbers = set(numbers)
    print(f"去重后得到 {len(unique_numbers)} 个唯一数字序号")
    
    # 获取源文件夹中的所有文件
    try:
        source_files = os.listdir(source_photo_dir)
    except FileNotFoundError:
        print(f"错误: 找不到源照片文件夹: {source_photo_dir}")
        return
    
    print(f"源文件夹中有 {len(source_files)} 个文件")
    
    # 支持的图片扩展名
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    copied_count = 0
    not_found_count = 0
    
    # 遍历每个数字，查找对应的照片文件
    for number in unique_numbers:
        number_found = False
        
        # 遍历所有前缀
        for prefix in prefixes:
            # 遍历所有可能的图片扩展名
            for ext in image_extensions:
                # 构建可能的文件名模式
                # 模式1: 前缀 + 数字 + 扩展名（如DSCN1234.jpg）
                possible_filename1 = f"{prefix}{number}{ext}"
                # 模式2: 前缀 + 数字 + 扩展名大写（如DSCN1234.JPG）
                possible_filename2 = f"{prefix}{number}{ext.upper()}"
                # 模式3: 前缀 + 下划线 + 数字 + 扩展名（如DSCN_1234.jpg，如果需要）
                possible_filename3 = f"{prefix}_{number}{ext}"
                # 模式4: 前缀 + 数字 + 其他可能的扩展名变体
                possible_filename4 = f"{prefix}{number}{ext}"
                
                possible_filenames = [possible_filename1, possible_filename2, possible_filename3]
                
                # 检查每个可能的文件名
                for filename in possible_filenames:
                    if filename in source_files:
                        source_path = os.path.join(source_photo_dir, filename)
                        target_path = os.path.join(target_dir, filename)
                        
                        # 复制文件
                        try:
                            shutil.copy2(source_path, target_path)
                            print(f"已复制: {filename}")
                            copied_count += 1
                            number_found = True
                        except Exception as e:
                            print(f"复制文件 {filename} 时出错: {e}")
                        
                        break  # 找到文件后跳出内层循环
                
                if number_found:
                    break  # 找到文件后跳出扩展名循环
            
            if number_found:
                break  # 找到文件后跳出前缀循环
        
        if not number_found:
            # 尝试不区分大小写匹配
            for file in source_files:
                # 检查文件名是否包含数字（不区分大小写）
                for prefix in prefixes:
                    pattern = f"{prefix}{number}"
                    if file.lower().startswith(pattern.lower()):
                        source_path = os.path.join(source_photo_dir, file)
                        target_path = os.path.join(target_dir, file)
                        
                        try:
                            shutil.copy2(source_path, target_path)
                            print(f"已复制（不区分大小写）: {file}")
                            copied_count += 1
                            number_found = True
                            break
                        except Exception as e:
                            print(f"复制文件 {file} 时出错: {e}")
                
                if number_found:
                    break
            
            if not number_found:
                print(f"未找到数字 {number} 对应的照片文件")
                not_found_count += 1
    
    # 输出统计信息
    print("\n" + "="*50)
    print(f"处理完成!")
    print(f"成功复制: {copied_count} 个文件")
    print(f"未找到: {not_found_count} 个数字对应的文件")
    print(f"目标文件夹: {target_dir}")

def main():
    """
    主函数：获取用户输入并执行复制操作
    """
    print("="*50)
    print("照片选择工具")
    print("根据文本文档中的数字序号选择对应照片")
    print("="*50)
    
    # 获取用户输入
    txt_file_path = input("请输入包含数字的文本文档路径 (例如: numbers.txt): ").strip()
    source_photo_dir = input("请输入源照片文件夹路径 (例如: photos): ").strip()
    target_dir = input("请输入目标文件夹路径 (例如: selected_photos): ").strip()
    
    # 如果用户没有输入，使用默认值
    if not txt_file_path:
        txt_file_path = "numbers.txt"
    if not source_photo_dir:
        source_photo_dir = "photos"
    if not target_dir:
        target_dir = "selected_photos"
    
    # 照片文件名前缀列表
    # 可以在此处添加其他格式前缀，例如：["DSCN", "IMG", "PICTURE", "DSC"]
    photo_prefixes = ["DSCN"]
    
    # 询问是否需要添加其他前缀
    add_more_prefixes = input("是否要添加其他照片前缀? (y/n, 默认n): ").strip().lower()
    if add_more_prefixes == 'y' or add_more_prefixes == 'yes':
        more_prefixes = input("请输入其他前缀，用逗号分隔 (例如: IMG,PICTURE): ").strip()
        if more_prefixes:
            additional_prefixes = [p.strip() for p in more_prefixes.split(',') if p.strip()]
            photo_prefixes.extend(additional_prefixes)
    
    print(f"使用的前缀: {photo_prefixes}")
    
    try:
        # 执行复制操作
        copy_numbered_photos(txt_file_path, source_photo_dir, target_dir, photo_prefixes)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请检查文件路径是否正确")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    main()