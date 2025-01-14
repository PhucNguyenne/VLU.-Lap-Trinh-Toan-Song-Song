import time
import dask.array as da
import numpy as np
from tqdm import tqdm

# Mảng numpy giả sử
array = np.arange(60)

# Tạo Dask array
dask_array = da.from_array(array, chunks=(15,))

# Lấy số lượng chunk
num_chunks = len(dask_array.chunks[0])

# Hàm xử lý
def inc(i):
    time.sleep(1)  # Mô phỏng công việc nặng
    chunk = dask_array[i].compute()  # Tính toán chunk thứ i
    return chunk + 1

# Danh sách kết quả
ls = []

# Vòng lặp với tqdm
for i in tqdm(range(num_chunks)):
    ls.append(inc(i))

# In kết quả
print(ls[:5])