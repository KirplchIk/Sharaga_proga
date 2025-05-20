import uuid
from datetime import datetime
import sys
import os

STATUS_ACTIVE = "✕"
STATUS_DONE = "✓"
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

def validate_due_date_content(date_content_str):
    if not date_content_str:
        return ""
    try:
        datetime.strptime(date_content_str, '%d.%m.%Y %H:%M')
        return date_content_str
    except ValueError:
        return False

class Task:
    def __init__(self, task_id, description, due_date_str, creation_date, status):
        self._task_id = str(task_id)
        self.description = description
        self.due_date_str = due_date_str

        if isinstance(creation_date, datetime):
            self._creation_date = creation_date
        elif isinstance(creation_date, str):
            self._creation_date = datetime.strptime(creation_date, '%Y-%m-%d %H:%M:%S.%f')
        else:
            self._creation_date = datetime.now()
            print(f"Предупреждение: Некорректный тип creation_date для задачи {self._task_id}, используется текущее время.")
        self.status = status

    @property
    def task_id(self):
        return self._task_id

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def due_date(self):
        if self.due_date_str and self.due_date_str.startswith("[") and self.due_date_str.endswith("]"):
            date_content = self.due_date_str[1:-1].strip()
            if not date_content:
                return None
            return datetime.strptime(date_content, '%d.%m.%Y %H:%M')
        return None

    @property
    def is_overdue(self):
        if self.status == STATUS_ACTIVE:
            parsed_due_date = self.due_date
            if parsed_due_date:
                return datetime.now() > parsed_due_date
        return False

    def to_db_string(self):
        return SEPARATOR.join([
            self._task_id,
            self.description,
            self.due_date_str,
            self._creation_date.strftime('%Y-%m-%d %H:%M:%S.%f'),
            self.status
        ])

    @classmethod
    def from_db_parts(cls, parts):
        if len(parts) == 5:
            task_id, description, due_date_str, creation_date_str, status = parts
            creation_dt = datetime.strptime(creation_date_str, '%Y-%m-%d %H:%M:%S.%f')
            if status not in [STATUS_ACTIVE, STATUS_DONE]:
                print(f"Предупреждение: Некорректный статус '{status}' для задачи {task_id}, пропускаем.")
                return None
            return cls(task_id, description, due_date_str, creation_dt, status)
        return None

    def to_display_string(self):
        status_symbol = "✕" if self.status == STATUS_ACTIVE else "✓"
        
        overdue_marker = ""
        if self.is_overdue: 
            overdue_marker = " (просрочено)"

        creation_date_str_formatted = self._creation_date.strftime('%d.%m.%Y %H:%M')
        due_date_display = self.due_date_str

        return f"{status_symbol}{overdue_marker} {self.description} {due_date_display} (Создана: {creation_date_str_formatted})"

def print_all_tasks_to_console(tasks_display_strings):
    counter = 1
    if not tasks_display_strings:
        print("Список задач пуст.")
        return
    for task_str in tasks_display_strings:
        print(str(counter) + ": " + task_str)
        counter += 1

def read_from_db():
    if not os.path.exists(DB_FILE_PATH):
        print(f"Файл {DB_FILE_PATH} не найден. Будет создан новый при добавлении задачи.")
        return ""
    with open(DB_FILE_PATH, "r", encoding="utf8") as file_object:
        file_content = file_object.read()
    return file_content if file_content else ""

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
    task_objects = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(SEPARATOR)
        if len(parts) == 5:
            task_obj = Task.from_db_parts(parts)
            if task_obj:
                task_objects.append(task_obj)
        else:
            print(f"Предупреждение: Пропущена некорректная строка в базе данных: {line}")
    return task_objects

def prepare_tasks_list_to_output(task_objects_list):
    return [task.to_display_string() for task in task_objects_list]

def prepare_new_task_to_save(description_val, validated_due_date_content):
    task_id_val = uuid.uuid4()
    task_date_created_val = datetime.now()
    due_date_str_val = f"[{validated_due_date_content}]"
    new_task_obj = Task(
        task_id=task_id_val,
        description=description_val,
        due_date_str=due_date_str_val,
        creation_date=task_date_created_val,
        status=STATUS_ACTIVE
    )
    return new_task_obj.to_db_string()

def get_all_tasks(to_show_status=None):
    all_tasks_content = read_from_db()
    all_task_objects = deserialize_tasks_from_db(all_tasks_content)
    final_task_objects = []
    if to_show_status:
        final_task_objects = [task_obj for task_obj in all_task_objects if task_obj.status == to_show_status]
    else:
        final_task_objects = all_task_objects
    tasks_list_to_print = prepare_tasks_list_to_output(final_task_objects)
    return tasks_list_to_print, final_task_objects

def get_active_tasks_raw():
    all_tasks_content = read_from_db()
    all_task_objects = deserialize_tasks_from_db(all_tasks_content)
    active_task_objects = [task_obj for task_obj in all_task_objects if task_obj.status == STATUS_ACTIVE]
    return active_task_objects

def parse_new_task_input(raw_data):
    splitted_params = raw_data.split("[", 1)
    task_description = splitted_params[0].strip()
    task_due_date_content = ""
    if len(splitted_params) > 1:
        due_part = splitted_params[1]
        if ']' in due_part:
            task_due_date_content = due_part.split("]", 1)[0].strip()
    return [task_description, task_due_date_content]

def action_new_task():
    print("#------------------#")
    print("Введите параметры новой задачи (описание [дата исполнения ДД.ММ.ГГГГ ЧЧ:ММ]) или 0, чтобы вернуться:")
    new_task_info_str = input()

    if new_task_info_str == "0": return

    if not new_task_info_str.strip():
        print("Ошибка: Описание задачи не может быть пустым.")
        input("Нажмите Enter для возврата в меню...")
        return

    task_data_parts = parse_new_task_input(new_task_info_str)
    description_val = task_data_parts[0]
    due_date_content_input = task_data_parts[1]

    if not description_val: 
        print("Ошибка: Описание задачи не может быть пустым.")
        input("Нажмите Enter для возврата в меню...")
        return

    validated_due_date_content = validate_due_date_content(due_date_content_input)
    if due_date_content_input and validated_due_date_content is False:
        print(f"Ошибка: Неверный формат даты исполнения '{due_date_content_input}'. "
              f"Используйте формат ДД.ММ.ГГГГ ЧЧ:ММ или оставьте поле пустым.")
        input("Нажмите Enter для возврата в меню...")
        return

    task_to_save_str = prepare_new_task_to_save(description_val, validated_due_date_content)
    append_new_line_to_db(task_to_save_str)
    print("Задача успешно добавлена!")
    input("Нажмите Enter для возврата в меню...")

def action_complete_task():
    print("#------------------#")
    active_task_objects_list = get_active_tasks_raw()
    if not active_task_objects_list:
        print("Нет активных задач для завершения.")
        input("Нажмите Enter для возврата в меню...")
        return

    print("Активные задачи:")
    print_all_tasks_to_console(prepare_tasks_list_to_output(active_task_objects_list))
    print("\nВведите номер задачи для завершения или 0, чтобы вернуться:")

    task_number_str = input()
    if task_number_str == "0": return
    task_number = int(task_number_str)

    if task_number < 1 or task_number > len(active_task_objects_list):
        print("Ошибка: Неверный номер задачи.")
        input("Нажмите Enter для возврата в меню...")
        return

    task_to_complete_id_val = active_task_objects_list[task_number - 1].task_id
    all_tasks_content = read_from_db()
    all_task_objects_from_db = deserialize_tasks_from_db(all_tasks_content)
    updated_task_db_strings = []
    found = False
    for task_obj in all_task_objects_from_db:
        if task_obj.task_id == task_to_complete_id_val:
            task_obj.status = STATUS_DONE
            found = True
        updated_task_db_strings.append(task_obj.to_db_string())

    if found:
        final_string_to_save = "\n".join(updated_task_db_strings)
        rewrite_db(final_string_to_save)
        print(f"Задача номер {task_number} успешно завершена.")
    else:
        print("Ошибка: Не удалось найти задачу для завершения (возможно, база данных изменилась).")
    input("Нажмите Enter для возврата в меню...")

def action_change_task_params():
    print("#------------------#")
    active_task_objects_list = get_active_tasks_raw()
    if not active_task_objects_list:
        print("Нет активных задач для изменения.")
        input("Нажмите Enter для возврата в меню...")
        return

    print("Активные задачи:")
    print_all_tasks_to_console(prepare_tasks_list_to_output(active_task_objects_list))
    print("\nВведите номер задачи для изменения её параметров или 0, чтобы вернуться:")

    task_number_str = input()
    if task_number_str == "0": return
    task_number = int(task_number_str)

    if task_number < 1 or task_number > len(active_task_objects_list):
        print("Ошибка: Неверный номер задачи.")
        input("Нажмите Enter для возврата в меню...")
        return

    task_to_change_obj = active_task_objects_list[task_number - 1]
    task_to_change_id_val = task_to_change_obj.task_id
    current_description = task_to_change_obj.description
    current_due_date_content = task_to_change_obj.due_date_str[1:-1] if len(task_to_change_obj.due_date_str) > 1 else ""

    print(f"\nИзменение задачи №{task_number}:")
    print(f"Текущее описание: {current_description}")
    print(f"Текущая дата исполнения: {current_due_date_content}")
    print("Введите новое описание (или нажмите Enter, чтобы оставить текущее):")
    new_description_input = input().strip()
    print("Введите новую дату исполнения (формат ДД.ММ.ГГГГ ЧЧ:ММ; Enter - оставить; '-' - удалить):")
    new_due_date_content_user_input = input().strip()

    final_description = new_description_input if new_description_input else current_description
    if not final_description:
        print("Ошибка: Описание задачи не может быть пустым. Изменения не сохранены.")
        input("Нажмите Enter для возврата в меню...")
        return

    description_changed = final_description != current_description
    due_date_changed = False
    final_due_date_str_with_brackets = task_to_change_obj.due_date_str
    due_date_error_occurred = False

    if new_due_date_content_user_input == '-':
        if task_to_change_obj.due_date_str != "[]":
            due_date_changed = True
            final_due_date_str_with_brackets = "[]"
    elif new_due_date_content_user_input:
        validated_new_content = validate_due_date_content(new_due_date_content_user_input)
        if validated_new_content is False:
            print(f"Ошибка: Неверный формат новой даты исполнения '{new_due_date_content_user_input}'. "
                  f"Дата не будет изменена.")
            due_date_error_occurred = True
        else:
            proposed_due_date_str = f"[{validated_new_content}]"
            if proposed_due_date_str != task_to_change_obj.due_date_str:
                due_date_changed = True
                final_due_date_str_with_brackets = proposed_due_date_str
    elif not new_due_date_content_user_input:
        if task_to_change_obj.due_date_str != "[]":
            due_date_changed = True
            final_due_date_str_with_brackets = "[]"

    if not description_changed and not due_date_changed:
        if due_date_error_occurred:
            print("Никаких других изменений не внесено.")
        else:
            print("Никаких изменений не внесено.")
        input("Нажмите Enter для возврата в меню...")
        return

    all_tasks_content = read_from_db()
    all_task_objects_from_db = deserialize_tasks_from_db(all_tasks_content)
    updated_task_db_strings = []
    found_and_updated = False
    for task_obj_from_db in all_task_objects_from_db:
        if task_obj_from_db.task_id == task_to_change_id_val:
            task_obj_from_db.description = final_description
            if due_date_changed: 
                task_obj_from_db.due_date_str = final_due_date_str_with_brackets
            found_and_updated = True
        updated_task_db_strings.append(task_obj_from_db.to_db_string())

    if found_and_updated:
        final_string_to_save = "\n".join(updated_task_db_strings)
        rewrite_db(final_string_to_save)
        print(f"Параметры задачи номер {task_number} успешно изменены.")
    else:
        print("Ошибка: Не удалось найти задачу для изменения (возможно, база данных изменилась).")
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
    all_task_objects = deserialize_tasks_from_db(all_tasks_content)
    active_tasks_to_keep_db_strings = [
        task_obj.to_db_string() for task_obj in all_task_objects if task_obj.status == STATUS_ACTIVE
    ]
    removed_count = len(all_task_objects) - len(active_tasks_to_keep_db_strings)

    if removed_count > 0:
        final_string_to_save = "\n".join(active_tasks_to_keep_db_strings)
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
        rewrite_db("")
        print("База данных успешно очищена.")
    else:
        print("Очистка базы данных отменена.")
    print("#------------------#")
    input("Нажмите Enter для возврата в меню...")

def show_main_menu():
    print("#------------------#")
    print("Выберите действие:")
    menu_text = ""
    sorted_keys = sorted(MENU_ITEMS.keys(), key=lambda x: int(x) if x != EXIT_ITEM else float('inf'))
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
        tasks_list_to_print, _active_task_objects = get_all_tasks(STATUS_ACTIVE)
        print("\n#---------- АКТУАЛЬНЫЕ ЗАДАЧИ ----------#")
        print_all_tasks_to_console(tasks_list_to_print)
        show_main_menu()

if __name__ == "__main__":
    main()