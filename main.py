import uuid
from datetime import datetime
import sys

STATUS_ACTIVE = "active"
STATUS_DONE = "done"
SEPARATOR = "<>"
DB_FILE_PATH = "db.txt"

NEW_TASK_ITEM = "1"
COMPLETE_TASK_ITEM = "2"
CHANGE_TASK_ITEM = "3"
SHOW_COMPLETED_TASKS = "4"
ERASE_COMPLETED_TASKS = "5"
WIPE_DATABASE_ITEM = "6"
EXIT_ITEM = "0"
MENU_ITEMS = {
    NEW_TASK_ITEM: "Создать новую задачу",
    COMPLETE_TASK_ITEM: "Завершить задачу",
    CHANGE_TASK_ITEM: "Изменить параметры задачи",
    SHOW_COMPLETED_TASKS: "Показать завершённые задачи",
    ERASE_COMPLETED_TASKS: "Очистить все завершённые задачи",
    WIPE_DATABASE_ITEM: "Полностью очистить базу данных",
    EXIT_ITEM: "Выйти из программы"
}

def print_all_tasks_to_console(tasks):
    counter = 1
    if not tasks:
        print("Список задач пуст.")
        return
    for task_info in tasks:
        print(str(counter) + ": " + task_info)
        counter += 1

def read_from_db():
    try:
        with open(DB_FILE_PATH, "r", encoding="utf8") as file_object:
            file_content = file_object.read()
        return file_content if file_content else ""
    except FileNotFoundError:
        print(f"Файл {DB_FILE_PATH} не найден. Будет создан новый при добавлении задачи.")
        return ""

def append_new_line_to_db(new_line):
    current_content = read_from_db()
    prefix = "\n" if current_content else ""
    with open(DB_FILE_PATH, "a", encoding="utf8") as file_object:
        file_object.write(prefix + new_line)

def rewrite_db(raw_content):
    with open(DB_FILE_PATH, "w", encoding="utf8") as file_object:
        file_object.write(raw_content)

def deserialize_tasks_from_db(raw_content):
    if not raw_content:
        return []
    lines = raw_content.strip().splitlines()
    tasks = [line.split(SEPARATOR) for line in lines if line]

    validated_tasks = []
    for task in tasks:
        if len(task) == 5:
            validated_tasks.append(task)
        else:
            print(f"Предупреждение: Пропущена некорректная строка в базе данных: {SEPARATOR.join(task)}")
    return validated_tasks


def prepare_tasks_list_to_output(raw_tasks_list):
    tasks = []
    for task_info in raw_tasks_list:
        status_symbol = "✓" if task_info[4] == STATUS_ACTIVE else "✕"
        try:
            creation_date = datetime.strptime(task_info[3].split('.')[0], '%Y-%m-%d %H:%M:%S')
            creation_date_str = creation_date.strftime('%d.%m.%Y %H:%M')
        except ValueError:
             creation_date_str = task_info[3]

        task = f"{status_symbol} {task_info[1]} {task_info[2]} (Создана: {creation_date_str})"
        tasks.append(task)
    return tasks

def serialize_task_for_db(task_data):
    return SEPARATOR.join([task_data[0], task_data[1], task_data[2], task_data[3], task_data[4]])

def prepare_new_task_to_save(task_info):
    task_id = uuid.uuid4()
    task_date_created = datetime.now()
    task_to_save = serialize_task_for_db([str(task_id), task_info[0], "["+task_info[1]+"]", str(task_date_created), STATUS_ACTIVE])
    return task_to_save

def get_all_tasks(to_show=None):
    all_tasks_content = read_from_db()
    raw_tasks = deserialize_tasks_from_db(all_tasks_content)

    final_tasks = []
    if to_show:
        final_tasks = [raw_task for raw_task in raw_tasks if raw_task[4] == to_show]
    else:
        final_tasks = raw_tasks

    tasks_list_to_print = prepare_tasks_list_to_output(final_tasks)
    return tasks_list_to_print, final_tasks

def get_active_tasks_raw():
    all_tasks_content = read_from_db()
    raw_tasks = deserialize_tasks_from_db(all_tasks_content)
    active_tasks = [task for task in raw_tasks if task[4] == STATUS_ACTIVE]
    return active_tasks

def parse_new_task_input(raw_data):
    splitted_params = raw_data.split("[")
    task_description = splitted_params[0].strip()
    task_due_date = ""

    if len(splitted_params) > 1:
        task_due_date = "[".join(splitted_params[1:]).strip()
        if task_due_date.endswith("]"):
            task_due_date = task_due_date[:-1].strip()

    return [task_description, task_due_date]

def action_new_task():
    print("#------------------#")
    print("Введите параметры новой задачи (описание [дата исполнения]) или 0, чтобы вернуться:")
    new_task_info = input()

    if new_task_info == "0": return

    if not new_task_info.strip():
        print("Ошибка: Описание задачи не может быть пустым.")
        return

    task_data = parse_new_task_input(new_task_info)
    task_to_save = prepare_new_task_to_save(task_data)
    append_new_line_to_db(task_to_save)
    print("Задача успешно добавлена!")

def action_complete_task():
    print("#------------------#")
    active_tasks_raw = get_active_tasks_raw()

    if not active_tasks_raw:
        print("Нет активных задач для завершения.")
        return

    print("Активные задачи:")
    print_all_tasks_to_console(prepare_tasks_list_to_output(active_tasks_raw))
    print("\nВведите номер задачи для завершения или 0, чтобы вернуться:")

    try:
        task_number_str = input()
        if task_number_str == "0": return
        task_number = int(task_number_str)

        if task_number < 1 or task_number > len(active_tasks_raw):
            print("Ошибка: Неверный номер задачи.")
            return

        task_to_complete_id = active_tasks_raw[task_number - 1][0]

        all_tasks_content = read_from_db()
        all_tasks_raw = deserialize_tasks_from_db(all_tasks_content)

        tasks_output = []
        found = False
        for task in all_tasks_raw:
            if task[0] == task_to_complete_id:
                task[4] = STATUS_DONE
                found = True
            tasks_output.append(serialize_task_for_db(task))

        if found:
            final_string_to_save = "\n".join(tasks_output)
            rewrite_db(final_string_to_save)
            print(f"Задача номер {task_number} успешно завершена.")
        else:
            print("Ошибка: Не удалось найти задачу для завершения (возможно, база данных изменилась).")

    except ValueError:
        print("Ошибка: Введите числовое значение номера задачи.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

    input("Нажмите Enter для возврата в меню...")


def action_change_task_params():
    print("#------------------#")
    active_tasks_raw = get_active_tasks_raw()

    if not active_tasks_raw:
        print("Нет активных задач для изменения.")
        input("Нажмите Enter для возврата в меню...")
        return

    print("Активные задачи:")
    print_all_tasks_to_console(prepare_tasks_list_to_output(active_tasks_raw))
    print("\nВведите номер задачи для изменения её параметров или 0, чтобы вернуться:")

    try:
        task_number_str = input()
        if task_number_str == "0": return
        task_number = int(task_number_str)

        if task_number < 1 or task_number > len(active_tasks_raw):
            print("Ошибка: Неверный номер задачи.")
            input("Нажмите Enter для возврата в меню...")
            return

        task_to_change_index = task_number - 1
        task_to_change_id = active_tasks_raw[task_to_change_index][0]
        current_description = active_tasks_raw[task_to_change_index][1]
        current_due_date_content = active_tasks_raw[task_to_change_index][2].strip('[]')
        current_due_date_str_with_brackets = active_tasks_raw[task_to_change_index][2]


        print(f"\nИзменение задачи №{task_number}:")
        print(f"Текущее описание: {current_description}")
        print(f"Текущая дата исполнения: {current_due_date_content}")

        print("Введите новое описание (или нажмите Enter, чтобы оставить текущее):")
        new_description_input = input().strip()
        print("Введите новую дату исполнения (или нажмите Enter, чтобы оставить текущую):")
        new_due_date_input = input().strip()

        description_changed = bool(new_description_input)
        due_date_changed = bool(new_due_date_input)

        if not description_changed and not due_date_changed:
             if new_due_date_input == '' and current_due_date_content != '':
                 due_date_changed = True
             else:
                 print("Никаких изменений не внесено.")
                 input("Нажмите Enter для возврата в меню...")
                 return

        final_description = new_description_input if description_changed else current_description
        final_due_date_str = ""
        if due_date_changed:
            final_due_date_str = f"[{new_due_date_input}]"
        else:
            final_due_date_str = current_due_date_str_with_brackets

        all_tasks_content = read_from_db()
        all_tasks_raw = deserialize_tasks_from_db(all_tasks_content)

        tasks_output = []
        found_and_updated = False
        for task in all_tasks_raw:
            if task[0] == task_to_change_id:
                task[1] = final_description
                task[2] = final_due_date_str
                found_and_updated = True
            tasks_output.append(serialize_task_for_db(task))

        if found_and_updated:
            final_string_to_save = "\n".join(tasks_output)
            rewrite_db(final_string_to_save)
            print(f"Параметры задачи номер {task_number} успешно изменены.")
        else:
             print("Ошибка: Не удалось найти задачу для изменения (возможно, база данных изменилась).")

    except ValueError:
        print("Ошибка: Введите числовое значение номера задачи.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

    input("Нажмите Enter для возврата в меню...")


def show_completed_tasks():
    print("#------------------#")
    print("Завершённые задачи:")
    tasks_list_to_print, _ = get_all_tasks(STATUS_DONE)
    print_all_tasks_to_console(tasks_list_to_print)
    print("#------------------#")
    input("Нажмите Enter для возврата в меню...")

def erase_completed_tasks():
    print("#------------------#")
    print("Очищаем базу от завершённых задач...")

    all_tasks_content = read_from_db()
    all_tasks_raw = deserialize_tasks_from_db(all_tasks_content)

    active_tasks_to_keep = [serialize_task_for_db(task) for task in all_tasks_raw if task[4] == STATUS_ACTIVE]
    removed_count = len(all_tasks_raw) - len(active_tasks_to_keep)

    if removed_count > 0:
        final_string_to_save = "\n".join(active_tasks_to_keep)
        rewrite_db(final_string_to_save)
        print(f"Успешно удалено завершённых задач: {removed_count}")
    else:
        print("Нет завершённых задач для удаления.")

    print("#------------------#")
    input("Нажмите Enter для возврата в меню...")

def action_wipe_database():
    print("#------------------#")
    print("!!! ВНИМАНИЕ !!!")
    print("Это действие полностью удалит ВСЕ задачи (активные и завершенные).")
    confirmation = input("Вы уверены, что хотите продолжить? (введите 'да' для подтверждения): ").lower()

    if confirmation == 'да':
        try:
            rewrite_db("")
            print("База данных успешно очищена.")
        except Exception as e:
            print(f"Произошла ошибка при очистке базы данных: {e}")
    else:
        print("Очистка базы данных отменена.")

    print("#------------------#")
    input("Нажмите Enter для возврата в меню...")

def show_main_menu():
    print("#------------------#")
    print("Выберите действие:")
    menu_text = ""
    sorted_keys = sorted(MENU_ITEMS.keys(), key=lambda x: int(x) if x != '0' else float('inf'))
    for key in sorted_keys:
        menu_text = menu_text + key + " – " + MENU_ITEMS[key] + "\n"

    print(menu_text)
    print("Номер действия: ", end="")
    choice = input()

    if choice == NEW_TASK_ITEM:
        action_new_task()
    elif choice == COMPLETE_TASK_ITEM:
        action_complete_task()
    elif choice == CHANGE_TASK_ITEM:
        action_change_task_params()
    elif choice == SHOW_COMPLETED_TASKS:
        show_completed_tasks()
    elif choice == ERASE_COMPLETED_TASKS:
        erase_completed_tasks()
    elif choice == WIPE_DATABASE_ITEM:
        action_wipe_database()
    elif choice == EXIT_ITEM:
        print("Выход из программы...")
        sys.exit()
    else:
        print("Неизвестная команда")
        input("Нажмите Enter для продолжения...")


def main():
    while True:
        tasks_list_to_print, _ = get_all_tasks(STATUS_ACTIVE)
        print("\n#---------- АКТУАЛЬНЫЕ ЗАДАЧИ ----------#")
        print_all_tasks_to_console(tasks_list_to_print)
        show_main_menu()

if __name__ == "__main__":
    main()