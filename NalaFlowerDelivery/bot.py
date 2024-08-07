import logging
import asyncio
import requests
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command
import io

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Ваш токен от BotFather
API_TOKEN = '6789035821:AAE0pdtUGw9X40fPAxT4t2GAXtewob5wXzg'
API_BASE_URL = 'http://127.0.0.1:8000/api/'  # Убедитесь, что URL-адрес правильный
MEDIA_BASE_URL = 'http://127.0.0.1:8000'  # Базовый URL для доступа к медиафайлам

# Создание экземпляра бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Используем MemoryStorage для FSM
dp = Dispatcher(storage=storage)

# Определение состояний с использованием StatesGroup
class OrderStates(StatesGroup):
    WAITING_FOR_PRODUCT_ID = State()
    WAITING_FOR_QUANTITY = State()
    WAITING_FOR_ADDRESS = State()

# Асинхронная функция для загрузки изображения
async def fetch_image(image_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                return await response.read()
            else:
                logging.error(f"Failed to fetch image. Status code: {response.status}")
                return None

# Обработка команды /start
@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        "Welcome to Nala Flower Bot! You can view our catalog with /catalog and make an order with /order."
    )

# Обработка команды /catalog для отображения каталога
@dp.message(Command(commands=['catalog']))
async def show_catalog(message: types.Message):
    try:
        # Запрос к API для получения каталога продуктов
        response = requests.get(f'{API_BASE_URL}products/')
        response.raise_for_status()  # Проверка на ошибки HTTP
        products = response.json()

        # Логирование для отладки
        logging.info(f"Fetched products: {products}")

        if not products:
            await message.reply("The catalog is currently empty.")
            return

        for product in products:
            catalog_text = (
                f"**ID**: {product['id']}\n"
                f"**Name**: {product['name']}\n"
                f"**Price**: ${product['price']}\n"
                f"**Description**: {product['description']}\n"
            )
            image_url = product.get('image')  # Предполагаем, что URL изображения хранится в поле image

            # Отправка сообщения с изображением продукта
            if image_url:
                # Убедитесь, что URL начинается с 'http://' или 'https://'
                if not image_url.startswith(('http://', 'https://')):
                    image_url = f"{MEDIA_BASE_URL}{image_url}"  # Добавляем базовый URL для доступа к медиафайлам

                try:
                    # Загружаем изображение в память
                    image_data = await fetch_image(image_url)

                    if image_data:
                        # Используем io.BytesIO для отправки изображения
                        photo = types.BufferedInputFile(image_data, filename="product.jpg")

                        # Отправляем изображение напрямую
                        await bot.send_photo(
                            chat_id=message.chat.id,
                            photo=photo,
                            caption=catalog_text,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await message.reply("Failed to fetch image.")
                except Exception as e:
                    logging.error(f"Failed to send image: {e}")
                    await message.reply(catalog_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply(catalog_text, parse_mode=ParseMode.MARKDOWN)

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching the catalog: {e}")
        await message.reply(f"An error occurred while fetching the catalog: {e}")

# Обработка команды /order для оформления заказа
@dp.message(Command(commands=['order']))
async def start_order(message: types.Message, state: FSMContext):
    await message.reply("Please enter the product ID you wish to order.")
    await state.set_state(OrderStates.WAITING_FOR_PRODUCT_ID)

# Обработка ввода ID продукта
@dp.message(OrderStates.WAITING_FOR_PRODUCT_ID)
async def process_product_id(message: types.Message, state: FSMContext):
    product_id = message.text
    try:
        product_id = int(product_id)
    except ValueError:
        await message.reply("Invalid Product ID. Please enter a numeric Product ID.")
        return

    # Проверка существования продукта
    response = requests.get(f'{API_BASE_URL}products/{product_id}/')
    if response.status_code == 404:
        await message.reply("Product not found. Please enter a valid Product ID.")
        return

    product = response.json()
    await state.update_data(product_id=product_id, product_price=product['price'])

    await message.reply("Please enter the quantity.")
    await state.set_state(OrderStates.WAITING_FOR_QUANTITY)

# Обработка ввода количества
@dp.message(OrderStates.WAITING_FOR_QUANTITY)
async def process_quantity(message: types.Message, state: FSMContext):
    quantity = message.text
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
    except ValueError:
        await message.reply("Invalid quantity. Please enter a positive integer.")
        return

    await state.update_data(quantity=quantity)

    await message.reply("Please enter your address (any format).")
    await state.set_state(OrderStates.WAITING_FOR_ADDRESS)

# Обработка ввода адреса доставки
@dp.message(OrderStates.WAITING_FOR_ADDRESS)
async def process_address(message: types.Message, state: FSMContext):
    # Просто сохраняем адрес, как он введен пользователем
    address = message.text.strip()  # Удаляем пробелы в начале и конце строки

    # Обновляем состояние с адресом
    await state.update_data(address=address)

    # Получение данных пользователя
    user_data = await state.get_data()
    product_id = user_data.get('product_id')
    quantity = user_data.get('quantity')
    product_price = user_data.get('product_price')
    total_price = product_price * quantity

    # Логирование отправляемых данных
    logging.info(f"Placing order with Product ID: {product_id}, Quantity: {quantity}, Address: {address}")

    # Создание заказа через API
    response = requests.post(f'{API_BASE_URL}orders/', json={
        'user_id': message.from_user.id,  # Убедитесь, что это правильный ID пользователя в базе данных
        'product_ids': [product_id],
        'quantities': [quantity],
        'address': address
    })

    if response.status_code == 201:
        payment_url = f"http://127.0.0.1:8000/payments/{response.json().get('order_id')}/"  # Ссылка на оплату
        await message.reply(
            f"Your order has been placed successfully!\n\n"
            f"**Total Price**: ${total_price}\n"
            f"[Pay Now]({payment_url})",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Логирование ошибки
        logging.error(f"Failed to place order. Response code: {response.status_code}, Response content: {response.text}")
        await message.reply(f"There was an error placing your order. Please try again. Error: {response.text}")

    await state.clear()

# Регистрация обработчиков
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, CommandStart())
    dp.message.register(show_catalog, Command(commands=['catalog']))
    dp.message.register(start_order, Command(commands=['order']))
    dp.message.register(process_product_id, OrderStates.WAITING_FOR_PRODUCT_ID)
    dp.message.register(process_quantity, OrderStates.WAITING_FOR_QUANTITY)
    dp.message.register(process_address, OrderStates.WAITING_FOR_ADDRESS)

# Асинхронная функция main для запуска бота
async def main():
    register_handlers(dp)
    await dp.start_polling(bot)

# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
