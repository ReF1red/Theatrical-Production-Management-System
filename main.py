
from datetime import date

#  Данные о постановке

production_title = "Вишнёвый сад"
production_author = "А. П. Чехов"
production_genre = "драма"
premiere_date = date(2026, 10, 15)

rehearsals_done = True   # репетиции
costumes_ready = True    # костюмы 
scenery_ready = False    # декорации

BASE_TICKET_PRICE = 1500.0


# Статус постановки

def get_production_status(rehearsals_done, costumes_done, scenery_done):
    """Определяет этап подготовки постановки по её готовности."""
    if not rehearsals_done:
        return "Идут репетиции"
    if not costumes_done or not scenery_done:
        return "Репетиции окончены, идёт оформление спектакля"
    return "Постановка готова к выпуску на сцену"


# Расчёт стоимости билета 

def calculate_ticket_price(base_price, seat_zone, is_discount_eligible):
    # Условные размеры зала их обозначения и множитель цены
    # 1 — партер (x1.5), 2 — бельэтаж (x1.2), 3 — балкон (x0.7).
    # скидка там всяким несчастным 30 процентов тобишь * 0.7
    if seat_zone == 1:
        price = base_price * 1.5
    elif seat_zone == 2:
        price = base_price * 1.2
    elif seat_zone == 3:
        price = base_price * 0.7
    else:
        return None

    if is_discount_eligible:
        price = price * 0.7

    return round(price, 2)


# Подбор актёра на роль

def can_cast_actor(actor_gender, actor_age, role_gender, role_min_age, role_max_age):
    #Проверяет соответствие актёра роли по полу и возрастному диапазону
    if actor_gender != role_gender:
        return "Актёр не подходит на роль: не совпадает пол"
    if actor_age < role_min_age:
        return "Актёр не подходит на роль: не достиг минимального возраста роли"
    if actor_age > role_max_age:
        return "Актёр не подходит на роль: превышает максимальный возраст роли"
    return "Актёр подходит на роль по полу и возрасту"

# УСЛОВНЫЙ ДЕМО СЦЕНАРИЙ
if __name__ == "__main__":
    print("=" * 46)
    print(f"Спектакль: «{production_title}» ({production_genre})")
    print(f"Автор: {production_author}")
    print("Дата премьеры:", premiere_date.strftime("%d.%m.%Y"))
    print("=" * 46)

    # Демо статус постановки
    status = get_production_status(rehearsals_done, costumes_ready, scenery_ready)
    print("Статус постановки:", status)

    # ДЕмо расчёт стоимости билета
    # данные кассы приходят строками, выполняем преобразование типов
    zone_input = "2"                      
    discount_input = "да"                  
    seat_zone = int(zone_input)            
    has_discount = discount_input == "да"  

    price = calculate_ticket_price(BASE_TICKET_PRICE, seat_zone, has_discount)
    if price is None:
        print("Ошибка: указана несуществующая зона зала")
    else:
        print(f"Билет (зона {seat_zone}): {price} руб.")

    #подбор актёров на роль
    role_title = "Раневская"
    role_gender = "ж"
    role_min_age = 30
    role_max_age = 45

    print(f"\nРоль: {role_title} (пол: {role_gender}, возраст: {role_min_age}–{role_max_age})")

    # Актёр 1: данные приходят строками — преобразуем типы
    actor1_name = "Анна Иванова"
    actor1_gender = "ж"
    actor1_age = int("34")
    print(f"{actor1_name} ({actor1_gender}, {actor1_age} лет):",
          can_cast_actor(actor1_gender, actor1_age, role_gender, role_min_age, role_max_age))

    # Актёр 2: пол не совпадает с требуемым
    actor2_name = "Пётр Смирнов"
    actor2_gender = "м"
    actor2_age = int("40")
    print(f"{actor2_name} ({actor2_gender}, {actor2_age} лет):",
          can_cast_actor(actor2_gender, actor2_age, role_gender, role_min_age, role_max_age))
