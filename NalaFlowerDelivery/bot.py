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
from aiogram.types import BufferedInputFile

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
    WAITING_FOR_CONFIRMATION = State()


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
async def start_command(message: types.Message):
    await message.answer(
        "Welcome to Nala Flower Bot! You can view our catalog with /catalog and make an order with /order.")


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

            if image_url:
                # Убедитесь, что URL начинается с 'http://' или 'https://'
                if not image_url.startswith(('http://', 'https://')):
                    image_url = f"{MEDIA_BASE_URL}{image_url}"  # Добавляем базовый URL для доступа к медиафайлам

                try:
                    # Загружаем изображение в память
                    image_data = await fetch_image(image_url)

                    if image_data:
                        # Используем io.BytesIO для отправки изображения
                        photo = BufferedInputFile(image_data, filename="product.jpg")

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

    # Сохранение данных о заказе
    user_data = await state.get_data()
    product_id = user_data.get('product_id')
    product_price = float(user_data.get('product_price'))  # Преобразуем цену в float
    total_price = product_price * quantity

    # Генерация ссылки на страницу заказа
    checkout_url = f"http://127.0.0.1:8000/checkout?product_id={product_id}&quantity={quantity}&price={total_price:.2f}"

    await message.reply(
        f"Your order has been prepared!\n\n"
        f"**Total Price**: ${total_price:.2f}\n"
        f"[Proceed to Checkout]({checkout_url})",
        parse_mode=ParseMode.MARKDOWN
    )

    await state.clear()


# Ваша функция для обработки заказа
@dp.message(OrderStates.WAITING_FOR_CONFIRMATION)
async def process_order_confirmation(message: types.Message, state: FSMContext):
    global payment_url
    user_data = await state.get_data()
    product_id = user_data.get('product_id')
    quantity = user_data.get('quantity')
    total_price = user_data.get('total_price')

    # Создаем заказ через API
    response = requests.post(f'{API_BASE_URL}orders/', json={
        'user_id': message.from_user.id,
        'product_ids': [product_id],
        'quantities': [quantity],
        'total_price': total_price
    })

    if response.status_code == 201:
        order_id = response.json().get('id')
        payment_url = f"http://127.0.0.1:8000/checkout/{order_id}/"
        await message.reply(
            f"Your order has been placed successfully!\n\n"
            f"**Total Price**: ${total_price}\n"
            f"[Pay Now]({payment_url})",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply("There was an error placing your order. Please try again.")

    await state.clear()


# Обработка команды /status для проверки статуса заказа



# Регистрация обработчиков
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, CommandStart())
    dp.message.register(show_catalog, Command(commands=['catalog']))
    dp.message.register(start_order, Command(commands=['order']))
    dp.message.register(process_product_id, OrderStates.WAITING_FOR_PRODUCT_ID)
    dp.message.register(process_quantity, OrderStates.WAITING_FOR_QUANTITY)


# Асинхронная функция main для запуска бота
async def main():
    register_handlers(dp)
    await dp.start_polling(bot)


# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())

