"""
提取 Unity Assets 文件中的字体信息
用来查看 sharedassets0.assets 中包含哪些字体
"""

import UnityPy
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def list_fonts_in_asset(asset_path):
    """
    列出 Assets 文件中的所有字体信息
    
    Args:
        asset_path: Assets 文件路径 (如 sharedassets0.assets)
    """
    
    print("=" * 60)
    print(f"正在分析文件: {asset_path}")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(asset_path):
        print(f"❌ 错误: 找不到文件 '{asset_path}'")
        return False
    
    file_size = os.path.getsize(asset_path)
    print(f"文件大小: {file_size / (1024*1024):.2f} MB")
    print()
    
    # 加载 Assets 文件
    try:
        print("正在加载 Assets 文件...")
        env = UnityPy.load(asset_path)
        print("✅ 加载成功！")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False
    
    print()
    print("=" * 60)
    print("开始扫描字体对象...")
    print("=" * 60)
    print()
    
    fonts = []
    other_objects = {
        'Texture2D': [],
        'Material': [],
        'Shader': [],
        'Sprite': [],
        'GameObject': [],
        'Transform': [],
        '其他': []
    }
    
    # 遍历所有对象
    for obj in env.objects:
        obj_type = obj.type.name
        
        if obj_type == "Font":
            try:
                font_obj = obj.read()
                font_info = {
                    'name': font_obj.m_Name,
                    'path_id': obj.path_id,
                    'object': font_obj,
                    'has_font_data': hasattr(font_obj, 'm_FontData') and font_obj.m_FontData is not None
                }
                fonts.append(font_info)
            except Exception as e:
                print(f"⚠️ 读取字体对象失败 (PathID: {obj.path_id}): {e}")
        else:
            # 统计其他对象类型
            if obj_type in other_objects:
                other_objects[obj_type].append(obj_type)
            else:
                other_objects['其他'].append(obj_type)
    
    # 显示字体信息
    print(f"找到 {len(fonts)} 个字体对象:")
    print()
    
    if len(fonts) == 0:
        print("⚠️ 未找到任何字体对象")
    else:
        for i, font in enumerate(fonts, 1):
            print(f"{i}. 字体名: {font['name']}")
            print(f"   PathID: {font['path_id']}")
            print(f"   有字体数据: {'✅ 是' if font['has_font_data'] else '❌ 否'}")
            
            # 显示字体数据大小
            if font['has_font_data']:
                font_data_size = len(font['object'].m_FontData)
                print(f"   数据大小: {font_data_size / 1024:.2f} KB")
            print()
    
    # 显示其他对象统计
    print("=" * 60)
    print("其他对象统计:")
    print("=" * 60)
    for obj_type, count in other_objects.items():
        if count:
            print(f"{obj_type}: {len(count)}")
    
    print()
    print("=" * 60)
    print("总结:")
    print("=" * 60)
    print(f"字体对象: {len(fonts)}")
    print(f"总对象数: {len(list(env.objects))}")
    
    return True


def extract_font_file(asset_path, font_name, output_path):
    """
    从 Assets 文件中提取单个字体文件
    
    Args:
        asset_path: Assets 文件路径
        font_name: 字体名称 (如 'OpenSans-Bold')
        output_path: 输出文件路径 (如 'OpenSans-Bold.ttf')
    """
    
    print(f"\n正在从 '{asset_path}' 中提取字体: {font_name}")
    
    try:
        env = UnityPy.load(asset_path)
        
        for obj in env.objects:
            if obj.type.name == "Font":
                font_obj = obj.read()
                
                if font_obj.m_Name == font_name:
                    if hasattr(font_obj, 'm_FontData') and font_obj.m_FontData:
                        # 保存字体文件
                        with open(output_path, 'wb') as f:
                            f.write(font_obj.m_FontData)
                        
                        file_size = os.path.getsize(output_path)
                        print(f"✅ 成功提取: {output_path}")
                        print(f"   文件大小: {file_size / 1024:.2f} KB")
                        return True
                    else:
                        print(f"❌ 字体 '{font_name}' 没有字体数据")
                        return False
        
        print(f"❌ 找不到字体 '{font_name}'")
        return False
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Unity 字体提取工具")
    print("=" * 60)
    print()
    
    # 弹出文件选择窗口
    print("请在弹出的窗口中选择 .assets 文件...")
    try:
        root = tk.Tk()
        root.withdraw()  # 隐藏根窗口
        asset_file = filedialog.askopenfilename(
            title="选择 .assets 文件",
            filetypes=[("Unity Assets", "*.assets"), ("All Files", "*.*")],
            mustexist=True
        )
        root.destroy()
    except Exception as e:
        print(f"❌ 错误：无法打开文件选择窗口: {e}")
        sys.exit(1)
    
    if not asset_file:
        print("❌ 操作已取消：未选择任何文件")
        sys.exit(0)
    
    print(f"✅ 已选择: {asset_file}")
    print()
    
    # 可选: 提取某个字体
    print()
    print("=" * 60)
    print("提取字体:")
    print("=" * 60)
    response = input("是否要提取某个字体? (y/n): ").strip().lower()
    
    if response == 'y':
        font_name = input("输入字体名称 (如 OpenSans-Bold): ").strip()
        
        if not font_name:
            print("❌ 字体名称不能为空")
            sys.exit(1)
        
        # 弹出文件保存窗口
        print("请在弹出的窗口中选择输出文件位置...")
        try:
            root = tk.Tk()
            root.withdraw()
            output_file = filedialog.asksaveasfilename(
                title="保存字体文件",
                defaultextension=".ttf",
                filetypes=[("TrueType Font", "*.ttf"), ("OpenType Font", "*.otf"), ("All Files", "*.*")]
            )
            root.destroy()
        except Exception as e:
            print(f"❌ 错误：无法打开文件保存窗口: {e}")
            sys.exit(1)
        
        if output_file:
            extract_font_file(asset_file, font_name, output_file)
        else:
            print("❌ 操作已取消")
