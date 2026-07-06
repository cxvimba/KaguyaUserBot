import io
import os
import sys
import zipfile
import shutil
import logging
from pathlib import Path
from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import on_command
from kaguya.utils.prefix import get_prefix


logger = logging.getLogger('Kaguya.SystemModules')


def check_security(code: str) -> list[str]:
    """Проверяет код на наличие потенциально опасных конструкций."""
    suspicious_keywords = {
        'eval(', 'exec(', '__import__', 'os.system', 'subprocess',
        '.session', 'session_path'
    }
    normalized_code = ''.join(code.split()).lower()

    found = []
    for word in suspicious_keywords:
        clean_word = ''.join(word.split()).lower()
        if clean_word in normalized_code:
            found.append(word)
    return found


@on_command(['modules', 'модули'])
async def list_modules(self, client: Client, message: Message):
    """Выводит список всех активных моделей."""
    try:
        if not self.client.loaded_modules:
            text = '⚠️ <b>Kaguya:</b> Нет загруженных модулей.'
            return

        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) > 1:
            target_name = command_parts[1].strip()
            found_mod = None

            for full_name, mod in self.client.loaded_modules.items():
                if mod.meta.name.lower() == target_name.lower():
                    found_mod = mod
                    break

            if not found_mod:
                text = f'❌ <b>Kaguya:</b> Модуль «{target_name}» не найден.'
                return

            text = f'📦 <b>{found_mod.meta.name}</b> <code>v{found_mod.meta.version}</code>\n'
            text += f' ├ <i>{found_mod.meta.description}</i>\n'
            if found_mod.meta.author and found_mod.meta.author != 'Anonymous':
                text += f' ├ <b>Автор:</b> {found_mod.meta.author}\n'

            if found_mod.meta.commands:
                p = get_prefix(client)
                cmds_list = []

                for cmd_key, desc in found_mod.meta.commands.items():
                    aliases = [a.strip() for a in cmd_key.split('|')]
                    formatted_aliases = ' | '.join([f'<code>{p}{alias}</code>' for alias in aliases])
                    cmds_list.append(f'<blockquote>{formatted_aliases} — {desc}</blockquote>')

                text += ' └ <b>Команды:</b>\n' + '\n'.join(cmds_list)
            else:
                text += ' └ <b>Команды:</b> отсутствуют'
            return

        count = len(self.client.loaded_modules)
        text = f'⚡️ <b>Kaguya UserBot</b> | 🌟 Модули: <code>{count}</code>\n\n'

        for idx, (path, mod) in enumerate(reversed(self.client.loaded_modules.items()), 1):
            text += f'{idx}. 📦 <b>{mod.meta.name}</b> <code>v{mod.meta.version}</code>\n'
            if mod.meta.author and mod.meta.author != 'Anonymous':
                text += f' └ <b>Автор:</b> {mod.meta.author}\n'
            text += '\n'
        p = get_prefix(client)
        text += f'<blockquote>💡 Узнать больше о модуле: <code>{p}modules Модуль</code></blockquote>'

    finally:
        await client.edit_media_cached(
            message=message,
            cache_key='modules_menu_file_id',
            local_path='assets/Kaguya_modules.png',
            caption=text
        )


@on_command(['install', 'установить'])
async def install_module(self, client: Client, message: Message):
    """
    Динамически загружает пользовательский модуль.
    Допустимые форматы: .py, .txt или папки в .zip
    """
    reply = message.reply_to_message

    if not reply or not reply.document:
        await message.edit_text('❌ <b>Kaguya:</b> Ответь этой командой на файл модуля (.py, .txt или .zip).')
        return

    doc = reply.document
    if not doc.file_name.endswith(('.py', '.txt', '.zip')):
        await message.edit_text(
            '❌ <b>Kaguya:</b> Поддерживаются только файлы <code>.py</code>, <code>.txt</code> или <code>.zip</code>.')
        return

    await message.edit_text('📥 <b>Kaguya:</b> Скачиваю и проверяю модуль...')

    target_dir = 'kaguya/modules'
    forbidden_filenames = {'system', 'client', 'loader', 'types', 'main', 'fsm', 'config'}

    # Установка пакетного модуля .zip
    if doc.file_name.endswith('.zip'):
        file_io = await client.download_media(doc, in_memory=True)
        zip_bytes = io.BytesIO(file_io.getvalue())

        temp_zip_dir = os.path.join(target_dir, '_temp_zip_install')
        if os.path.exists(temp_zip_dir):
            shutil.rmtree(temp_zip_dir)
        os.makedirs(temp_zip_dir)

        try:
            # Распаковка и проверка безопасности
            with zipfile.ZipFile(zip_bytes) as z:
                for member in z.infolist():
                    try:
                        member.filename = member.filename.encode('cp437').decode('cp866')
                    except Exception:
                        pass

                    filename = os.path.normpath(member.filename)
                    if filename.startswith(('/', '..')) or '../' in filename or '..\\' in filename:
                        raise ValueError('Попытка обхода директории в ZIP архиве (Zip Slip)!')
                z.extractall(temp_zip_dir)
        except Exception as e:
            if os.path.exists(temp_zip_dir):
                shutil.rmtree(temp_zip_dir)
            await message.edit_text(f'❌ <b>Kaguya:</b> Поврежденный или опасный ZIP-архив: <code>{e}</code>')
            return

        # Распознание структуры папки внутри архива
        init_at_root = os.path.exists(os.path.join(temp_zip_dir, '__init__.py'))
        subdirs = [d for d in os.listdir(temp_zip_dir) if os.path.isdir(os.path.join(temp_zip_dir, d))]

        if init_at_root:
            module_name = Path(doc.file_name).stem
            final_module_dir = os.path.join(target_dir, module_name)
            temp_file_path = os.path.join(temp_zip_dir, '__init__.py')
        elif len(subdirs) == 1:
            nested_folder = subdirs[0]
            if os.path.exists(os.path.join(temp_zip_dir, nested_folder, '__init__.py')):
                module_name = nested_folder
                final_module_dir = os.path.join(target_dir, module_name)
                temp_file_path = os.path.join(temp_zip_dir, nested_folder, '__init__.py')
            else:
                shutil.rmtree(temp_zip_dir)
                await message.edit_text(
                    '❌ <b>Kaguya:</b> Внутри ZIP-архива не найден файл <code>__init__.py</code>.')
                return
        else:
            shutil.rmtree(temp_zip_dir)
            await message.edit_text(
                '❌ <b>Kaguya:</b> Неверная структура архива. Ожидалась папка с <code>__init__.py</code>.')
            return

        if module_name.lower() in forbidden_filenames:
            shutil.rmtree(temp_zip_dir)
            await message.edit_text(f'❌ <b>Kaguya:</b> Имя модуля «{module_name}» зарезервировано системой.')
            return

        temp_import_name = 'kaguya.modules._temp_zip_install'

        try:
            # Импорт из временной папки для сбора метаданных
            meta = self.client.manager.load_module(temp_import_name, temp_file_path)

            with open(temp_file_path, 'r', encoding='utf-8') as f:
                init_code = f.read()

            warnings = check_security(init_code)
            if warnings:
                shutil.rmtree(temp_zip_dir)
                await message.edit_text(
                    f'⚠️ <b>Kaguya | Подозрительный модуль!</b>\n\n'
                    f'В коде пакета обнаружены заблокированные вызовы: <code>{", ".join(warnings)}</code>\n'
                    f'Этот архив может содержать вредоносный код!\n\n'
                    f'<b>Установка заблокирована из соображений безопасности.</b>'
                )
                return

            self.client.unload_module_handler(temp_import_name)
            self.client.loaded_modules.pop(temp_import_name, None)
            sys.modules.pop(temp_import_name, None)

            # Проверка на конфликты системных имен
            forbidden_meta_names = {'система', 'system', 'client', 'loader', 'core', 'ядро'}
            if meta.name.lower() in forbidden_meta_names:
                shutil.rmtree(temp_zip_dir)
                await message.edit_text(f'❌ <b>Kaguya:</b> Название «{meta.name}» зарезервировано системой.')
                return

            # Поиск дубликата имени модуля
            existing_full_name = None
            existing_mod = None
            for full_name, mod in self.client.loaded_modules.items():
                if mod.meta.name.lower() == meta.name.lower():
                    existing_full_name = full_name
                    existing_mod = mod
                    break

            if existing_mod:
                if 'core_modules' in existing_full_name:
                    shutil.rmtree(temp_zip_dir)
                    await message.edit_text(f'❌ <b>Kaguya:</b> Модуль «{meta.name}» конфликтует с системой.')
                    return

                # Защита от перезаписи разных авторов
                if existing_mod.meta.author.lower() != meta.author.lower():
                    shutil.rmtree(temp_zip_dir)
                    await message.edit_text(
                        f'❌ <b>Kaguya | Конфликт авторов</b>\n\n'
                        f'Модуль «{meta.name}» уже установлен, но его автор — <b>{existing_mod.meta.author}</b>.\n'
                        f'Новый модуль написан автором <b>{meta.author}</b>.\n\n'
                        f'Установка заблокирована во избежание перезаписи. Если хочешь заменить его, '
                        f'сначала удали старый: <code>{client.prefixes[0]}удалить {existing_mod.meta.name}</code>'
                        )
                    return

                # Обновление модуля
                await message.edit_text(f'🔄 <b>Kaguya:</b> Обновление модуля «{meta.name}» до v{meta.version}...')
                old_file = getattr(sys.modules.get(existing_full_name), '__file__', None)
                self.client.unload_module_handler(existing_full_name)
                self.client.loaded_modules.pop(existing_full_name, None)
                sys.modules.pop(existing_full_name, None)
                if old_file and os.path.exists(old_file):
                    package_dir = os.path.dirname(old_file)
                    shutil.rmtree(package_dir)

        except Exception as e:
            if os.path.exists(temp_zip_dir):
                shutil.rmtree(temp_zip_dir)
            raise e

        # Резервирование старой версии
        backup_dir = os.path.join(target_dir, f'_backup_{module_name}')
        if os.path.exists(final_module_dir):
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            os.rename(final_module_dir, backup_dir)

        if init_at_root:
            os.rename(temp_zip_dir, final_module_dir)
        else:
            os.rename(os.path.join(temp_zip_dir, nested_folder), final_module_dir)
            shutil.rmtree(temp_zip_dir)

        full_module_name = f'kaguya.modules.{module_name}'
        init_file_path = os.path.join(final_module_dir, '__init__.py')

        try:
            # Финализация установки модуля
            meta_final = self.client.manager.load_module(full_module_name, init_file_path)
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

            await message.edit_text(
                f'✅ <b>Модуль-пакет успешно установлен!</b>\n\n'
                f'📦 <b>{meta_final.name}</b> <code>v{meta_final.version}</code>\n'
                f' ├ <i>{meta_final.description}</i>\n'
                f' └ Папка модуля: <code>kaguya/modules/{module_name}</code>'
            )

        except Exception as load_error:
            # Откат к стабильной версии
            self.client.unload_module_handler(full_module_name)
            self.client.loaded_modules.pop(full_module_name, None)
            sys.modules.pop(full_module_name, None)

            if os.path.exists(final_module_dir):
                shutil.rmtree(final_module_dir)

            if os.path.exists(backup_dir):
                os.rename(backup_dir, final_module_dir)
                self.client.manager.load_module(full_module_name, init_file_path)

            raise load_error

    # Установка одиночного модуля .txt, .py
    else:
        module_name = Path(doc.file_name).stem

        if module_name.lower() in forbidden_filenames:
            await message.edit_text(
                f'❌ <b>Kaguya:</b> Имя файла «{module_name}» зарезервировано ядром. Установка заблокирована.')
            return

        file_path = os.path.join(target_dir, f'{module_name}.py')
        full_module_name = f'kaguya.modules.{module_name}'

        temp_file_path = os.path.join(target_dir, '_temp_install.py')
        temp_import_name = 'kaguya.modules._temp_install'

        try:
            file_io = await client.download_media(doc, in_memory=True)
            code = file_io.getvalue().decode('utf-8')

            compile(code, doc.file_name, 'exec')

            warnings = check_security(code)
            if warnings:
                await message.edit_text(
                    f'⚠️ <b>Kaguya | Подозрительный модуль!</b>\n\n'
                    f'В коде файла обнаружены заблокированные вызовы: <code>{", ".join(warnings)}</code>\n'
                    f'Этот файл может содержать вредоносный код!\n\n'
                    f'<b>Установка заблокирована из соображений безопасности.</b>'
                )
                return

            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            meta = self.client.manager.load_module(temp_import_name, temp_file_path)

            self.client.unload_module_handler(temp_import_name)
            self.client.loaded_modules.pop(temp_import_name, None)
            sys.modules.pop(temp_import_name, None)
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            forbidden_meta_names = {'система', 'system', 'client', 'loader', 'core', 'ядро'}
            if meta.name.lower() in forbidden_meta_names:
                await message.edit_text(
                    f'❌ <b>Kaguya:</b> Название модуля «{meta.name}» зарезервировано системой. Установка заблокирована.')
                return

            existing_full_name = None
            existing_mod = None
            for full_name, mod in self.client.loaded_modules.items():
                if mod.meta.name.lower() == meta.name.lower():
                    existing_full_name = full_name
                    existing_mod = mod
                    break

            if existing_mod:
                if 'core_modules' in existing_full_name:
                    await message.edit_text(
                        f'❌ <b>Kaguya:</b> Модуль «{meta.name}» конфликтует с системным компонентом.')
                    return

                if existing_mod.meta.author.lower() != meta.author.lower():
                    await message.edit_text(
                        f'❌ <b>Kaguya | Конфликт авторов</b>\n\n'
                        f'Модуль «{meta.name}» уже установлен, но его автор — <b>{existing_mod.meta.author}</b>.\n'
                        f'Новый модуль написан автором <b>{meta.author}</b>.\n\n'
                        f'Установка заблокирована во избежание перезаписи. Если хочешь заменить его, '
                        f'сначала удали старый: <code>{client.prefixes[0]}удалить {existing_mod.meta.name}</code>'
                    )
                    return

                await message.edit_text(f'🔄 <b>Kaguya:</b> Обновление модуля «{meta.name}» до v{meta.version}...')

                old_file = getattr(sys.modules.get(existing_full_name), '__file__', None)
                self.client.unload_module_handler(existing_full_name)
                self.client.loaded_modules.pop(existing_full_name, None)
                sys.modules.pop(existing_full_name, None)

                if old_file and os.path.exists(old_file):
                    os.remove(old_file)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            meta_final = self.client.manager.load_module(full_module_name, file_path)

            p = client.prefixes[0] if getattr(client, 'prefixes', None) else '.'
            cmds_list = []
            for cmd_key in meta_final.commands.keys():
                aliases = [a.strip() for a in cmd_key.split('|')]
                formatted_aliases = ' | '.join([f'<code>{p}{alias}</code>' for alias in aliases])
                cmds_list.append(formatted_aliases)

            cmds_str = ', '.join(cmds_list) if cmds_list else 'отсутствуют'
            await message.edit_text(
                f'✅ <b>Модуль успешно установлен!</b>\n\n'
                f'📦 <b>{meta_final.name}</b> <code>v{meta_final.version}</code>\n'
                f' ├ <i>{meta_final.description}</i>\n'
                f' └ <b>Команды:</b> {cmds_str}'
            )

        except SyntaxError as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            await message.edit_text(f'❌ <b>Kaguya:</b> Модуль поврежден\n<code>{e}</code>')
        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            await message.edit_text(f'❌ <b>Kaguya:</b> Не удалось загрузить модуль\n<code>{e}</code>')


@on_command(['unload', 'удалить'])
async def unload_module(self, client: Client, message: Message):
    """Удаляет пользовательский модуль."""
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.edit_text('❌ <b>Kaguya:</b> Укажи имя модуля. Пример: <code>.unload Модуль</code>')
        return

    target_name = command_parts[1].strip()

    found_full_import_name = None
    found_mod_instance = None

    for full_import_name, mod in self.client.loaded_modules.items():
        if mod.meta.name.lower() == target_name.lower():
            found_full_import_name = full_import_name
            found_mod_instance = mod
            break

    if not found_mod_instance:
        await message.edit_text(f'❌ <b>Kaguya:</b> Модуль с именем «{target_name}» не найден.')
        return

    if 'core_modules' in found_full_import_name:
        await message.edit_text('❌ <b>Kaguya:</b> Нельзя удалять системные модули ядра.')
        return

    try:
        module_file = getattr(sys.modules.get(found_full_import_name), '__file__', None)

        if module_file:
            abs_module_path = os.path.abspath(module_file)
            abs_safe_dir = os.path.abspath('kaguya/modules')

            if 'core_modules' in abs_module_path or 'client.py' in abs_module_path:
                await message.edit_text('❌ <b>Kaguya:</b> Нельзя удалять системные модули ядра.')
                return

            if abs_module_path.startswith(abs_safe_dir):
                if os.path.exists(abs_module_path):
                    if abs_module_path.endswith('__init__.py'):
                        package_dir = os.path.dirname(abs_module_path)
                        shutil.rmtree(package_dir)
                    else:
                        os.remove(abs_module_path)
            else:
                logger.warning(
                    f'Файл {abs_module_path} не был удален, так как он находится вне безопасной директории modules.')

        self.client.unload_module_handler(found_full_import_name)
        self.client.loaded_modules.pop(found_full_import_name, None)
        sys.modules.pop(found_full_import_name, None)

        await message.edit_text(
            f'🗑 <b>Kaguya:</b> Модуль «{found_mod_instance.meta.name}» успешно удален.')

    except Exception as e:
        await message.edit_text(f'❌ <b>Kaguya:</b> Ошибка при удалении модуля:\n<i>{e}</i>')
