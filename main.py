import argparse
import tkinter as tk
import tarfile
import os
import platform


class Node:
    def __init__(self, name: str, is_dir: bool = False):
        self.name = name
        self.is_dir = is_dir
        self.children = {}

    def add_child(self, child_node):
        self.children[child_node.name] = child_node

    def get_child(self, name):
        return self.children.get(name)

    def has_children(self):
        return bool(self.children)


class ShellEmulator:
    def __init__(self, username, computername, fs_path, script_path):
        self.username = username
        self.computername = computername
        self.fs_path = fs_path
        self.script_path = script_path
        self.cur_dir = "/"
        self.root_node = Node("/", is_dir=True)
        self._open_fs()
        self._build_tree()
        self._init_gui()

    def _open_fs(self):
        if not os.path.exists(self.fs_path):
            raise FileNotFoundError(f"Архив не найден по указанному пути: {self.fs_path}")
        self.fs = tarfile.open(self.fs_path, "r")

    
    def _build_tree(self):
        file_list = self.fs.getnames()

        for file_path in file_list:
            # Разбиваем путь на компоненты
            parts = file_path.strip("/").split("/")
            current_node = self.root_node

            for idx, part in enumerate(parts):
                # Определяем, является ли узел директорией
                # Если это не последний элемент или он не имеет расширения, то это директория
                is_dir = (idx != len(parts) - 1) or not os.path.splitext(part)[1]

                if part not in current_node.children:
                    new_node = Node(part, is_dir=is_dir)
                    current_node.add_child(new_node)
                current_node = current_node.get_child(part)



    def _init_gui(self):
        self.root = tk.Tk()
        self.root.title("Shell Emulator")
        self.text_area = tk.Text(self.root, height=20, width=80)
        self.text_area.pack()
        self.text_area.bind("<Return>", self._enter_handler)
        self._print_prompt()

    def _print_prompt(self):
        prompt = f"{self.username}@{self.computername}:{self.cur_dir}$ "
        self.text_area.insert(tk.END, prompt)
        self.text_area.mark_set("insert", tk.END)
    
    def _enter_handler(self, event=None):
        lines = self.text_area.get("1.0", tk.END).splitlines()
        command = lines[-1].split(f"{self.username}@{self.computername}:{self.cur_dir}$ ")[-1].strip()
        self._execute_command(command)
        self._print_prompt()
        return "break"

    def _execute_command(self, command):
        parts = command.split()
        cmd = parts[0] if parts else ""
        args = parts[1:]

        if cmd == "ls":
            self._ls(args)
        elif cmd == "cd":
            self._cd(args)
        elif cmd == "tree":
            self._tree()
        elif cmd == "wc":
            self._wc(args)
        elif cmd == "uname":
            self._uname()
        elif cmd == "exit":
            self.root.quit()
        else:
            self.text_area.insert(tk.END, f"\nКоманда '{cmd}' не найдена")
        self.text_area.insert(tk.END, "\n")
    def _ls(self, args):
        path = self.cur_dir if not args else args[0]
        node = self._find_node(path)
        if node and node.has_children():
            self.text_area.insert(tk.END, "\n" + "\n".join(sorted(node.children.keys())))
        else:
            self.text_area.insert(tk.END, "\nDirectory not found.")

    def _cd(self, args):
        if not args:
            return
        path = args[0]
        if path == "/":
            self.cur_dir = "/"
        elif path == "..":
            self.cur_dir = "/".join(self.cur_dir.strip("/").split("/")[:-1]) or "/"
        else:
            node = self._find_node(path)
            if node and node.is_dir:
                self.cur_dir = os.path.join(self.cur_dir, path).replace("//", "/")
            else:
                self.text_area.insert(tk.END, "\nDirectory not found.")

    def _tree(self):
        tree_str = self._print_tree(self.root_node)
        self.text_area.insert(tk.END, "\n" + tree_str)

    def _wc(self, args):
        if not args:
            return
        # Combine cur_dir with provided path argument
        path = os.path.normpath(os.path.join(self.cur_dir, args[0]))
        # Strip leading slash for compatibility with tarfile paths
        tar_path = path.lstrip("/")
        if tar_path not in self.fs.getnames():
            self.text_area.insert(tk.END, "\nFile not found.")
            return
        file_obj = self.fs.extractfile(tar_path)
        if file_obj:
            content = file_obj.read().decode("utf-8")
            lines = len(content.splitlines())
            words = len(content.split())
            bytes_size = len(content.encode("utf-8"))
            # Display only the relative path as expected by the test
            relative_path = os.path.basename(path)
            self.text_area.insert(tk.END, f"\n{lines} {words} {bytes_size} {relative_path}")

    def _uname(self):
        self.text_area.insert(tk.END, f"\n{platform.system()} {platform.release()}")

    def _print_tree(self, node, prefix=""):
        tree_str = f"{prefix}{node.name}/\n" if node.is_dir else f"{prefix}{node.name}\n"
        sorted_children = sorted(node.children.values(), key=lambda n: (not n.is_dir, n.name))
        for idx, child in enumerate(sorted_children):
            connector = "|__ " if idx == len(sorted_children) - 1 else "|-- "
            tree_str += self._print_tree(child, prefix + (connector if idx == len(sorted_children) - 1 else "│   "))
        return tree_str

    def _find_node(self, path):
        parts = path.strip("/").split("/")
        current_node = self.root_node
        for part in parts:
            if not part:
                continue
            current_node = current_node.get_child(part)
            if not current_node:
                return None
        return current_node

    def start(self):
        self.root.mainloop()


def parse_args():
    parser = argparse.ArgumentParser(description="Shell Emulator")
    parser.add_argument('-u', '--username', required=True, help="Имя пользователя для показа в приглашении к вводу")
    parser.add_argument('-c', '--computername', required=True, help="Имя компьютера для показа в приглашении к вводу")
    parser.add_argument('-p', '--path', required=True, help="Путь к архиву виртуальной файловой системы")
    parser.add_argument('-s', '--script', required=False, help="Путь к стартовому скрипту")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    emulator = ShellEmulator(args.username, args.computername, args.path, args.script)
    emulator.start()
