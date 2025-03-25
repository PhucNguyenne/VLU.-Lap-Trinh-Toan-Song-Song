import threading

def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2

    left_half = []
    right_half = []

    def sort_left():
        nonlocal left_half
        left_half = merge_sort(arr[:mid])

    def sort_right():
        nonlocal right_half
        right_half = merge_sort(arr[mid:])

    t1 = threading.Thread(target=sort_left)
    t2 = threading.Thread(target=sort_right)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return merge(left_half, right_half)

def merge(left, right):
    sorted_arr = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            sorted_arr.append(left[i])
            i += 1
        else:
            sorted_arr.append(right[j])
            j += 1

    sorted_arr.extend(left[i:])
    sorted_arr.extend(right[j:])

    return sorted_arr

if __name__ == "__main__":
    import time
    import numpy as np

    arr = np.random.randint(0, 100, 5000).tolist()
    
    start = time.time()
    sorted_arr = merge_sort(arr)
    print(f"Thời gian chạy: {time.time() - start} giây")
