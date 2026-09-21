"""Точка запуска системы управления театральными постановками."""

from pathlib import Path

from bookings import (
    cancel_booking,
    create_booking,
    get_booking_statistics,
    is_seat_available,
)
from casting import can_cast_actor, find_suitable_actors
from productions import (
    add_production,
    find_productions,
    get_production_by_id,
    get_production_status,
    iter_productions_by_genre,
    sort_productions,
    update_readiness,
)
from shows import add_show, get_show_by_id, sort_shows
from storage import load_json, save_json
from tickets import BASE_TICKET_PRICE, calculate_ticket_price
from utils import input_date, input_datetime, input_int, input_yes_no

DATA_DIR = Path(__file__).parent / "data"
PRODUCTIONS_FILE = DATA_DIR / "productions.json"
ACTORS_FILE = DATA_DIR / "actors.json"
ROLES_FILE = DATA_DIR / "roles.json"
SHOWS_FILE = DATA_DIR / "shows.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"


def show_productions(productions: list[dict]) -> None:
    """Вывести список постановок со статусом готовности."""
    if not productions:
        print("Постановок пока нет.")
        return

    for production in productions:
        status = get_production_status(
            production["rehearsals_done"],
            production["costumes_ready"],
            production["scenery_ready"],
        )
        print(
            f'{production["id"]}. «{production["title"]}» — '
            f'{production["author"]}, {production["genre"]}; '
            f'премьера {production["premiere_date"]}; {status}'
        )


def show_shows(shows: list[dict], productions: list[dict]) -> None:
    """Вывести список показов с названиями постановок."""
    if not shows:
        print("Показов пока нет.")
        return

    for show in sort_shows(shows):
        production = get_production_by_id(
            productions,
            show["production_id"],
        )
        title = production["title"] if production else "Неизвестная постановка"
        print(
            f'{show["id"]}. «{title}» — {show["datetime"]}, '
            f'{show["hall"]}, мест: {show["capacity"]}'
        )


def show_bookings(bookings: list[dict]) -> None:
    """Вывести список бронирований."""
    if not bookings:
        print("Бронирований пока нет.")
        return

    for booking in bookings:
        print(
            f'#{booking["id"]}: показ {booking["show_id"]}, '
            f'место {booking["seat_number"]}, зона {booking["zone"]}, '
            f'{booking["category"]}, {booking["price"]:.2f} руб.'
        )


def add_production_menu(productions: list[dict]) -> None:
    """Запросить данные и добавить постановку."""
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
    save_json(PRODUCTIONS_FILE, productions)
    print(f'Добавлена постановка #{production["id"]}.')


def update_readiness_menu(productions: list[dict]) -> None:
    """Изменить состояние подготовки выбранной постановки."""
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
        save_json(PRODUCTIONS_FILE, productions)
        print("Готовность постановки обновлена.")
    else:
        print("Постановка с таким ID не найдена.")


def find_production_menu(productions: list[dict]) -> None:
    """Выполнить поиск постановок по текстовому запросу."""
    query = input("Введите название, автора или жанр: ")
    found = find_productions(productions, query)
    show_productions(found)


def filter_genre_menu(productions: list[dict]) -> None:
    """Показать постановки выбранного жанра через генератор."""
    genre = input("Жанр: ")
    found = list(iter_productions_by_genre(productions, genre))
    show_productions(found)


def add_show_menu(shows: list[dict], productions: list[dict]) -> None:
    """Запросить данные и добавить показ."""
    production_id = input_int("ID постановки: ", 1)
    if get_production_by_id(productions, production_id) is None:
        print("Постановка с таким ID не найдена.")
        return
    show_datetime = input_datetime("Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ): ")
    hall = input("Название зала: ").strip()
    capacity = input_int("Вместимость зала: ", 1)
    show = add_show(shows, production_id, show_datetime, hall, capacity)
    save_json(SHOWS_FILE, shows)
    print(f'Добавлен показ #{show["id"]}.')


def seat_availability_menu(
    shows: list[dict],
    bookings: list[dict],
) -> None:
    """Проверить доступность места на показ."""
    show_id = input_int("ID показа: ", 1)
    show = get_show_by_id(shows, show_id)
    if show is None:
        print("Показ с таким ID не найден.")
        return
    seat_number = input_int("Номер места: ", 1, show["capacity"])
    if is_seat_available(bookings, show_id, seat_number):
        print("Место свободно.")
    else:
        print("Место уже забронировано.")


def create_booking_menu(
    shows: list[dict],
    bookings: list[dict],
) -> None:
    """Создать бронирование билета через меню."""
    show_id = input_int("ID показа: ", 1)
    show = get_show_by_id(shows, show_id)
    if show is None:
        print("Показ с таким ID не найден.")
        return

    seat_number = input_int("Номер места: ", 1, show["capacity"])
    zone = input_int("Зона (1 — партер, 2 — бельэтаж, 3 — балкон): ", 1, 3)
    category = input("Категория (полный/льготный): ").strip().lower()
    try:
        booking = create_booking(
            bookings,
            show_id,
            seat_number,
            zone,
            category,
        )
    except ValueError as error:
        print(f"Ошибка: {error}")
        return

    save_json(BOOKINGS_FILE, bookings)
    print(
        f'Бронь #{booking["id"]} создана. '
        f'Стоимость: {booking["price"]:.2f} руб.'
    )


def cancel_booking_menu(bookings: list[dict]) -> None:
    """Отменить бронирование через меню."""
    booking_id = input_int("ID бронирования: ", 1)
    if cancel_booking(bookings, booking_id):
        save_json(BOOKINGS_FILE, bookings)
        print("Бронирование отменено.")
    else:
        print("Бронирование с таким ID не найдено.")


def ticket_price_menu() -> None:
    """Рассчитать стоимость билета без создания бронирования."""
    zone = input_int("Зона (1/2/3): ", 1, 3)
    has_discount = input_yes_no("Есть льгота? (да/нет): ")
    price = calculate_ticket_price(
        BASE_TICKET_PRICE,
        zone,
        has_discount,
    )
    print(f"Стоимость билета: {price:.2f} руб.")


def casting_menu(actors: list[dict], roles: list[dict]) -> None:
    """Показать подходящих актёров для выбранной роли."""
    if not roles:
        print("Роли отсутствуют.")
        return

    for role in roles:
        print(
            f'{role["id"]}. {role["title"]}: пол '
            f'{role["required_gender"]}, возраст '
            f'{role["min_age"]}-{role["max_age"]}'
        )
    role_id = input_int("ID роли: ", 1)
    role = next((item for item in roles if item["id"] == role_id), None)
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
            actor["gender"],
            actor["age"],
            role["required_gender"],
            role["min_age"],
            role["max_age"],
        )
        print(f'- {actor["name"]}, {actor["age"]} лет — {result}')


def statistics_menu(bookings: list[dict]) -> None:
    """Вывести простую статистику по бронированиям."""
    stats = get_booking_statistics(bookings)
    print(f'Всего бронирований: {stats["count"]}')
    print(f'Льготных билетов: {stats["discount_count"]}')
    print(f'Выручка: {stats["revenue"]:.2f} руб.')
    print(f'Средняя цена: {stats["average_price"]:.2f} руб.')


def print_menu() -> None:
    """Вывести главное меню приложения."""
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
    """Загрузить данные и запустить основной цикл меню."""
    try:
        productions = load_json(PRODUCTIONS_FILE)
        actors = load_json(ACTORS_FILE)
        roles = load_json(ROLES_FILE)
        shows = load_json(SHOWS_FILE)
        bookings = load_json(BOOKINGS_FILE)
    except ValueError as error:
        print(f"Не удалось загрузить данные: {error}")
        return

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "0":
            print("Работа завершена.")
            break
        if choice == "1":
            show_productions(productions)
        elif choice == "2":
            find_production_menu(productions)
        elif choice == "3":
            filter_genre_menu(productions)
        elif choice == "4":
            add_production_menu(productions)
        elif choice == "5":
            update_readiness_menu(productions)
        elif choice == "6":
            show_productions(sort_productions(productions))
        elif choice == "7":
            show_shows(shows, productions)
        elif choice == "8":
            add_show_menu(shows, productions)
        elif choice == "9":
            seat_availability_menu(shows, bookings)
        elif choice == "10":
            create_booking_menu(shows, bookings)
        elif choice == "11":
            cancel_booking_menu(bookings)
        elif choice == "12":
            show_bookings(bookings)
        elif choice == "13":
            ticket_price_menu()
        elif choice == "14":
            casting_menu(actors, roles)
        elif choice == "15":
            statistics_menu(bookings)
        else:
            print("Неизвестный пункт меню.")


if __name__ == "__main__":
    main()
