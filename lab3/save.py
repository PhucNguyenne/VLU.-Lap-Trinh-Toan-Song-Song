import multiprocessing
import random
import time

# Hàm quản lý từng tầng
def floor_process(floor_id, num_rooms, x_time, hotel, nurses, room_flood_status, 
                  flood_status, roof_patient_count):
    while not flood_status[floor_id]:
        current_nurses = nurses[floor_id]
        for _ in range(current_nurses):
            # Bắt đầu từ phòng gần cầu thang (M-1)
            for room in range(num_rooms - 1, -1, -1):
                if not room_flood_status[floor_id][room] and hotel[floor_id][room] > 0:
                    patients_to_move = min(2, hotel[floor_id][room])
                    hotel[floor_id][room] -= patients_to_move
                    if floor_id < len(hotel) - 1:
                        hotel[floor_id + 1][num_rooms - 1] += patients_to_move  # Đưa lên cầu thang tầng trên
                    else:
                        with roof_patient_count.get_lock():
                            roof_patient_count.value += patients_to_move
                    break  # Sau khi cứu, chuyển sang y tá tiếp theo

        # Giảm độ trễ tối đa
        time.sleep(x_time / 10)

    nurses[floor_id] = 0  # Tầng ngập, y tá "chết"

# Hàm quản lý lũ lụt
def flood_controller(num_floors, num_rooms, x_time, room_flood_status, flood_status):
    current_floor = 0
    current_room = 0
    while current_floor < num_floors:
        room_flood_status[current_floor][current_room] = True
        if all(room_flood_status[current_floor]):
            flood_status[current_floor] = True
            if current_floor + 1 < num_floors:
                flood_status[current_floor + 1] = True
            current_floor += 1
            current_room = 0
        else:
            current_room += 1
        time.sleep(3 * x_time)

# Hàm chính
def main():
    # Tham số
    N = 5  # Số tầng
    M = 8  # Số phòng mỗi tầng
    X = 0.5  # Đơn vị thời gian X

    # Khởi tạo dữ liệu dùng Manager
    manager = multiprocessing.Manager()
    hotel = manager.list()
    for _ in range(N):
        floor = manager.list()
        remaining = M * 3
        for _ in range(M - 1):
            patients = random.randint(0, min(10, remaining))
            floor.append(patients)
            remaining -= patients
        floor.append(remaining)
        hotel.append(floor)

    nurses = manager.list([M // 4 for _ in range(N)])  # 4 y tá mỗi tầng
    initial_nurses = sum(nurses)
    room_flood_status = manager.list([manager.list([False] * M) for _ in range(N)])
    flood_status = manager.list([False] * N)
    flood_status[0] = True
    roof_patient_count = multiprocessing.Value('i', 0)

    total_patients = sum(sum(floor) for floor in hotel)

    # Tạo tiến trình
    processes = [
        multiprocessing.Process(target=flood_controller, 
                              args=(N, M, X, room_flood_status, flood_status))
    ]
    processes.extend(multiprocessing.Process(target=floor_process, 
                                            args=(i, M, X, hotel, nurses, room_flood_status, 
                                                  flood_status, roof_patient_count)) 
                    for i in range(N))

    # Bắt đầu tiến trình
    for p in processes:
        p.start()

    # Chờ tất cả tiến trình hoàn thành
    for p in processes:
        p.join()

    # Tính kết quả
    dead_patients = sum(hotel[f][r] for f in range(N) for r in range(M) 
                        if room_flood_status[f][r])
    saved_patients = roof_patient_count.value
    remaining_nurses = sum(nurses[f] for f in range(N) if not flood_status[f])
    dead_nurses = initial_nurses - remaining_nurses
    efficiency = (saved_patients / total_patients) * 100 if total_patients > 0 else 0

    # In kết quả
    print(f"\nKết quả cuối cùng:")
    print(f"Tổng số bệnh nhân ban đầu: {total_patients}")
    print(f"Số bệnh nhân được cứu: {saved_patients}")
    print(f"Số bệnh nhân đã chết: {dead_patients}")
    print(f"Tổng số y tá ban đầu: {initial_nurses}")
    print(f"Số y tá còn lại: {remaining_nurses}")
    print(f"Số y tá đã chết: {dead_nurses}")
    print(f"Hiệu suất cứu bệnh nhân: {efficiency:.2f}%")

if __name__ == "__main__":
    main()