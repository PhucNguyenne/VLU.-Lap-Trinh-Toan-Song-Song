import random
import time
import threading
import heapq

def generate_numbers_file(filename="numbers.txt", num_lines=25_000_000, max_value=25_000_000):
    """Tạo file chứa 25 triệu số ngẫu nhiên."""
    with open(filename, "w") as f:
        for _ in range(num_lines):
            f.write(f"{random.randint(1, max_value)}\n")

def quicksort(arr):
    """Quicksort tuần tự."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

def parallel_quicksort(arr, num_threads=4):
    """Quicksort song song sử dụng đa luồng."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    sorted_left = []
    sorted_right = []
    
    left_thread = threading.Thread(target=lambda: sorted_left.extend(quicksort(left)))
    right_thread = threading.Thread(target=lambda: sorted_right.extend(quicksort(right)))
    
    left_thread.start()
    right_thread.start()
    
    left_thread.join()
    right_thread.join()
    
    return sorted_left + middle + sorted_right

def merge_sorted_chunks(sorted_chunks):
    """Hợp nhất các khối dữ liệu đã sắp xếp với dữ liệu động."""
    return list(heapq.merge(*sorted_chunks))

def read_and_sort(filename="numbers.txt", chunk_size=1_000_000):
    """Đọc file theo từng khối và sắp xếp song song."""
    sorted_chunks = []
    with open(filename, "r") as f:
        while chunk := f.readlines(chunk_size):
            numbers = list(map(int, chunk))
            sorted_chunks.append(parallel_quicksort(numbers))
    
    sorted_numbers = merge_sorted_chunks(sorted_chunks)
    with open("sorted_numbers.txt", "w") as f:
        for num in sorted_numbers:
            f.write(f"{num}\n")

if __name__ == "__main__":
    start_time = time.time()
    print("Đang tạo file...")
    generate_thread = threading.Thread(target=generate_numbers_file)
    generate_thread.start()
    generate_thread.join()
    print("Đã tạo xong file numbers.txt")
    end_time = time.time()
    print(f"Tổng thời gian tạo file: {end_time - start_time:.2f} giây")
    
    print("Bắt đầu sắp xếp...")
    sort_start_time = time.time()
    read_and_sort()
    sort_end_time = time.time()
    print(f"Tổng thời gian sắp xếp: {sort_end_time - sort_start_time:.2f} giây")
