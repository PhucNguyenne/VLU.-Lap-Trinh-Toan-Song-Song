import multiprocessing
import random
import time
import os

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

# Hàm quản lý từng tầng - Di chuyển khi hết bệnh nhân ở tầng hiện tại
def floor_process(floor_id, num_rooms, x_time, hotel, nurses, room_flood_status, 
                  flood_status, roof_patient_count, roof_nurse_count, total_floors, lock, done_event):
    while not all(room_flood_status[floor_id]):  # Chưa ngập hết tầng
        with lock:
            current_nurses = nurses[floor_id]
        if current_nurses == 0:  # Không còn y tá thì thoát
            break
        for _ in range(current_nurses):
            rescued = False
            for room in range(num_rooms):  # Từ trái sang phải
                with lock:
                    if not room_flood_status[floor_id][room] and hotel[floor_id][room] > 0:
                        patients_to_move = min(2, hotel[floor_id][room])
                        hotel[floor_id][room] -= patients_to_move
                        rescued = True
                        if floor_id < total_floors - 2:
                            hotel[floor_id + 1][num_rooms - 1] += patients_to_move
                        elif floor_id == total_floors - 2:
                            roof_patient_count.value += patients_to_move
                        break
            time.sleep(x_time if rescued else x_time / 10)
        # Kiểm tra nếu không còn bệnh nhân ở tầng hiện tại
        with lock:
            if not has_patients_in_current_floor(hotel, room_flood_status, floor_id):
                if floor_id < total_floors - 2:
                    nurses[floor_id + 1] += nurses[floor_id]
                elif floor_id == total_floors - 2:
                    roof_nurse_count.value += nurses[floor_id]
                nurses[floor_id] = 0
                break  # Thoát vòng lặp, y tá đã di chuyển
            # Kiểm tra điều kiện dừng toàn bộ
            if should_stop(hotel, room_flood_status, nurses, roof_nurse_count, total_floors):
                done_event.set()
                return

    # Nếu thoát do tầng ngập hoặc hết bệnh nhân
    with lock:
        if nurses[floor_id] > 0:  # Nếu còn y tá chưa di chuyển trước đó
            if floor_id < total_floors - 2:
                nurses[floor_id + 1] += nurses[floor_id]
            elif floor_id == total_floors - 2:
                roof_nurse_count.value += nurses[floor_id]
            nurses[floor_id] = 0
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

# Hàm hiển thị trạng thái khách sạn, hiển thị từng bước không xóa terminal
def display_hotel_status(hotel, nurses, room_flood_status, flood_status, time_unit, roof_patient_count):
    total_floors = len(hotel)
    print(f"\nTime: {time_unit}")
    print("-" * 50)
    print("Floor/Room Status:")
    
    # Tiêu đề
    header = "Floor       | " + " | ".join([f"R{r+1}" for r in range(len(hotel[0]))]) + " | Nurses"
    print(header)
    print("-" * 50)
    
    # Hiển thị từng tầng theo thứ tự ngược (mái trên cùng, tầng 1 dưới cùng)
    for floor in range(total_floors - 1, -1, -1):
        if floor == total_floors - 1:  # Tầng mái
            row = f"Roof        | {roof_patient_count.value}P (Rescued) | " + "   | " * (len(hotel[0]) - 1) + "0"
        else:
            status = "Flooded" if flood_status[floor] else "Safe"
            row = f"Floor {floor+1} ({status}) | "
            for room in range(len(hotel[floor])):
                cell = "x" if room_flood_status[floor][room] else f"{hotel[floor][room]}P"
                row += f"{cell:<3} | "
            row += f"{nurses[floor]}"
        print(row)
    print("-" * 50)

# Hàm vòng lặp hiển thị
def display_loop(done_event, hotel, nurses, room_flood_status, flood_status, x_time, lock, roof_patient_count):
    t = 0
    while not done_event.is_set():
        with lock:
            display_hotel_status(hotel, nurses, room_flood_status, flood_status, t, roof_patient_count)
        time.sleep(3 * x_time)
        t += 3 * x_time

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
        if floor_patients is None:
            floor_patients = [3] * M
        hotel.append(manager.list(floor_patients))
    hotel.append(manager.list([0]))  # Tầng mái

    # Khởi tạo nurse
    nurses = manager.list([M // 4 for _ in range(N - 1)] + [0])
    initial_nurses = sum(nurses)
    total_patients = sum(sum(floor) for floor in hotel[:-1])

    # Khởi tạo trạng thái ngập
    room_flood_status = manager.list([manager.list([False] * M) for _ in range(N - 1)] + 
                                     [manager.list([False])])
    flood_status = manager.list([False] * N)

    roof_patient_count = multiprocessing.Value('i', 0)
    roof_nurse_count = multiprocessing.Value('i', 0)
    done_event = manager.Event()

    # Tạo tiến trình
    processes = [
        multiprocessing.Process(target=flood_controller, 
                               args=(N - 1, M, X, room_flood_status, flood_status, lock, done_event))
    ]
    processes.extend(multiprocessing.Process(target=floor_process, 
                                            args=(i, M, X, hotel, nurses, room_flood_status, 
                                                  flood_status, roof_patient_count, roof_nurse_count, N, lock, done_event)) 
                    for i in range(N - 1))

    # Tạo tiến trình hiển thị
    p_display = multiprocessing.Process(target=display_loop, 
                                       args=(done_event, hotel, nurses, room_flood_status, flood_status, X, lock, roof_patient_count))

    # Bắt đầu tiến trình
    for p in processes:
        p.start()
    p_display.start()

    # Chờ hoàn thành
    for p in processes:
        p.join()
    done_event.set()
    p_display.join()

    # Hiển thị bảng cuối cùng trước khi in kết quả
    with lock:
        display_hotel_status(hotel, nurses, room_flood_status, flood_status, "Final", roof_patient_count)

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