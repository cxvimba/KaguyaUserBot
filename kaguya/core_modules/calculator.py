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
        version='1.1.0',
        author='cxvimba',
        commands={
            'calc | калькулятор': 'Вычислить математическое выражение'
        }
    )

    LANGUAGES = {
        'en': {
            'usage': (
                '🧮 <b>Kaguya | Calculator</b>\n\n'
                ' └ Example: <code>{p}calc (2 + 2) * 5</code>'
            ),
            'calculating': '⏳ <b>Kaguya:</b> Calculating...',
            'result': (
                '🧮 <b>Kaguya | Result:</b>\n\n'
                ' ├ 📝 <code>{expression}</code>\n'
                ' └ 📊 <b>Answer:</b> <code>{result}</code>'
            ),
            'zero_division': '❌ <b>Kaguya:</b> Error — division by zero!',
            'calc_error': '❌ <b>Kaguya:</b> Calculation error. Reason: <code>{error}</code>'
        },
        'ru': {
            'usage': (
                '🧮 <b>Kaguya | Калькулятор</b>\n\n'
                ' └ Пример: <code>{p}calc (2 + 2) * 5</code>'
            ),
            'calculating': '⏳ <b>Kaguya:</b> Вычисление...',
            'result': (
                '🧮 <b>Kaguya | Результат:</b>\n\n'
                ' ├ 📝 <code>{expression}</code>\n'
                ' └ 📊 <b>Ответ:</b> <code>{result}</code>'
            ),
            'zero_division': '❌ <b>Kaguya:</b> Ошибка — деление на ноль!',
            'calc_error': '❌ <b>Kaguya:</b> Ошибка вычислений. Причина: <code>{error}</code>'
        }
    }

    @on_command(['calc', 'мат', 'калькулятор'])
    async def calculate_cmd(self, client: Client, message: Message):
        """Парсит и вычисляет математическое выражение."""
        if len(message.command) < 2:
            p = get_prefix(client)
            await message.edit_text(
                self.get_text('usage').format(p=p)
            )
            return

        expression = message.text.split(maxsplit=1)[1]
        await message.edit_text(self.get_text('calculating'))

        try:
            tree = ast.parse(expression, mode='eval')
            result = calc(tree.body)

            if isinstance(result, float) and result.is_integer():
                result = int(result)

            await message.edit_text(
                self.get_text('result').format(expression=expression, result=result)
            )

        except ZeroDivisionError:
            await message.edit_text(self.get_text('zero_division'))
        except Exception as e:
            await message.edit_text(
                self.get_text('calc_error').format(error=e)
            )
