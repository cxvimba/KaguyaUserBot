import ast
import operator as op
from pyrogram import Client
from pyrogram.types import Message
from kaguya.types import BaseModule, ModuleInfo, on_command
from kaguya.utils.prefix import get_prefix


def safe_pow(base, exponent):
    if abs(exponent) > 1000 or abs(base) > 1000:
        raise ValueError('числа слишком велики для возведения в степень')
    return op.pow(base, exponent)

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: safe_pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos
}

def calc(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise TypeError('поддерживаются только числа')

    elif isinstance(node, ast.BinOp):
        left = calc(node.left)
        right = calc(node.right)
        op_type = type(node.op)
        if op_type in operators:
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError('деление на ноль')
            return operators[op_type](left, right)
        raise TypeError(f'неподдерживаемый оператор: {op_type.__name__}')

    elif isinstance(node, ast.UnaryOp):
        operand = calc(node.operand)
        op_type = type(node.op)
        if op_type in operators:
            return operators[op_type](operand)
        raise TypeError(f'неподдерживаемый унарный оператор: {op_type.__name__}')

    else:
        raise TypeError(f'недопустимая конструкция: {type(node).__name__}')


class CalculatorModule(BaseModule):
    meta = ModuleInfo(
        name='Калькулятор',
        description='Математический калькулятор',
        version='1.0.0',
        author='cxvimba',
        commands={
            'calc | мат | кальк': 'Вычислить математическое выражение'
        }
    )

    @on_command(['calc', 'мат', "кальк"])
    async def calculate_cmd(self, client: Client, message: Message):
        """Парсит и вычисляет математическое выражение."""
        if len(message.command) < 2:
            p = get_prefix(client)
            await message.edit_text(
                f'🧮 <b>Kaguya | Калькулятор</b>\n\n'
                f' └ Пример: <code>{p}calc (2 + 2) * 5</code>'
            )
            return

        expression = message.text.split(maxsplit=1)[1]

        await message.edit_text('⏳ <b>Kaguya:</b> Вычисление...')

        try:
            tree = ast.parse(expression, mode='eval')
            result = calc(tree.body)

            if isinstance(result, float) and result.is_integer():
                result = int(result)

            await message.edit_text(
                f'🧮 <b>Kaguya | Результат:</b>\n\n'
                f' ├ 📝 <code>{expression}</code>\n'
                f' └ 📊 <b>Ответ:</b> <code>{result}</code>'
            )

        except ZeroDivisionError:
            await message.edit_text('❌ <b>Kaguya:</b> Ошибка — деление на ноль!')
        except Exception as e:
            await message.edit_text(f'❌ <b>Kaguya:</b> Ошибка вычислений. Причина: <code>{e}</code>')
