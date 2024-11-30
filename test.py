import unittest
import os
import tarfile
from io import StringIO
from unittest.mock import patch
import platform
from main import ShellEmulator


class TestShellEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Создание тестового tar-файла
        cls.test_tar_path = "test_vfs.tar"
        
        # Удаление старых файлов перед созданием новых, чтобы избежать ошибок
        if os.path.exists("some.txt"):
            os.remove("some.txt")
        if os.path.exists("test_dir/test_file.txt"):
            os.remove("test_dir/test_file.txt")
        if os.path.exists("test_dir"):
            os.rmdir("test_dir")

        try:
            with tarfile.open(cls.test_tar_path, "w") as tar:
                with open("some.txt", "w") as f:
                    f.write("This is a test file.\n")  # Обратите внимание на новую строку
                tar.add("some.txt", arcname="some.txt")
                
                os.mkdir("test_dir")
                with open("test_dir/test_file.txt", "w") as f:
                    f.write("Hello, World!")
                tar.add("test_dir/test_file.txt", arcname="test_dir/test_file.txt")
        except Exception as e:
            print(e)

        # Инициализация эмулятора с тестовыми параметрами
        cls.emulator = ShellEmulator("test_user", "test_computer", cls.test_tar_path, None)

    @classmethod
    def tearDownClass(cls):
        # Удаление тестового tar-файла после тестов
        if os.path.exists(cls.test_tar_path):
            os.remove(cls.test_tar_path)

    def test_ls_command(self):
        # Проверка вывода команды ls
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.emulator.cur_dir = "/"  # Установить текущую директорию
            self.emulator._ls([])
            output = self.emulator.text_area.get("1.0", "end")
        print(output)
        self.assertIn("some.txt", output)
        self.assertIn("test_dir", output)  # Проверка без слэша


    def test_cd_command(self):
        # Проверка перехода в директорию
        self.emulator._cd(["test_dir"])
        self.assertEqual(self.emulator.cur_dir, "/test_dir")

        # Переход обратно в корень
        self.emulator._cd([".."])
        self.assertEqual(self.emulator.cur_dir, "/")

        # Проверка неправильного перехода
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.emulator._cd(["non_existing_dir"])
            output = self.emulator.text_area.get("1.0", "end").strip()
        self.assertIn("Directory not found.", output)

    def test_tree_command(self):
        # Проверка вывода команды tree
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.emulator._tree()
            output = self.emulator.text_area.get("1.0", "end").strip()
        self.assertIn("some.txt", output)
        self.assertIn("test_dir/", output)
        self.assertIn("test_file.txt", output)

    def test_wc_command(self):
        # Проверка вывода команды wc
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.emulator._wc(["some.txt"])
            output = self.emulator.text_area.get("1.0", "end").strip()
        self.assertIn("1 5 21 some.txt", output)  # Ожидаемое количество строк, слов и байтов

    def test_uname_command(self):
        # Проверка вывода команды uname
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.emulator._uname()
            output = self.emulator.text_area.get("1.0", "end").strip()
        self.assertIn(platform.system(), output)  # Проверка, что вывод содержит имя ОС
        self.assertIn(platform.release(), output)  # Проверка, что вывод содержит версию ОС


if __name__ == "__main__":
    unittest.main()
