import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import tkinter.font as tkFont
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import requests
import os
import re
import subprocess
import time
from urllib.parse import urlparse, urljoin
import m3u8
from pathlib import Path
import json
from datetime import datetime
import cv2
from PIL import Image, ImageTk
import webbrowser

class VideoDownloader:
    def __init__(self, root):
        self.root = root
        
        # 初始化变量
        self.download_queue = []
        self.is_downloading = False
        self.current_download_thread = None
        self.output_dir = os.path.join(os.getcwd(), "downloads")
        self.create_folder_name = ""
        self.video_player = None
        self.current_video_path = None
        self.max_threads = 5
        self.active_downloads = 0
        
        # 视频播放相关变量
        self.video_cap = None
        self.is_playing = False
        self.current_video_url = None
        self.video_thread = None
        
        # 确保下载目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置UI
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("M3U8/MP4 批量下载工具 v2.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置现代化字体
        self.default_font = tkFont.Font(family="Microsoft YaHei UI", size=9)
        self.title_font = tkFont.Font(family="Microsoft YaHei UI", size=12, weight="bold")
        self.button_font = tkFont.Font(family="Microsoft YaHei UI", size=9)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧面板
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 右侧面板（视频播放器）
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
        
    def setup_left_panel(self, parent):
        # 标题
        title_label = ttk.Label(parent, text="M3U8/MP4 批量下载工具", font=self.title_font)
        title_label.pack(pady=(0, 10))
        
        # 拖拽区域
        drag_frame = ttk.LabelFrame(parent, text="拖拽链接区域", padding=10)
        drag_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.drag_text = tk.Text(drag_frame, height=8, wrap=tk.WORD, font=self.default_font,
                                bg='#ffffff', relief=tk.FLAT, borderwidth=1)
        self.drag_text.pack(fill=tk.BOTH, expand=True)
        self.drag_text.insert(tk.END, "请拖拽包含视频链接的文本文件到此处，或直接粘贴链接...\n\n支持格式：\n- M3U8链接\n- MP4直链\n- 包含链接的文本文件")
        
        # 启用拖拽功能
        self.drag_text.drop_target_register(DND_FILES)
        self.drag_text.dnd_bind('<<Drop>>', self.on_drop)
        
        # 控制按钮区域
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行按钮
        btn_frame1 = ttk.Frame(control_frame)
        btn_frame1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(btn_frame1, text="选择输出目录", command=self.select_output_dir).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame1, text="创建子文件夹", command=self.create_subfolder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame1, text="清空列表", command=self.clear_all).pack(side=tk.LEFT, padx=(0, 5))
        
        # 第二行按钮
        btn_frame2 = ttk.Frame(control_frame)
        btn_frame2.pack(fill=tk.X)
        
        self.download_btn = ttk.Button(btn_frame2, text="开始下载", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(btn_frame2, text="停止下载", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame2, text="手动添加", command=self.add_url_manually).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame2, text="删除选中", command=self.remove_selected_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame2, text="打开下载目录", command=self.open_download_dir).pack(side=tk.LEFT, padx=(0, 5))
        
        # 输出目录显示
        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="输出目录:", font=self.default_font).pack(side=tk.LEFT)
        self.dir_label = ttk.Label(dir_frame, text=self.output_dir, font=self.default_font, foreground='#0066cc')
        self.dir_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 下载列表
        list_frame = ttk.LabelFrame(parent, text="下载列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview
        columns = ('序号', '文件名', '链接', '状态', '进度')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # 设置列标题和宽度
        self.tree.heading('序号', text='序号')
        self.tree.heading('文件名', text='文件名')
        self.tree.heading('链接', text='链接')
        self.tree.heading('状态', text='状态')
        self.tree.heading('进度', text='进度')
        
        self.tree.column('序号', width=50, anchor=tk.CENTER)
        self.tree.column('文件名', width=120, anchor=tk.W)
        self.tree.column('链接', width=300, anchor=tk.W)
        self.tree.column('状态', width=80, anchor=tk.CENTER)
        self.tree.column('进度', width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件和右键菜单
        self.tree.bind('<Double-1>', self.on_item_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="播放视频", command=self.play_selected_video)
        self.context_menu.add_command(label="复制链接", command=self.copy_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除选中", command=self.remove_selected_item)
        self.context_menu.add_command(label="重新下载", command=self.redownload_selected)
        
        # 进度条
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X)
        
        ttk.Label(progress_frame, text="总进度:", font=self.default_font).pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
    def setup_right_panel(self, parent):
        # 视频播放器区域
        player_frame = ttk.LabelFrame(parent, text="视频播放器", padding=10)
        player_frame.pack(fill=tk.BOTH, expand=True)
        
        # 视频显示区域
        self.video_frame = tk.Frame(player_frame, bg='black', width=400, height=300)
        self.video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.video_frame.pack_propagate(False)
        
        # 视频显示标签
        self.video_label = tk.Label(self.video_frame, bg='black', text="点击视频链接开始播放", fg='white')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # 播放器控制
        control_frame = ttk.Frame(player_frame)
        control_frame.pack(fill=tk.X)
        
        self.play_btn = ttk.Button(control_frame, text="播放", command=self.toggle_play, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_video_btn = ttk.Button(control_frame, text="停止", command=self.stop_video, state=tk.DISABLED)
        self.stop_video_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 音量控制
        ttk.Label(control_frame, text="音量:").pack(side=tk.LEFT, padx=(10, 5))
        self.volume_var = tk.DoubleVar(value=50)
        self.volume_scale = ttk.Scale(control_frame, from_=0, to=100, variable=self.volume_var, orient=tk.HORIZONTAL)
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 播放信息
        info_frame = ttk.Frame(player_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.video_info_label = ttk.Label(info_frame, text="未选择视频", font=self.default_font)
        self.video_info_label.pack()
        
    def on_drop(self, event):
        """处理拖拽事件"""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            if os.path.isfile(file_path):
                self.process_dropped_file(file_path)
            else:
                # 如果是文本，直接处理
                self.process_text_content(file_path)
                
    def process_dropped_file(self, file_path):
        """处理拖拽的文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.process_text_content(content)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {str(e)}")
            
    def process_text_content(self, content):
        """处理文本内容，提取链接"""
        # 清空文本框并添加新内容
        self.drag_text.delete(1.0, tk.END)
        self.drag_text.insert(tk.END, content)
        
        # 提取链接
        urls = self.extract_urls(content)
        
        # 添加到下载列表
        for url in urls:
            current_index = len(self.download_queue) + 1
            filename = f"{current_index}.mp4"
            self.download_queue.append({
                'url': url,
                'filename': filename,
                'status': '等待下载',
                'progress': '0%'
            })
            
            # 添加到树形视图
            self.tree.insert('', tk.END, values=(
                current_index,
                filename,
                url[:50] + '...' if len(url) > 50 else url,
                '等待下载',
                '0%'
            ))
            
    def extract_urls(self, text):
        """从文本中提取URL"""
        # 匹配HTTP/HTTPS链接
        url_pattern = r'https?://[^\s<>"\[\]{}|\\^`]+'
        urls = re.findall(url_pattern, text)
        
        # 过滤出视频相关链接
        video_urls = []
        for url in urls:
            if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.avi', '.mov', '.mkv', '.flv']):
                video_urls.append(url)
            elif 'm3u8' in url.lower() or 'video' in url.lower():
                video_urls.append(url)
                
        return video_urls
        
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(initialdir=self.output_dir)
        if directory:
            self.output_dir = directory
            self.dir_label.config(text=self.output_dir)
            
    def create_subfolder(self):
        """创建子文件夹"""
        folder_name = simpledialog.askstring("创建文件夹", "请输入文件夹名称:")
        if folder_name:
            self.create_folder_name = folder_name
            new_dir = os.path.join(self.output_dir, folder_name)
            os.makedirs(new_dir, exist_ok=True)
            self.output_dir = new_dir
            self.dir_label.config(text=self.output_dir)
            messagebox.showinfo("成功", f"文件夹 '{folder_name}' 创建成功")
            
    def clear_all(self):
        """清空所有列表"""
        if messagebox.askyesno("确认", "确定要清空所有下载列表吗？"):
            self.download_queue.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.drag_text.delete(1.0, tk.END)
            self.drag_text.insert(tk.END, "请拖拽包含视频链接的文本文件到此处，或直接粘贴链接...")
            self.progress_var.set(0)
            
    def start_download(self):
        """开始下载"""
        if not self.download_queue:
            messagebox.showwarning("警告", "下载列表为空")
            return
            
        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中")
            return
            
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 启动下载线程
        self.current_download_thread = threading.Thread(target=self.download_worker)
        self.current_download_thread.daemon = True
        self.current_download_thread.start()
        
    def stop_download(self):
        """停止下载"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def download_worker(self):
        """下载工作线程管理器"""
        import concurrent.futures
        
        total_files = len(self.download_queue)
        completed_count = 0
        
        # 使用线程池进行并发下载
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # 提交所有下载任务
            future_to_index = {}
            for i, item in enumerate(self.download_queue):
                if not self.is_downloading:
                    break
                future = executor.submit(self.download_single_file, item, i)
                future_to_index[future] = i
            
            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_index):
                if not self.is_downloading:
                    break
                    
                index = future_to_index[future]
                try:
                    success = future.result()
                    completed_count += 1
                    
                    if success:
                        self.update_tree_item(index, status="完成", progress="100%")
                    else:
                        self.update_tree_item(index, status="失败", progress="0%")
                        
                    # 更新总进度
                    progress = (completed_count / total_files) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                except Exception as e:
                    self.update_tree_item(index, status="错误", progress="0%")
                    print(f"下载错误: {str(e)}")
                    completed_count += 1
                    
        # 下载完成
        self.root.after(0, self.download_completed)
        
    def download_single_file(self, item, index):
        """下载单个文件的工作函数"""
        try:
            # 更新状态
            self.update_tree_item(index, status="下载中")
            
            # 下载文件
            success = self.download_file(item['url'], item['filename'], index)
            return success
            
        except Exception as e:
            print(f"下载文件异常: {str(e)}")
            return False
        
    def download_file(self, url, filename, index):
        """下载单个文件"""
        try:
            output_path = os.path.join(self.output_dir, filename)
            
            if url.lower().endswith('.m3u8') or 'm3u8' in url.lower():
                # 使用ffmpeg下载M3U8
                return self.download_m3u8(url, output_path, index)
            else:
                # 直接下载MP4等文件
                return self.download_direct(url, output_path, index)
                
        except Exception as e:
            print(f"下载文件失败: {str(e)}")
            return False
            
    def download_m3u8(self, url, output_path, index):
        """使用ffmpeg下载M3U8"""
        try:
            # 查找ffmpeg路径
            ffmpeg_path = None
            possible_paths = [
                os.path.join(os.getcwd(), "ffmpeg.exe"),
                os.path.join(os.getcwd(), "视频速率修改工具", "ffmpeg.exe"),
                "ffmpeg"
            ]
            
            for path in possible_paths:
                if os.path.exists(path) or path == "ffmpeg":
                    ffmpeg_path = path
                    break
                    
            if not ffmpeg_path:
                print("未找到ffmpeg")
                self.update_tree_item(index, status="失败", progress="未找到ffmpeg")
                return False
                
            # 构建ffmpeg命令 - 使用更兼容的参数
            cmd = [
                ffmpeg_path,
                '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '-headers', 'Referer: https://v.qq.com/',
                '-headers', 'Origin: https://v.qq.com',
                '-headers', 'Accept: */*',
                '-headers', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
                '-headers', 'Accept-Encoding: gzip, deflate, br',
                '-headers', 'Connection: keep-alive',
                '-headers', 'Sec-Fetch-Dest: video',
                '-headers', 'Sec-Fetch-Mode: cors',
                '-headers', 'Sec-Fetch-Site: cross-site',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_delay_max', '5',
                '-reconnect_at_eof', '1',
                '-timeout', '30000000',
                '-i', url,
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-fflags', '+genpts',
                '-movflags', '+faststart',
                '-f', 'mp4',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            self.update_tree_item(index, progress="开始下载...")
            
            # 启动进程
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 收集所有输出用于调试
            stderr_output = []
            error_count = 0
            reconnect_count = 0
            
            # 监控进程输出
            while True:
                if not self.is_downloading:
                    process.terminate()
                    return False
                    
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                    
                if output.strip():
                    stderr_output.append(output.strip())
                    
                # 检测错误模式
                if 'Will reconnect' in output or 'error=End of file' in output:
                    reconnect_count += 1
                    if reconnect_count > 10:  # 如果重连次数过多，直接切换到备用方法
                        print(f"检测到过多重连尝试({reconnect_count})，切换到备用方法")
                        process.terminate()
                        return self.download_m3u8_fallback(url, output_path, index)
                        
                if 'Server returned 403' in output or 'Forbidden' in output:
                    error_count += 1
                    if error_count > 3:  # 如果403错误过多，直接切换
                        print("检测到多次403错误，切换到备用方法")
                        process.terminate()
                        return self.download_m3u8_fallback(url, output_path, index)
                    
                # 解析进度
                if 'time=' in output:
                    try:
                        # 提取时间信息
                        time_match = re.search(r'time=(\d+:\d+:\d+\.\d+)', output)
                        if time_match:
                            self.update_tree_item(index, progress=f"下载中 {time_match.group(1)}")
                    except:
                        self.update_tree_item(index, progress="下载中...")
                elif 'Opening' in output or 'Stream' in output:
                    self.update_tree_item(index, progress="连接中...")
                elif 'frame=' in output:
                    try:
                        frame_match = re.search(r'frame=\s*(\d+)', output)
                        if frame_match:
                            self.update_tree_item(index, progress=f"处理帧 {frame_match.group(1)}")
                    except:
                        pass
                elif reconnect_count > 0:
                    self.update_tree_item(index, progress=f"重连中({reconnect_count})...")
                        
                # 打印调试信息（减少输出）
                if output.strip() and not ('Skip' in output or 'Will reconnect' in output):
                    print(f"FFmpeg输出: {output.strip()}")
                    
            # 等待进程完成
            process.wait()
            return_code = process.returncode
            print(f"FFmpeg返回码: {return_code}")
            
            # 如果有错误输出，打印最后几行
            if stderr_output:
                print("FFmpeg错误输出（最后10行）:")
                for line in stderr_output[-10:]:
                    print(f"  {line}")
            
            # 检查输出文件是否存在
            if return_code == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.update_tree_item(index, status="完成", progress="100%")
                return True
            else:
                # 尝试备用方法
                print(f"标准方法失败（返回码: {return_code}），尝试备用方法...")
                if self.download_m3u8_fallback(url, output_path, index):
                    return True
                else:
                    # 最后尝试yt-dlp方法
                    print("备用方法也失败，尝试yt-dlp方法...")
                    return self.download_m3u8_ytdlp(url, output_path, index)
                
        except Exception as e:
            print(f"M3U8下载异常: {str(e)}")
            self.update_tree_item(index, status="失败", progress=f"异常: {str(e)[:20]}")
            return False
            
    def download_m3u8_fallback(self, url, output_path, index):
        """M3U8下载备用方法"""
        try:
            # 查找ffmpeg路径
            ffmpeg_path = None
            possible_paths = [
                os.path.join(os.getcwd(), "ffmpeg.exe"),
                os.path.join(os.getcwd(), "视频速率修改工具", "ffmpeg.exe"),
                "ffmpeg"
            ]
            
            for path in possible_paths:
                if os.path.exists(path) or path == "ffmpeg":
                    ffmpeg_path = path
                    break
                    
            if not ffmpeg_path:
                return False
                
            # 使用更简单但带请求头的命令
            cmd = [
                ffmpeg_path,
                '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '-headers', 'Referer: https://v.qq.com/',
                '-timeout', '30000000',
                '-i', url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                '-y',
                output_path
            ]
            
            print(f"执行备用命令: {' '.join(cmd)}")
            self.update_tree_item(index, progress="尝试备用方法...")
            
            # 启动进程
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 等待完成
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5分钟超时
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                print("备用方法超时")
                return False
            return_code = process.returncode
            
            print(f"备用方法返回码: {return_code}")
            if stderr:
                print(f"备用方法错误输出: {stderr[-500:]}")
            
            # 检查输出文件
            if return_code == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.update_tree_item(index, status="完成", progress="100%")
                return True
            else:
                self.update_tree_item(index, status="失败", progress="下载失败")
                return False
                
        except Exception as e:
             print(f"备用方法异常: {str(e)}")
             self.update_tree_item(index, status="失败", progress="备用方法失败")
             return False
             
    def download_m3u8_ytdlp(self, url, output_path, index):
        """使用yt-dlp下载M3U8（最后备选方案）"""
        try:
            # 检查是否有yt-dlp
            ytdlp_path = None
            possible_paths = [
                os.path.join(os.getcwd(), "yt-dlp.exe"),
                os.path.join(os.getcwd(), "视频速率修改工具", "yt-dlp.exe"),
                "yt-dlp"
            ]
            
            for path in possible_paths:
                if os.path.exists(path) or path == "yt-dlp":
                    ytdlp_path = path
                    break
                    
            if not ytdlp_path:
                print("未找到yt-dlp，尝试使用requests直接下载")
                return self.download_m3u8_requests(url, output_path, index)
                
            # 使用yt-dlp下载
            cmd = [
                ytdlp_path,
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '--referer', 'https://v.qq.com/',
                '--add-header', 'Origin:https://v.qq.com',
                '--merge-output-format', 'mp4',
                '--output', output_path,
                url
            ]
            
            print(f"执行yt-dlp命令: {' '.join(cmd)}")
            self.update_tree_item(index, progress="尝试yt-dlp方法...")
            
            # 启动进程
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 等待完成
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5分钟超时
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                print("yt-dlp方法超时")
                return False
            return_code = process.returncode
            
            print(f"yt-dlp返回码: {return_code}")
            if stderr:
                print(f"yt-dlp错误输出: {stderr[-500:]}")
            
            # 检查输出文件
            if return_code == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.update_tree_item(index, status="完成", progress="100%")
                return True
            else:
                print("yt-dlp方法也失败，尝试requests直接下载")
                return self.download_m3u8_requests(url, output_path, index)
                
        except Exception as e:
            print(f"yt-dlp方法异常: {str(e)}")
            return self.download_m3u8_requests(url, output_path, index)
            
    def download_m3u8_requests(self, url, output_path, index):
        """使用requests库直接下载M3U8（最后的最后备选方案）"""
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://v.qq.com/',
                'Origin': 'https://v.qq.com',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            self.update_tree_item(index, progress="尝试直接下载...")
            
            # 直接下载文件
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not self.is_downloading:
                        return False
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.update_tree_item(index, progress=f"{progress}%")
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.update_tree_item(index, status="完成", progress="100%")
                return True
            else:
                self.update_tree_item(index, status="失败", progress="下载失败")
                return False
                
        except Exception as e:
            print(f"requests下载异常: {str(e)}")
            self.update_tree_item(index, status="失败", progress=f"下载失败: {str(e)[:20]}")
            return False
            
    def download_direct(self, url, output_path, index):
        """使用aria2c下载文件"""
        try:
            # 查找aria2c路径
            aria2c_path = None
            possible_paths = [
                os.path.join(os.getcwd(), "aria2c.exe"),
                os.path.join(os.getcwd(), "视频速率修改工具", "aria2c.exe"),
                "aria2c"
            ]
            
            for path in possible_paths:
                if os.path.exists(path) or path == "aria2c":
                    aria2c_path = path
                    break
                    
            if not aria2c_path:
                print("未找到aria2c，使用requests下载")
                return self.download_with_requests(url, output_path, index)
                
            # 构建aria2c命令
            cmd = [
                aria2c_path,
                '--dir=' + os.path.dirname(output_path),
                '--out=' + os.path.basename(output_path),
                '--max-connection-per-server=16',
                '--split=16',
                '--min-split-size=1M',
                '--continue=true',
                '--allow-overwrite=true',
                '--summary-interval=1',
                url
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            
            # 启动进程
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 监控进程输出
            while True:
                if not self.is_downloading:
                    process.terminate()
                    return False
                    
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                    
                # 解析进度
                if '%' in output and '(' in output:
                    try:
                        # 提取百分比
                        percent_match = re.search(r'\((\d+)%\)', output)
                        if percent_match:
                            progress = percent_match.group(1)
                            self.update_tree_item(index, progress=f"{progress}%")
                    except:
                        self.update_tree_item(index, progress="下载中...")
                        
                # 打印调试信息
                if output.strip():
                    print(f"Aria2c输出: {output.strip()}")
                    
            # 检查返回码
            return_code = process.returncode
            print(f"Aria2c返回码: {return_code}")
            
            # 检查输出文件是否存在
            if return_code == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print(f"下载失败，返回码: {return_code}")
                return False
                
        except Exception as e:
            print(f"Aria2c下载异常: {str(e)}")
            return self.download_with_requests(url, output_path, index)
            
    def download_with_requests(self, url, output_path, index):
        """使用requests作为备用下载方法"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not self.is_downloading:
                        return False
                        
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.update_tree_item(index, progress=f"{progress:.1f}%")
                            
            return True
            
        except Exception as e:
            print(f"Requests下载失败: {str(e)}")
            return False
            
    def update_tree_item(self, index, status=None, progress=None):
        """更新树形视图项目"""
        def update():
            items = self.tree.get_children()
            if index < len(items):
                item = items[index]
                values = list(self.tree.item(item, 'values'))
                if status:
                    values[3] = status
                if progress:
                    values[4] = progress
                self.tree.item(item, values=values)
                
        self.root.after(0, update)
        
    def download_completed(self):
        """下载完成处理"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        messagebox.showinfo("完成", "所有下载任务已完成")
        
    def open_download_dir(self):
        """打开下载目录"""
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)
        else:
            messagebox.showerror("错误", "下载目录不存在")
            
    def on_item_double_click(self, event):
        """处理列表项双击事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if len(values) >= 3:
                url = values[2]
                if url.endswith('...'):  # 如果URL被截断，从原始数据获取
                    index = int(values[0]) - 1
                    if index < len(self.download_queue):
                        url = self.download_queue[index]['url']
                        
                # 如果是MP4文件，尝试播放
                if '.mp4' in url.lower():
                    self.play_video_from_url(url)
                else:
                    # 在浏览器中打开链接
                    webbrowser.open(url)
                    
    def play_video_from_url(self, url):
        """在内嵌播放器中播放视频"""
        try:
            # 停止当前播放
            self.stop_video()
            
            # 设置当前视频URL
            self.current_video_url = url
            
            # 尝试使用OpenCV打开视频
            self.video_cap = cv2.VideoCapture(url)
            
            if not self.video_cap.isOpened():
                messagebox.showerror("播放错误", "无法打开视频文件")
                return
                
            # 开始播放
            self.is_playing = True
            self.play_btn.config(state=tk.NORMAL, text="暂停")
            self.stop_video_btn.config(state=tk.NORMAL)
            self.video_info_label.config(text=f"正在播放: {url[:50]}...")
            
            # 启动播放线程
            self.video_thread = threading.Thread(target=self.video_playback_loop, daemon=True)
            self.video_thread.start()
            
        except Exception as e:
            messagebox.showerror("播放错误", f"无法播放视频: {str(e)}")
            
    def video_playback_loop(self):
        """视频播放循环"""
        try:
            while self.is_playing and self.video_cap and self.video_cap.isOpened():
                ret, frame = self.video_cap.read()
                if not ret:
                    break
                    
                # 调整帧大小以适应显示区域
                frame_height, frame_width = frame.shape[:2]
                display_width = 400
                display_height = 300
                
                # 计算缩放比例，保持宽高比
                scale_w = display_width / frame_width
                scale_h = display_height / frame_height
                scale = min(scale_w, scale_h)
                
                new_width = int(frame_width * scale)
                new_height = int(frame_height * scale)
                
                # 调整帧大小
                frame = cv2.resize(frame, (new_width, new_height))
                
                # 转换颜色格式 (BGR to RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 转换为PIL图像
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                
                # 在主线程中更新显示
                self.root.after(0, self.update_video_frame, photo)
                
                # 控制播放速度 (大约30fps)
                time.sleep(1/30)
                
        except Exception as e:
            print(f"视频播放错误: {str(e)}")
        finally:
            # 播放结束，重置状态
            self.root.after(0, self.video_playback_finished)
            
    def update_video_frame(self, photo):
        """更新视频帧显示"""
        try:
            self.video_label.config(image=photo, text="")
            self.video_label.image = photo  # 保持引用
        except:
            pass
            
    def video_playback_finished(self):
        """视频播放结束处理"""
        self.is_playing = False
        self.play_btn.config(text="播放", state=tk.DISABLED)
        self.stop_video_btn.config(state=tk.DISABLED)
        self.video_label.config(image="", text="播放结束", fg='white')
        self.video_info_label.config(text="播放结束")
            
    def toggle_play(self):
        """切换播放/暂停"""
        if self.is_playing:
            # 暂停播放
            self.is_playing = False
            self.play_btn.config(text="播放")
        else:
            # 恢复播放
            if self.current_video_url:
                self.play_video_from_url(self.current_video_url)
        
    def stop_video(self):
        """停止视频播放"""
        # 停止播放
        self.is_playing = False
        
        # 释放视频资源
        if self.video_cap:
            try:
                self.video_cap.release()
                self.video_cap = None
            except:
                pass
                
        # 停止外部播放器进程（如果存在）
        if self.video_player:
            try:
                self.video_player.terminate()
                self.video_player = None
            except:
                pass
                
        # 重置UI状态
        self.play_btn.config(state=tk.DISABLED, text="播放")
        self.stop_video_btn.config(state=tk.DISABLED)
        self.video_info_label.config(text="未选择视频")
        self.video_label.config(image="", text="点击视频链接开始播放", fg='white')
        
        # 清除当前视频URL
        self.current_video_url = None
        
    def on_closing(self):
        """窗口关闭事件处理"""
        # 停止所有下载和播放
        self.is_downloading = False
        self.stop_video()
        
        # 确认退出
        if self.is_downloading or (self.current_download_thread and self.current_download_thread.is_alive()):
            if messagebox.askyesno("确认退出", "正在下载中，确定要退出吗？"):
                self.root.destroy()
        else:
            self.root.destroy()
            
    def add_url_manually(self):
        """手动添加URL"""
        url = simpledialog.askstring("添加链接", "请输入视频链接:")
        if url and url.strip():
            self.process_text_content(url.strip())
            
    def remove_selected_item(self):
        """删除选中的下载项"""
        selection = self.tree.selection()
        if selection:
            if messagebox.askyesno("确认删除", "确定要删除选中的下载项吗？"):
                for item in selection:
                    # 获取索引并从队列中删除
                    values = self.tree.item(item, 'values')
                    index = int(values[0]) - 1
                    if 0 <= index < len(self.download_queue):
                        del self.download_queue[index]
                    
                    # 从树形视图中删除
                    self.tree.delete(item)
                
                # 重新编号
                self.renumber_items()
                
    def renumber_items(self):
        """重新编号下载项"""
        for i, item in enumerate(self.tree.get_children()):
            values = list(self.tree.item(item, 'values'))
            values[0] = str(i + 1)
            values[1] = f"{i + 1}.mp4"
            self.tree.item(item, values=values)
            
            # 更新队列中的文件名
            if i < len(self.download_queue):
                self.download_queue[i]['filename'] = f"{i + 1}.mp4"
                 
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 选中右键点击的项目
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def play_selected_video(self):
        """播放选中的视频"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if len(values) >= 3:
                url = values[2]
                if url.endswith('...'):
                    index = int(values[0]) - 1
                    if index < len(self.download_queue):
                        url = self.download_queue[index]['url']
                self.play_video_from_url(url)
                
    def copy_selected_url(self):
        """复制选中的链接"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if len(values) >= 3:
                url = values[2]
                if url.endswith('...'):
                    index = int(values[0]) - 1
                    if index < len(self.download_queue):
                        url = self.download_queue[index]['url']
                
                # 复制到剪贴板
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                messagebox.showinfo("成功", "链接已复制到剪贴板")
                
    def redownload_selected(self):
        """重新下载选中的项目"""
        selection = self.tree.selection()
        if selection:
            if messagebox.askyesno("确认", "确定要重新下载选中的项目吗？"):
                for item in selection:
                    values = list(self.tree.item(item, 'values'))
                    values[3] = "等待下载"
                    values[4] = "0%"
                    self.tree.item(item, values=values)
                    
                    # 更新队列状态
                    index = int(values[0]) - 1
                    if index < len(self.download_queue):
                        self.download_queue[index]['status'] = '等待下载'
                        self.download_queue[index]['progress'] = '0%'

def main():
    # 创建主窗口
    root = TkinterDnD.Tk()
    
    # 设置窗口图标（如果存在）
    icon_path = os.path.join(os.getcwd(), "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    # 创建应用
    app = VideoDownloader(root)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()