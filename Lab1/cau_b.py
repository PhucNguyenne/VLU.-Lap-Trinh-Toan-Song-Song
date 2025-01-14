import numpy as np
import dask.array as da
import time

# Tạo một mảng NumPy ngẫu nhiên 1000000 phần tử (1 chiều)
numpy_array = np.random.random((1000000,))

# Tạo một mảng Dask từ mảng NumPy
x = da.from_array(numpy_array, chunks=(10000,))

# Hàm tính tổng tuần tự
def sum_sequential(array):
    total = 0
    for value in array:
        total += value
    return total

# Hàm tính tổng song song cho mảng Dask
def sum_parallel(dask_array):
    # Áp dụng np.sum trên mỗi chunk mà không dùng map_blocks
    total = dask_array.sum().compute()  # Sử dụng phương thức sum của Dask để tính tổng
    return total

# Phép toán tuần tự: Tính tổng mảng NumPy
start_time = time.time()
result_tt = sum_sequential(numpy_array)  # Tính tổng toàn bộ mảng
end_time = time.time()
print(f"Tổng tuần tự: {result_tt}")
print(f"Thời gian thực thi tuần tự: {end_time - start_time} giây")

# Phép toán song song: Tính tổng mảng Dask
start_time = time.time()
result_ss = sum_parallel(x)  # Tính tổng song song
end_time = time.time()
print(f"Tổng song song: {result_ss}")
print(f"Thời gian thực thi song song: {end_time - start_time} giây")