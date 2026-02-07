# universal_file_searcher.py
import os
import re
import zipfile
import tarfile
from pathlib import Path
from typing import List, Dict, Union, Optional
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading

try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    RAR_SUPPORT = False
    print("Для работы с RAR файлами установите: pip install rarfile")

class UniversalFileSearcher:
    def __init__(self):
        self.supported_extensions = {
            'txt': self._read_text_file,
            'csv': self._read_text_file,
            'json': self._read_text_file,
            'xml': self._read_text_file,
            'html': self._read_text_file,
            'py': self._read_text_file,
            'js': self._read_text_file,
            'md': self._read_text_file,
            'log': self._read_text_file,
            'ini': self._read_text_file,
            'cfg': self._read_text_file,
            'zip': self._read_zip_file,
            'tar': self._read_tar_file,
            'gz': self._read_tar_file,
        }
        
        if RAR_SUPPORT:
            self.supported_extensions['rar'] = self._read_rar_file
    
    def _read_text_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """Чтение текстового файла"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    return f.read()
            except:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except:
                    return ""
        except Exception as e:
            print(f"Ошибка чтения файла {file_path}: {e}")
            return ""
    
    def _read_zip_file(self, file_path: str) -> Dict[str, str]:
        """Чтение ZIP архива"""
        content = {}
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir():
                        # Проверяем расширение файла
                        ext = os.path.splitext(file_info.filename)[1][1:].lower()
                        if ext in ['txt', 'csv', 'json', 'xml', 'html', 'py', 'js', 'md', 'log']:
                            try:
                                with zip_ref.open(file_info) as file:
                                    text = file.read().decode('utf-8', errors='ignore')
                                    content[file_info.filename] = text
                            except:
                                continue
        except Exception as e:
            print(f"Ошибка чтения ZIP архива {file_path}: {e}")
        return content
    
    def _read_rar_file(self, file_path: str) -> Dict[str, str]:
        """Чтение RAR архива"""
        if not RAR_SUPPORT:
            return {}
        
        content = {}
        try:
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                for file_info in rar_ref.infolist():
                    if not file_info.is_dir():
                        ext = os.path.splitext(file_info.filename)[1][1:].lower()
                        if ext in ['txt', 'csv', 'json', 'xml', 'html', 'py', 'js', 'md', 'log']:
                            try:
                                with rar_ref.open(file_info) as file:
                                    text = file.read().decode('utf-8', errors='ignore')
                                    content[file_info.filename] = text
                            except:
                                continue
        except Exception as e:
            print(f"Ошибка чтения RAR архива {file_path}: {e}")
        return content
    
    def _read_tar_file(self, file_path: str) -> Dict[str, str]:
        """Чтение TAR архива"""
        content = {}
        try:
            mode = 'r:gz' if file_path.endswith('.gz') else 'r'
            with tarfile.open(file_path, mode) as tar_ref:
                for member in tar_ref.getmembers():
                    if member.isfile():
                        ext = os.path.splitext(member.name)[1][1:].lower()
                        if ext in ['txt', 'csv', 'json', 'xml', 'html', 'py', 'js', 'md', 'log']:
                            try:
                                f = tar_ref.extractfile(member)
                                if f:
                                    text = f.read().decode('utf-8', errors='ignore')
                                    content[member.name] = text
                            except:
                                continue
        except Exception as e:
            print(f"Ошибка чтения TAR архива {file_path}: {e}")
        return content
    
    def read_file(self, file_path: str) -> Union[str, Dict[str, str]]:
        """Чтение файла по его расширению"""
        if not os.path.exists(file_path):
            return ""
        
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        
        if ext in ['zip', 'rar', 'tar', 'gz']:
            if ext == 'zip':
                return self._read_zip_file(file_path)
            elif ext == 'rar' and RAR_SUPPORT:
                return self._read_rar_file(file_path)
            elif ext in ['tar', 'gz']:
                return self._read_tar_file(file_path)
            return {}
        elif ext in self.supported_extensions:
            return self._read_text_file(file_path)
        else:
            # Пытаемся прочитать как текстовый файл
            try:
                return self._read_text_file(file_path)
            except:
                return ""
    
    def search_in_text(self, text: str, pattern: str, 
                      case_sensitive: bool = False, 
                      regex: bool = False) -> List[Dict]:
        """Поиск в тексте"""
        results = []
        
        if not text:
            return results
        
        lines = text.split('\n')
        
        if regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                regex_pattern = re.compile(pattern, flags)
                for i, line in enumerate(lines, 1):
                    matches = regex_pattern.finditer(line)
                    for match in matches:
                        results.append({
                            'line': i,
                            'position': match.start(),
                            'match': match.group(),
                            'context': self._get_context(line, match.start(), match.end()),
                            'full_line': line
                        })
            except re.error as e:
                print(f"Ошибка в регулярном выражении: {e}")
                return []
        else:
            for i, line in enumerate(lines, 1):
                if case_sensitive:
                    line_to_search = line
                    pattern_to_use = pattern
                else:
                    line_to_search = line.lower()
                    pattern_to_use = pattern.lower()
                
                start = 0
                pattern_len = len(pattern)
                while True:
                    pos = line_to_search.find(pattern_to_use, start)
                    if pos == -1:
                        break
                    
                    results.append({
                        'line': i,
                        'position': pos,
                        'match': line[pos:pos + pattern_len] if case_sensitive else line[pos:pos + pattern_len],
                        'context': self._get_context(line, pos, pos + pattern_len),
                        'full_line': line
                    })
                    start = pos + 1
        
        return results
    
    def _get_context(self, line: str, start: int, end: int, 
                    context_chars: int = 50) -> str:
        """Получение контекста вокруг найденного совпадения"""
        context_start = max(0, start - context_chars)
        context_end = min(len(line), end + context_chars)
        
        context = line[context_start:context_end]
        if context_start > 0:
            context = "..." + context
        if context_end < len(line):
            context = context + "..."
        
        return context
    
    def search_in_file(self, file_path: str, pattern: str, 
                      case_sensitive: bool = False,
                      regex: bool = False) -> Dict:
        """Поиск в файле или архиве"""
        results = {
            'file': file_path,
            'matches': [],
            'archive_contents': [],
            'is_archive': False,
            'match_count': 0
        }
        
        try:
            content = self.read_file(file_path)
            
            if isinstance(content, dict):  # Это архив
                results['is_archive'] = True
                for filename, text in content.items():
                    if text:
                        file_results = self.search_in_text(text, pattern, 
                                                         case_sensitive, regex)
                        if file_results:
                            results['archive_contents'].append({
                                'file_in_archive': filename,
                                'matches': file_results,
                                'match_count': len(file_results)
                            })
                            results['match_count'] += len(file_results)
            else:  # Это обычный файл
                file_results = self.search_in_text(content, pattern, 
                                                 case_sensitive, regex)
                results['matches'] = file_results
                results['match_count'] = len(file_results)
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def search_in_directory(self, directory: str, pattern: str,
                           file_pattern: str = "*",
                           recursive: bool = True,
                           case_sensitive: bool = False,
                           regex: bool = False) -> List[Dict]:
        """Поиск во всех файлах директории"""
        all_results = []
        
        dir_path = Path(directory)
        
        if recursive:
            files = list(dir_path.rglob(file_pattern))
        else:
            files = list(dir_path.glob(file_pattern))
        
        total_files = len(files)
        processed = 0
        
        for file_path in files:
            if file_path.is_file():
                processed += 1
                if processed % 10 == 0:
                    print(f"Обработано {processed}/{total_files} файлов...")
                
                ext = file_path.suffix[1:].lower()
                if ext in self.supported_extensions or ext == '':
                    result = self.search_in_file(str(file_path), pattern,
                                               case_sensitive, regex)
                    if result.get('match_count', 0) > 0:
                        all_results.append(result)
        
        return all_results


class FileSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Универсальный поиск по файлам")
        self.root.geometry("1000x800")
        
        self.searcher = UniversalFileSearcher()
        self.search_thread = None
        self.current_results = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка расширения окна
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="🔍 Универсальный поиск по файлам", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Поисковая строка
        ttk.Label(main_frame, text="Что искать:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.search_entry = ttk.Entry(main_frame, width=60)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # Путь к файлу/директории
        ttk.Label(main_frame, text="Где искать:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(0, weight=1)
        
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(path_frame, text="Обзор...", command=self.browse_path).grid(row=0, column=1)
        
        # Опции поиска
        options_frame = ttk.LabelFrame(main_frame, text="Опции поиска", padding="10")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.case_var = tk.BooleanVar()
        self.regex_var = tk.BooleanVar()
        self.recursive_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Учитывать регистр", 
                       variable=self.case_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Регулярные выражения", 
                       variable=self.regex_var).grid(row=0, column=1, sticky=tk.W, padx=20)
        ttk.Checkbutton(options_frame, text="Рекурсивный поиск", 
                       variable=self.recursive_var).grid(row=0, column=2, sticky=tk.W)
        
        # Тип поиска
        ttk.Label(main_frame, text="Тип поиска:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.search_type = tk.StringVar(value="dir")
        search_type_frame = ttk.Frame(main_frame)
        search_type_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(search_type_frame, text="Один файл", 
                       variable=self.search_type, value="file").pack(side=tk.LEFT)
        ttk.Radiobutton(search_type_frame, text="Директория", 
                       variable=self.search_type, value="dir").pack(side=tk.LEFT, padx=20)
        ttk.Radiobutton(search_type_frame, text="По шаблону", 
                       variable=self.search_type, value="pattern").pack(side=tk.LEFT)
        
        # Шаблон файлов (скрыт по умолчанию)
        self.pattern_label = ttk.Label(main_frame, text="Шаблон файлов:")
        self.pattern_entry = ttk.Entry(main_frame, width=30)
        self.pattern_entry.insert(0, "*.txt")
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Начать поиск", 
                  command=self.start_search, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить результаты", 
                  command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт результатов", 
                  command=self.export_results).pack(side=tk.LEFT, padx=5)
        
        # Создание стиля для акцентной кнопки
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='white', background='#0078D7')
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Панель с вкладками для результатов
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Вкладка с таблицей результатов
        table_frame = ttk.Frame(self.notebook)
        self.notebook.add(table_frame, text="Результаты поиска")
        
        # Treeview для результатов
        self.tree = ttk.Treeview(table_frame, columns=('file', 'matches', 'type'), 
                                show='headings', height=20)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        self.tree.heading('file', text='Файл')
        self.tree.heading('matches', text='Совпадений')
        self.tree.heading('type', text='Тип')
        
        self.tree.column('file', width=400)
        self.tree.column('matches', width=100)
        self.tree.column('type', width=200)
        
        # Вкладка с деталями
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Детали совпадений")
        
        self.details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к поиску")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Привязка события выбора в treeview
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Привязка изменения типа поиска
        self.search_type.trace('w', self.on_search_type_change)
        
        # Примеры поиска
        example_frame = ttk.LabelFrame(main_frame, text="Примеры поиска", padding="5")
        example_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        examples = [
            "текст - обычный поиск",
            "[A-Za-z]+@[A-Za-z]+\\.[A-Za-z]+ - email (рег. выражение)",
            "\\d{3}-\\d{2}-\\d{2} - дата (рег. выражение)"
        ]
        
        for i, example in enumerate(examples):
            ttk.Label(example_frame, text=example, font=('Arial', 9)).grid(row=0, column=i, padx=10)
    
    def on_search_type_change(self, *args):
        if self.search_type.get() == 'pattern':
            self.pattern_label.grid(row=5, column=0, sticky=tk.W, pady=5)
            self.pattern_entry.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        else:
            self.pattern_label.grid_remove()
            self.pattern_entry.grid_remove()
    
    def browse_path(self):
        if self.search_type.get() == 'file':
            filetypes = [
                ("Все файлы", "*.*"),
                ("Текстовые файлы", "*.txt *.csv *.json *.xml *.html *.log"),
                ("Архивы", "*.zip *.rar *.tar *.gz"),
                ("Python файлы", "*.py"),
                ("Документы", "*.md *.ini *.cfg")
            ]
            filename = filedialog.askopenfilename(filetypes=filetypes)
            if filename:
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, filename)
        else:
            directory = filedialog.askdirectory()
            if directory:
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, directory)
    
    def start_search(self):
        pattern = self.search_entry.get().strip()
        if not pattern:
            messagebox.showwarning("Внимание", "Введите строку для поиска!")
            return
        
        path = self.path_entry.get().strip()
        if not path:
            messagebox.showwarning("Внимание", "Укажите путь для поиска!")
            return
        
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", f"Путь не существует: {path}")
            return
        
        # Очистка предыдущих результатов
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.details_text.delete(1.0, tk.END)
        self.current_results = []
        
        # Запуск поиска в отдельном потоке
        self.progress.start()
        self.status_var.set("Выполняется поиск...")
        
        self.search_thread = threading.Thread(
            target=self.perform_search,
            args=(pattern, path)
        )
        self.search_thread.daemon = True
        self.search_thread.start()
        
        # Проверка завершения потока
        self.root.after(100, self.check_thread)
    
    def perform_search(self, pattern, path):
        try:
            search_type = self.search_type.get()
            
            if search_type == 'file':
                results = [self.searcher.search_in_file(
                    path, pattern,
                    self.case_var.get(),
                    self.regex_var.get()
                )]
            elif search_type == 'dir':
                results = self.searcher.search_in_directory(
                    path, pattern,
                    recursive=self.recursive_var.get(),
                    case_sensitive=self.case_var.get(),
                    regex=self.regex_var.get()
                )
            else:  # pattern
                file_pattern = self.pattern_entry.get().strip() or "*"
                results = self.searcher.search_in_directory(
                    path, pattern,
                    file_pattern=file_pattern,
                    recursive=self.recursive_var.get(),
                    case_sensitive=self.case_var.get(),
                    regex=self.regex_var.get()
                )
            
            self.current_results = results
            
            # Обновление UI из главного потока
            self.root.after(0, self.display_results, results)
            
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
    
    def display_results(self, results):
        total_files = len(results)
        total_matches = 0
        
        for result in results:
            if result.get('is_archive', False):
                matches_count = result.get('match_count', 0)
                file_type = f"Архив ({len(result.get('archive_contents', []))} файлов)"
            else:
                matches_count = result.get('match_count', 0)
                file_type = "Файл"
            
            if matches_count > 0:
                total_matches += matches_count
                
                # Определяем цвет строки
                tag = 'archive' if result.get('is_archive', False) else 'file'
                
                self.tree.insert('', 'end', 
                               values=(result['file'], matches_count, file_type),
                               tags=(tag,))
        
        # Настройка тегов для цветов
        self.tree.tag_configure('file', background='#f0f0f0')
        self.tree.tag_configure('archive', background='#e0f7fa')
        
        self.status_var.set(f"Найдено {total_matches} совпадений в {total_files} файлах")
    
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item_idx = self.tree.index(selection[0])
        if item_idx < len(self.current_results):
            result = self.current_results[item_idx]
            self.display_result_details(result)
    
    def display_result_details(self, result):
        self.details_text.delete(1.0, tk.END)
        
        self.details_text.insert(tk.END, f"Файл: {result['file']}\n", 'header')
        self.details_text.insert(tk.END, f"Всего совпадений: {result.get('match_count', 0)}\n\n")
        
        if result.get('is_archive', False):
            for arc_file in result.get('archive_contents', []):
                self.details_text.insert(tk.END, f"\nФайл в архиве: {arc_file['file_in_archive']}\n", 'subheader')
                self.details_text.insert(tk.END, f"Совпадений: {arc_file['match_count']}\n")
                
                for match in arc_file['matches'][:10]:  # Показываем первые 10 совпадений
                    self.details_text.insert(tk.END, f"\n  Строка {match['line']}, позиция {match['position']}:\n")
                    self.details_text.insert(tk.END, f"  {match['context']}\n")
                    self.details_text.insert(tk.END, f"  → Найдено: '{match['match']}'\n")
                
                if arc_file['match_count'] > 10:
                    self.details_text.insert(tk.END, f"\n  ... и еще {arc_file['match_count'] - 10} совпадений\n")
        else:
            for match in result.get('matches', [])[:20]:  # Показываем первые 20 совпадений
                self.details_text.insert(tk.END, f"\nСтрока {match['line']}, позиция {match['position']}:\n")
                self.details_text.insert(tk.END, f"{match['context']}\n")
                self.details_text.insert(tk.END, f"→ Найдено: '{match['match']}'\n")
            
            if result.get('match_count', 0) > 20:
                self.details_text.insert(tk.END, f"\n... и еще {result['match_count'] - 20} совпадений\n")
        
        # Настройка тегов для форматирования
        self.details_text.tag_configure('header', font=('Arial', 11, 'bold'))
        self.details_text.tag_configure('subheader', font=('Arial', 10, 'bold'), foreground='blue')
    
    def show_error(self, error_msg):
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error_msg}")
        self.status_var.set("Ошибка при выполнении поиска")
    
    def check_thread(self):
        if self.search_thread and self.search_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.progress.stop()
            if "Найдено" not in self.status_var.get():
                self.status_var.set("Поиск завершен")
    
    def clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.details_text.delete(1.0, tk.END)
        self.current_results = []
        self.status_var.set("Готов к поиску")
    
    def export_results(self):
        if not self.current_results:
            messagebox.showwarning("Внимание", "Нет результатов для экспорта!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовый файл", "*.txt"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Результаты поиска\n")
                    f.write(f"Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Строка поиска: {self.search_entry.get()}\n")
                    f.write(f"Путь: {self.path_entry.get()}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for result in self.current_results:
                        f.write(f"\nФайл: {result['file']}\n")
                        f.write(f"Совпадений: {result.get('match_count', 0)}\n")
                        
                        if result.get('is_archive', False):
                            for arc_file in result.get('archive_contents', []):
                                f.write(f"\n  Файл в архиве: {arc_file['file_in_archive']}\n")
                                for match in arc_file['matches']:
                                    f.write(f"    Строка {match['line']}: {match['full_line']}\n")
                        else:
                            for match in result.get('matches', []):
                                f.write(f"  Строка {match['line']}: {match['full_line']}\n")
                        
                        f.write("\n" + "-" * 80 + "\n")
                
                messagebox.showinfo("Успех", f"Результаты экспортированы в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать результаты:\n{e}")


def main():
    """Запуск GUI приложения"""
    import time
    
    root = tk.Tk()
    app = FileSearchGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()