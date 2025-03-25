import multiprocessing
import random
import time

# Hàm sinh số bệnh nhân với đệ quy
def generate_floor_patients(M, total, max_val=10):
    if M == 1:
        return [total] if total <= max_val else None
    valid_choices = [v for v in range(0, min(max_val, total) + 1)]
    random.shuffle(valid_choices)
    for v in valid_choices:
        sub = generate_floor_patients(M - 1, total - v, max_val)
        if sub is not None:
            return [v] + sub
    return None

# Hàm kiểm tra xem còn bệnh nhân để cứu ở tầng hiện tại không
def has_patients_in_current_floor(hotel, room_flood_status, floor_id):
    for room in range(len(hotel[floor_id])):
        if not room_flood_status[floor_id][room] and hotel[floor_id][room] > 0:
            return True
    return False

# Hàm kiểm tra xem còn bệnh nhân để cứu ở bất kỳ tầng nào không
def has_patients_to_rescue(hotel, room_flood_status, total_floors):
    for floor in range(total_floors - 1):
        for room in range(len(hotel[floor])):
            if not room_flood_status[floor][room] and hotel[floor][room] > 0:
                return True
    return False

# Hàm kiểm tra điều kiện dừng
def should_stop(hotel, room_flood_status, nurses, roof_nurse_count, total_floors):
    no_patients = not has_patients_to_rescue(hotel, room_flood_status, total_floors)
    all_nurses_on_roof = sum(nurses[:-1]) == 0 and roof_nurse_count.value > 0
    return no_patients and all_nurses_on_roof

# Hàm quản lý từng tầng - Di chuyển qua cầu thang ở phòng cuối cùng bên phải
def floor_process(floor_id, num_rooms, x_time, hotel, nurses, room_flood_status, 
                  flood_status, roof_patient_count, roof_nurse_count, total_floors, lock, done_event, nurse_positions):
    while not all(room_flood_status[floor_id]):  # Chưa ngập hết tầng
        with lock:
            current_nurses = nurses[floor_id]
        if current_nurses == 0:
            break
        for _ in range(current_nurses):
            rescued = False
            current_room = nurse_positions[floor_id]  # Vị trí hiện tại của y tá
            for room in range(current_room, num_rooms):
                with lock:
                    if room_flood_status[floor_id][num_rooms - 1]:
                        break  # Không thể cứu nếu cầu thang ngập
                    if not room_flood_status[floor_id][room] and hotel[floor_id][room] > 0:
                        patients_to_move = min(2, hotel[floor_id][room])
                        hotel[floor_id][room] -= patients_to_move
                        hotel[floor_id][num_rooms - 1] += patients_to_move  # Di chuyển đến R4
                        rescued = True
                        nurse_positions[floor_id] = num_rooms - 1  # Y tá di chuyển đến R4
                        break
            if rescued:
                distance_to_stair = num_rooms - 1 - current_room
                time_to_rescue = x_time
                time_to_move_to_stair = distance_to_stair * x_time
                total_time = time_to_rescue + time_to_move_to_stair
                time.sleep(total_time)
            else:
                time.sleep(x_time / 10)

            # Đưa bệnh nhân từ R4 lên mái nếu R4 chưa ngập
            with lock:
                if not room_flood_status[floor_id][num_rooms - 1] and hotel[floor_id][num_rooms - 1] > 0:
                    patients_at_stair = hotel[floor_id][num_rooms - 1]
                    hotel[floor_id][num_rooms - 1] = 0
                    if floor_id < total_floors - 2:
                        hotel[floor_id + 1][num_rooms - 1] += patients_at_stair
                    elif floor_id == total_floors - 2:
                        roof_patient_count.value += patients_at_stair
                    time.sleep(x_time)  # Thời gian qua cầu thang

        with lock:
            if not has_patients_in_current_floor(hotel, room_flood_status, floor_id):
                if not room_flood_status[floor_id][num_rooms - 1]:
                    time.sleep(x_time)
                    if floor_id < total_floors - 2:
                        nurses[floor_id + 1] += nurses[floor_id]
                        nurse_positions[floor_id + 1] = num_rooms - 1
                    elif floor_id == total_floors - 2:
                        roof_nurse_count.value += nurses[floor_id]
                    nurses[floor_id] = 0
                    nurse_positions[floor_id] = -1
                break
            if should_stop(hotel, room_flood_status, nurses, roof_nurse_count, total_floors):
                done_event.set()
                return

    with lock:
        if nurses[floor_id] > 0 and not room_flood_status[floor_id][num_rooms - 1]:
            time.sleep(x_time)
            if floor_id < total_floors - 2:
                nurses[floor_id + 1] += nurses[floor_id]
                nurse_positions[floor_id + 1] = num_rooms - 1
            elif floor_id == total_floors - 2:
                roof_nurse_count.value += nurses[floor_id]
            nurses[floor_id] = 0
            nurse_positions[floor_id] = -1
        if should_stop(hotel, room_flood_status, nurses, roof_nurse_count, total_floors):
            done_event.set()

# Hàm quản lý lũ lụt
def flood_controller(num_floors, num_rooms, x_time, room_flood_status, flood_status, lock, done_event):
    current_floor = 0
    current_room = 0
    while current_floor < num_floors and not done_event.is_set():
        time.sleep(3 * x_time)
        with lock:
            room_flood_status[current_floor][current_room] = True
            if all(room_flood_status[current_floor]):
                flood_status[current_floor] = True
                current_floor += 1
                current_room = 0
            else:
                current_room += 1

# Hàm hiển thị trạng thái khách sạn với số y tá trong phòng
def display_hotel_status(hotel, nurses, room_flood_status, flood_status, time_unit, roof_patient_count, nurse_positions):
    total_floors = len(hotel)
    print(f"\nTime: {time_unit}")
    print("-" * 50)
    print("Floor/Room Status:")
    header = "Floor       | " + " | ".join([f"R{r+1}" for r in range(len(hotel[0]))]) + " | Nurses"
    print(header)
    print("-" * 50)
    for floor in range(total_floors - 1, -1, -1):
        if floor == total_floors - 1:
            row = f"Roof        | {roof_patient_count.value}P (Rescued) | " + "   | " * (len(hotel[0]) - 1) + f"{nurses[floor]}"
        else:
            status = "Flooded" if flood_status[floor] else "Safe"
            row = f"Floor {floor+1} ({status}) | "
            for room in range(len(hotel[floor])):
                cell = "x" if room_flood_status[floor][room] else f"{hotel[floor][room]}P"
                if nurse_positions[floor] == room:
                    cell += f"/{nurses[floor]}N"
                row += f"{cell:<6} | "
            row += f"{nurses[floor]}"
        print(row)
    print("-" * 50)

# Hàm vòng lặp hiển thị
def display_loop(done_event, hotel, nurses, room_flood_status, flood_status, x_time, lock, roof_patient_count, nurse_positions):
    t = 0
    while not done_event.is_set():
        with lock:
            display_hotel_status(hotel, nurses, room_flood_status, flood_status, t, roof_patient_count, nurse_positions)
        time.sleep(x_time)  # Hiển thị mỗi X giây
        t += x_time

# Hàm chính
def main():
    # Tham số
    N = 2  # Số tầng (bao gồm mái)
    M = 4  # Số phòng mỗi tầng
    X = 1  # Đơn vị thời gian X

    manager = multiprocessing.Manager()
    lock = multiprocessing.Lock()

    # Khởi tạo khách sạn
    hotel = manager.list()
    for _ in range(N - 1):
        floor_patients = generate_floor_patients(M, M * 3, max_val=10)
        if floor_patients is None or sum(floor_patients) != 12:  # Đảm bảo tổng là 12
            floor_patients = [3, 7, 1, 1]  # Nếu không tạo được, dùng mặc định từ ví dụ
        hotel.append(manager.list(floor_patients))
    hotel.append(manager.list([0]))  # Tầng mái

    # Khởi tạo y tá ở R1 của Floor 1
    nurses = manager.list([1] + [0] * (N - 1))  # Y tá ở Floor 1
    nurse_positions = manager.list([0] + [-1] * (N - 1))  # Y tá ở R1 của Floor 1
    initial_nurses = sum(nurses)
    total_patients = sum(sum(floor) for floor in hotel[:-1])

    # Khởi tạo trạng thái ngập
    room_flood_status = manager.list([manager.list([False] * M) for _ in range(N - 1)] + 
                                     [manager.list([False])])
    flood_status = manager.list([False] * N)

    roof_patient_count = multiprocessing.Value('i', 0)
    roof_nurse_count = multiprocessing.Value('i', 0)
    done_event = manager.Event()

    # Hiển thị trạng thái ban đầu trước khi lũ lụt bắt đầu
    print("Initial State (Before Flood):")
    with lock:
        display_hotel_status(hotel, nurses, room_flood_status, flood_status, "0 (Initial)", roof_patient_count, nurse_positions)

    # Tạo tiến trình
    processes = [
        multiprocessing.Process(target=flood_controller, 
                               args=(N - 1, M, X, room_flood_status, flood_status, lock, done_event))
    ]
    processes.extend(multiprocessing.Process(target=floor_process, 
                                            args=(i, M, X, hotel, nurses, room_flood_status, 
                                                  flood_status, roof_patient_count, roof_nurse_count, N, lock, done_event, nurse_positions)) 
                    for i in range(N - 1))

    # Tạo tiến trình hiển thị
    p_display = multiprocessing.Process(target=display_loop, 
                                       args=(done_event, hotel, nurses, room_flood_status, flood_status, X, lock, roof_patient_count, nurse_positions))

    # Bắt đầu tiến trình
    for p in processes:
        p.start()
    p_display.start()

    # Chờ hoàn thành
    for p in processes:
        p.join()
    done_event.set()
    p_display.join()

    # Hiển thị bảng cuối cùng
    with lock:
        display_hotel_status(hotel, nurses, room_flood_status, flood_status, "Final", roof_patient_count, nurse_positions)

    # Tính kết quả
    dead_patients = sum(hotel[f][r] for f in range(N - 1) for r in range(M) 
                        if room_flood_status[f][r])
    saved_patients = roof_patient_count.value
    remaining_nurses = roof_nurse_count.value
    dead_nurses = initial_nurses - remaining_nurses
    efficiency = (saved_patients / total_patients) * 100 if total_patients > 0 else 0

    # In kết quả
    print("\n--- Final Results ---")
    print(f"Tổng số bệnh nhân ban đầu: {total_patients}")
    print(f"Số bệnh nhân được cứu: {saved_patients}")
    print(f"Số bệnh nhân đã chết: {dead_patients}")
    print(f"Tổng số y tá ban đầu: {initial_nurses}")
    print(f"Số y tá còn lại (sống sót): {remaining_nurses}")
    print(f"Số y tá đã chết: {dead_nurses}")
    print(f"Hiệu suất cứu bệnh nhân: {efficiency:.2f}%")

if __name__ == "__main__":
    main()