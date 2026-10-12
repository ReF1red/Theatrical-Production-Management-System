"""Консольное меню."""

from pathlib import Path

from models.bookings import (
    cancel_booking,
    create_booking,
    get_booking_statistics,
    is_seat_available,
)
from models.casting import can_cast_actor, find_suitable_actors
from models.productions import (
    add_production,
    find_productions,
    get_production_by_id,
    iter_productions_by_genre,
    sort_productions,
    update_readiness,
)
from models.shows import add_show, get_show_by_id, sort_shows
from models import Actor, Booking, Production, Role, Show
from storage import (
    load_project, save_bookings, save_productions, save_shows,
)
from models.tickets import BASE_TICKET_PRICE, calculate_ticket_price
from utils import input_date, input_datetime, input_int, input_yes_no

DATA_DIR = Path(__file__).parent / "data"
PRODUCTIONS_FILE = DATA_DIR / "productions.json"
ACTORS_FILE = DATA_DIR / "actors.json"
ROLES_FILE = DATA_DIR / "roles.json"
SHOWS_FILE = DATA_DIR / "shows.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"


def show_productions(productions: list[Production]) -> None:
    if not productions:
        print("Постановок пока нет.")
    for production in productions:
        print(production)


def show_shows(shows: list[Show]) -> None:
    if not shows:
        print("Показов пока нет.")
    for show in sort_shows(shows):
        print(show)


def show_bookings(bookings: list[Booking]) -> None:
    if not bookings:
        print("Бронирований пока нет.")
    for booking in bookings:
        print(booking)


def add_production_menu(productions: list[Production]) -> None:
    title = input("Название: ").strip()
    author = input("Автор: ").strip()
    genre = input("Жанр: ").strip()
    premiere_date = input_date("Дата премьеры (ДД.ММ.ГГГГ): ")
    production = add_production(
        productions,
        title,
        author,
        genre,
        premiere_date,
    )
    save_productions(PRODUCTIONS_FILE, productions)
    print(f'Добавлена постановка #{production.id}.')


def update_readiness_menu(productions: list[Production]) -> None:
    production_id = input_int("ID постановки: ", 1)
    rehearsals_done = input_yes_no("Репетиции завершены? (да/нет): ")
    costumes_ready = input_yes_no("Костюмы готовы? (да/нет): ")
    scenery_ready = input_yes_no("Декорации готовы? (да/нет): ")
    updated = update_readiness(
        productions,
        production_id,
        rehearsals_done,
        costumes_ready,
        scenery_ready,
    )
    if updated:
        save_productions(PRODUCTIONS_FILE, productions)
        print("Готовность постановки обновлена.")
    else:
        print("Постановка с таким ID не найдена.")


def find_production_menu(productions: list[Production]) -> None:
    query = input("Введите название, автора или жанр: ")
    found = find_productions(productions, query)
    show_productions(found)


def filter_genre_menu(productions: list[Production]) -> None:
    genre = input("Жанр: ")
    found = list(iter_productions_by_genre(productions, genre))
    show_productions(found)


def add_show_menu(shows: list[Show], productions: list[Production]) -> None:
    production_id = input_int("ID постановки: ", 1)
    production = get_production_by_id(productions, production_id)
    if production is None:
        print("Постановка с таким ID не найдена.")
        return
    show_datetime = input_datetime("Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ): ")
    hall = input("Название зала: ").strip()
    capacity = input_int("Вместимость зала: ", 1)
    show = add_show(shows, production, show_datetime, hall, capacity)
    save_shows(SHOWS_FILE, shows)
    print(f'Добавлен показ #{show.id}.')


def seat_availability_menu(
    shows: list[Show],
    bookings: list[Booking],
) -> None:
    show_id = input_int("ID показа: ", 1)
    show = get_show_by_id(shows, show_id)
    if show is None:
        print("Показ с таким ID не найден.")
        return
    seat_number = input_int("Номер места: ", 1, show.capacity)
    if is_seat_available(bookings, show, seat_number):
        print("Место свободно.")
    else:
        print("Место уже забронировано.")


def create_booking_menu(
    shows: list[Show],
    bookings: list[Booking],
) -> None:
    show_id = input_int("ID показа: ", 1)
    show = get_show_by_id(shows, show_id)
    if show is None:
        print("Показ с таким ID не найден.")
        return

    seat_number = input_int("Номер места: ", 1, show.capacity)
    zone = input_int("Зона (1 — партер, 2 — бельэтаж, 3 — балкон): ", 1, 3)
    category = input("Категория (полный/льготный): ").strip().lower()
    try:
        booking = create_booking(
            bookings,
            show,
            seat_number,
            zone,
            category,
        )
    except ValueError as error:
        print(f"Ошибка: {error}")
        return

    save_bookings(BOOKINGS_FILE, bookings)
    print(
        f'Бронь #{booking.id} создана. '
        f'Стоимость: {booking.price:.2f} руб.'
    )


def cancel_booking_menu(bookings: list[Booking]) -> None:
    booking_id = input_int("ID бронирования: ", 1)
    if cancel_booking(bookings, booking_id):
        save_bookings(BOOKINGS_FILE, bookings)
        print("Бронирование отменено.")
    else:
        print("Бронирование с таким ID не найдено.")


def ticket_price_menu() -> None:
    zone = input_int("Зона (1/2/3): ", 1, 3)
    has_discount = input_yes_no("Есть льгота? (да/нет): ")
    price = calculate_ticket_price(
        BASE_TICKET_PRICE,
        zone,
        has_discount,
    )
    print(f"Стоимость билета: {price:.2f} руб.")


def casting_menu(actors: list[Actor], roles: list[Role]) -> None:
    if not roles:
        print("Роли отсутствуют.")
        return

    for role in roles:
        print(
            f'{role.id}. {role.title}: пол '
            f'{role.required_gender}, возраст '
            f'{role.min_age}-{role.max_age}'
        )
    role_id = input_int("ID роли: ", 1)
    role = next((item for item in roles if item.id == role_id), None)
    if role is None:
        print("Роль с таким ID не найдена.")
        return

    suitable = find_suitable_actors(actors, role)
    if not suitable:
        print("Подходящих актёров нет.")
        return

    print("Подходящие актёры:")
    for actor in suitable:
        result = can_cast_actor(
            actor.gender,
            actor.age,
            role.required_gender,
            role.min_age,
            role.max_age,
        )
        print(f'- {actor.name}, {actor.age} лет — {result}')


def statistics_menu(bookings: list[Booking]) -> None:
    stats = get_booking_statistics(bookings)
    print(f'Всего бронирований: {stats["count"]}')
    print(f'Льготных билетов: {stats["discount_count"]}')
    print(f'Выручка: {stats["revenue"]:.2f} руб.')
    print(f'Средняя цена: {stats["average_price"]:.2f} руб.')


def print_menu() -> None:
    print("\n=== Система управления театральными постановками ===")
    print("1. Показать постановки")
    print("2. Найти постановку")
    print("3. Показать постановки выбранного жанра")
    print("4. Добавить постановку")
    print("5. Изменить готовность постановки")
    print("6. Показать постановки по дате премьеры")
    print("7. Показать сеансы")
    print("8. Добавить сеанс")
    print("9. Проверить свободное место")
    print("10. Забронировать билет")
    print("11. Отменить бронирование")
    print("12. Показать бронирования")
    print("13. Рассчитать стоимость билета")
    print("14. Подобрать актёра на роль")
    print("15. Статистика бронирований")
    print("0. Выход")


def main() -> None:
    try:
        data = load_project(DATA_DIR)
    except (ValueError, OSError) as error:
        print(f"Не удалось загрузить данные: {error}")
        return

    actions = {
        "1": lambda: show_productions(data.productions),
        "2": lambda: find_production_menu(data.productions),
        "3": lambda: filter_genre_menu(data.productions),
        "4": lambda: add_production_menu(data.productions),
        "5": lambda: update_readiness_menu(data.productions),
        "6": lambda: show_productions(sort_productions(data.productions)),
        "7": lambda: show_shows(data.shows),
        "8": lambda: add_show_menu(data.shows, data.productions),
        "9": lambda: seat_availability_menu(data.shows, data.bookings),
        "10": lambda: create_booking_menu(data.shows, data.bookings),
        "11": lambda: cancel_booking_menu(data.bookings),
        "12": lambda: show_bookings(data.bookings),
        "13": ticket_price_menu,
        "14": lambda: casting_menu(data.actors, data.roles),
        "15": lambda: statistics_menu(data.bookings),
    }
    while True:
        try:
            print_menu()
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                print("Работа завершена.")
                break
            action = actions.get(choice)
            if action is None:
                print("Неизвестный пункт меню.")
            else:
                action()
        except (ValueError, OSError) as error:
            print(f"Ошибка: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nРабота завершена.")
            break


if __name__ == "__main__":
    main()
