import multiprocessing
import random
import time
from tabulate import tabulate

def display_hotel_status(hotel, nurses, room_flood_status, flood_status, roof_patient_count, time_step):
    if hotel is None or nurses is None or room_flood_status is None or flood_status is None:
        return
    
    print(f"\nThời gian: {time_step}")
    headers = ["Phòng"] + [f"P{i+1}" for i in range(max(len(floor) for floor in hotel))] + ["Y tá"]
    table = []
    for floor_id in range(len(hotel)):
        if floor_id == len(hotel) - 1:
            status = "Roof (Không ngập)"
            rooms = [f"{hotel[floor_id][0]}"]
        else:
            status = f"Tầng {floor_id + 1} ({'Ngập' if flood_status[floor_id] else 'Bình thường'})"
            rooms = [f"{hotel[floor_id][room]} ({'Ngập' if room_flood_status[floor_id][room] else 'Bình thường'})" 
                     for room in range(len(hotel[floor_id]))]
        row = [status] + rooms + [""] * (len(headers) - len(rooms) - 2) + [nurses[floor_id]]
        table.append(row)
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print(f"Bệnh nhân đã được cứu: {roof_patient_count.value}\n")

def floor_process(floor_id, num_rooms, x_time, hotel, nurses, room_flood_status, 
                  flood_status, roof_patient_count, progress_data, lock):
    time_step = 0
    while True:
        with lock:
            if all(flood_status[i] for i in range(len(hotel) - 1)):  # Tất cả tầng 1-4 ngập hết
                break
            if floor_id < len(hotel) - 1 and flood_status[floor_id]:  # Tầng hiện tại ngập
                for target_floor in range(len(hotel)):
                    if target_floor != floor_id and (target_floor == len(hotel) - 1 or not flood_status[target_floor]):
                        nurses[target_floor] += nurses[floor_id]
                        nurses[floor_id] = 0
                        break
                break

            current_nurses = nurses[floor_id]
            # Nếu tầng 1 còn người và chưa ngập hết, kéo y tá từ tầng trên xuống
            if floor_id > 0 and nurses[floor_id] > 0 and not flood_status[0] and any(hotel[0][r] > 0 and not room_flood_status[0][r] for r in range(num_rooms)):
                nurses[0] += 1
                nurses[floor_id] -= 1
                time.sleep(x_time / 10)  # Thời gian chuyển tầng xuống tầng 1
                current_nurses = nurses[floor_id]

            # Chỉ di chuyển y tá lên tầng trên nếu tầng hiện tại không còn người để cứu
            if current_nurses > 0 and not any(hotel[floor_id][r] > 0 and (floor_id == len(hotel) - 1 or not room_flood_status[floor_id][r]) for r in range(num_rooms if floor_id < len(hotel) - 1 else 1)):
                for target_floor in range(floor_id + 1, len(hotel)):
                    if target_floor == len(hotel) - 1 or not flood_status[target_floor]:
                        nurses[target_floor] += nurses[floor_id]
                        nurses[floor_id] = 0
                        time.sleep(x_time / 10)  # Thời gian chuyển tầng lên
                        break
            if nurses[floor_id] == 0:
                break
            current_nurses = nurses[floor_id]

            patients_moved = 0
            for nurse in range(current_nurses):
                for room in range(num_rooms if floor_id < len(hotel) - 1 else 1):
                    if (floor_id == len(hotel) - 1 or not room_flood_status[floor_id][room]) and hotel[floor_id][room] > 0:
                        patients_to_move = min(2, hotel[floor_id][room])
                        hotel[floor_id][room] -= patients_to_move
                        time.sleep(x_time / 10)  # Thời gian đi qua mỗi phòng

                        # Phòng cuối (P8 hoặc roof)
                        if room == (num_rooms - 1 if floor_id < len(hotel) - 1 else 0):
                            target_floor = floor_id + 1 if floor_id < len(hotel) - 1 else floor_id - 1
                            while target_floor >= 0 and target_floor < len(hotel) - 1 and flood_status[target_floor]:
                                target_floor += 1 if target_floor < floor_id else -1
                            if target_floor >= 0 and target_floor < len(hotel):
                                if target_floor == len(hotel) - 1:
                                    hotel[target_floor][0] += patients_to_move
                                    roof_patient_count.value += patients_to_move
                                else:
                                    hotel[target_floor][num_rooms - 1] += patients_to_move
                                time.sleep(x_time / 10)  # Thời gian chuyển tầng
                        else:  # Di chuyển trong tầng đến P8
                            if floor_id < len(hotel) - 1:
                                hotel[floor_id][num_rooms - 1] += patients_to_move
                        patients_moved += patients_to_move
                        break

        time.sleep(x_time / 50)  # Thời gian nghỉ giữa các bước
        time_step += 1
        with lock:
            progress_data.put((list(hotel), list(nurses), list(room_flood_status), 
                             list(flood_status), roof_patient_count, time_step))

    with lock:
        nurses[floor_id] = 0  # Y tá chết khi tầng ngập

def flood_controller(num_floors, num_rooms, x_time, room_flood_status, flood_status, progress_data, lock):
    current_floor = 0
    current_room = 0
    time_step = 0
    while current_floor < num_floors - 1:
        with lock:
            room_flood_status[current_floor][current_room] = True
            if all(room_flood_status[current_floor]):
                flood_status[current_floor] = True
                for room in range(num_rooms):
                    room_flood_status[current_floor][room] = True
                if current_floor + 1 < num_floors - 1:
                    flood_status[current_floor + 1] = True
                current_floor += 1
                current_room = 0
            else:
                current_room = (current_room + 1) % num_rooms
        time.sleep(x_time / 2)  # Thời gian ngập mỗi phòng
        time_step += 3
        with lock:
            progress_data.put((None, None, list(room_flood_status), list(flood_status), None, time_step))

def can_rescue_more(hotel, room_flood_status, flood_status, num_floors):
    all_floors_flooded = all(flood_status[i] for i in range(num_floors - 1))
    if all_floors_flooded:
        return False
    for floor_id in range(num_floors - 1):
        for room in range(len(hotel[floor_id])):
            if not room_flood_status[floor_id][room] and hotel[floor_id][room] > 0:
                return True
    return False

def main():
    N = 5
    M = 8
    X = 1
    manager = multiprocessing.Manager()
    
    hotel = manager.list()
    total_patients = M * 3 * (N - 1)  # 96 người
    remaining = total_patients
    for _ in range(N - 1):  # Tầng 1-4
        floor = manager.list()
        floor_patients = min(remaining, M * 3)
        remaining -= floor_patients
        for _ in range(M - 1):
            patients = random.randint(0, min(10, floor_patients))
            floor.append(patients)
            floor_patients -= patients
        floor.append(floor_patients)
        hotel.append(floor)
    hotel.append(manager.list([0]))  # Tầng roof
    
    nurses = manager.list([2, 2, 2, 2, 0])  # Tầng 1-4: 2 y tá, tầng roof: 0
    initial_nurses = sum(nurses)
    room_flood_status = manager.list([manager.list([False] * M) for _ in range(N - 1)])
    flood_status = manager.list([False] * (N - 1))
    flood_status[0] = True  # Tầng 1 bắt đầu ngập
    roof_patient_count = manager.Value('i', 0)
    total_patients = sum(sum(floor) for floor in hotel[:N-1])
    progress_data = manager.Queue()
    lock = multiprocessing.Lock()
    
    processes = [
        multiprocessing.Process(target=flood_controller, 
                              args=(N, M, X, room_flood_status, flood_status, progress_data, lock))
    ]
    processes.extend(multiprocessing.Process(target=floor_process, 
                                            args=(i, M, X, hotel, nurses, room_flood_status, 
                                                  flood_status, roof_patient_count, progress_data, lock)) 
                    for i in range(N))
    
    for p in processes:
        p.start()
    
    try:
        while any(p.is_alive() for p in processes):
            if not progress_data.empty():
                data = progress_data.get()
                display_hotel_status(*data)
                with lock:
                    if not can_rescue_more(hotel, room_flood_status, flood_status, N):
                        print("Không còn bệnh nhân nào để cứu hoặc tất cả tầng dưới roof đã ngập. Dừng chương trình.")
                        for p in processes:
                            p.terminate()
                        break
            time.sleep(0.01)  # Thời gian chờ trong main
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
    
    for p in processes:
        p.join()
    
    dead_patients = sum(hotel[f][r] for f in range(N-1) for r in range(M) if room_flood_status[f][r])
    saved_patients = roof_patient_count.value
    remaining_nurses = sum(nurses[f] for f in range(N))
    dead_nurses = initial_nurses - remaining_nurses
    efficiency = (saved_patients / total_patients) * 100 if total_patients > 0 else 0
    
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