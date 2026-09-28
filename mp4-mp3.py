import os
import sys
import time
import threading
from pathlib import Path
from colorama import init, Fore, Style

# Инициализация Colorama с автосбросом цветов
init(autoreset=True)

animation_running = False
# Глобальный словарь для хранения результатов последнего поиска
last_search_results = {}

def spinner_animation(message: str):
    """Анимация спиннера в стиле CMD [ / \\ - | ]"""
    symbols = ['/', '\\', '-', '|']
    i = 0
    while animation_running:
        sys.stdout.write(f"\r{symbols[i % 4]} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * (len(message) + 4) + "\r")
    sys.stdout.flush()

def search_files(drive_letter: str):
    """Поиск MP4 файлов на указанном диске с выводом таблицы в стиле CMD."""
    global animation_running, last_search_results
    
    drive_path = Path(f"{drive_letter.upper()}:\\")
    if not drive_path.exists():
        print(f"Ошибка: Диск {drive_letter.upper()}: не найден.")
        return

    found_files = []
    last_search_results.clear()
    animation_running = True
    
    spinner_thread = threading.Thread(target=spinner_animation, args=(f"[ In process ] Поиск в {drive_letter.upper()}:",))
    spinner_thread.start()

    try:
        for root, dirs, files in os.walk(drive_path):
            for file in files:
                if file.lower().endswith('.mp4'):
                    full_path = Path(root) / file
                    try:
                        stat = full_path.stat()
                        created_time = time.strftime('%d.%m.%Y  %H:%M', time.localtime(stat.st_mtime))
                        found_files.append({
                            'name': file,
                            'path': full_path,
                            'time': created_time
                        })
                        last_search_results[file.lower()] = full_path
                    except (PermissionError, FileNotFoundError):
                        continue
    finally:
        animation_running = False
        spinner_thread.join()

    if found_files:
        print()
        print(f"{'Создание/Время':<20} {'Имя':<35} {'Расположение'}")
        print("-" * 85)
        for f in found_files:
            print(f"{f['time']:<20} {f['name']:<35} {f['path'].parent}")
        print()
    else:
        print(f"\nФайлы MP4 на диске {drive_letter.upper()}: не найдены.")

def convert_mp4_to_mp3(file_name: str):
    """Поиск и конвертация файла."""
    file_name = file_name.strip('"\'')
    
    if file_name.lower() in last_search_results:
        input_path = last_search_results[file_name.lower()]
    else:
        input_path = Path(file_name)
        if not input_path.is_absolute():
            input_path = Path(os.getcwd()) / input_path

    if not input_path.exists():
        print(f"Ошибка: Файл '{file_name}' не найден ни в результатах поиска, ни в текущей папке.")
        return

    if input_path.suffix.lower() != '.mp4':
        print("Ошибка: Поддерживаются только файлы с расширением .mp4")
        return

    output_path = input_path.with_suffix('.mp3')
    print(f"\nНачало конвертации видео: {input_path.name}")
    print("Загрузка медиа-движка...")
    
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        
        with VideoFileClip(str(input_path)) as video:
            if video.audio is None:
                print("Ошибка: В видеофайле отсутствует аудиодорожка.")
                return
            video.audio.write_audiofile(str(output_path), logger=None)
            
        print(f"\n[Успех] Файл успешно конвертирован!")
        print(f"Аудио сохранено: {output_path}\n")
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}\n")

def main():
    # ИСПРАВЛЕНО: Разделены склеенные вызовы функций print
    print(f"{Fore.GREEN}{Style.BRIGHT}=== Converter MP4 in MP3 ===")
    print(f"{Fore.CYAN}{Style.BRIGHT}Доступные команды: search [диск]: | convert [имя_файла.mp4] | exit\n")

    while True:
        try:
            # Оранжевое приглашение к вводу
            prompt = f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}convert> {Style.RESET_ALL}"
            user_input = input(prompt).strip()
            
            if not user_input:
                continue

            if user_input.lower() == 'exit':
                break
                
            elif user_input.lower() == 'cls':
                os.system('cls' if os.name == 'nt' else 'clear')
                
            elif user_input.lower() == 'dir':
                os.system('dir' if os.name == 'nt' else 'ls -la')

            elif user_input.lower().startswith('cd '):
                target_dir = user_input[3:].strip()
                try:
                    os.chdir(target_dir)
                except FileNotFoundError:
                    print("Системе не удается найти указанный путь.")
                except Exception as e:
                    print(f"Ошибка изменения папки: {e}")

            elif user_input.lower().startswith('search '):
                parts = user_input.split()
                if len(parts) == 2 and parts[1].endswith(':'):
                    drive_letter = parts[1][:-1]
                    search_files(drive_letter)
                else:
                    print("Неправильный синтаксис команды. Пример: search f:")

            elif user_input.lower().startswith('convert '):
                # ИСПРАВЛЕНО: Срез [8:] корректно берет всё имя файла, даже если оно с пробелами
                file_name = user_input[8:].strip()
                if file_name:
                    convert_mp4_to_mp3(file_name)
                else:
                    print("Ошибка: необходимо указать имя файла. Пример: convert movie.mp4")

            else:
                os.system(user_input)
                
        except KeyboardInterrupt:
            print("\nОперация прервана пользователем.")
        except Exception as e:
            print(f"Ошибка командного процессора: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as fatal_err:
        print(f"\nКРИТИЧЕСКИЙ СБОЙ ПРОГРАММЫ: {fatal_err}")
        input("\nНажмите Enter, чтобы закрыть окно...")
