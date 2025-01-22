# data set: https://noaa-ghcn-pds.s3.amazonaws.com/index.html#csv/by_year/


# 1. Tìm trạm quan trắc có số ngày tuyết rơi cao nhất. 
# Liệt kê danh sách các trạm quan trắc theo thứ tự từ số ngày tuyết rơi nhiều đến thấp nhất.
 
# import dask.dataframe as dd

# # Đọc dữ liệu từ file CSV
# df = dd.read_csv('2024.csv', dtype={'Q_FLAG': 'object'})

# # Lọc dữ liệu để chỉ lấy các dòng có yếu tố là tuyết (giả sử 'ELEMENT' có giá trị 'SNOW' hoặc 'PRCP')
# snow_days = df[(df['ELEMENT'] == 'SNOW') & (df['DATA_VALUE'] > 0)]  # Chỉ tính những ngày có tuyết (DATA_VALUE > 0)

# # Nhóm theo trạm và đếm số ngày tuyết rơi
# snow_days_count = snow_days.groupby('ID')['DATE'].count().compute()

# # Sắp xếp các trạm theo số ngày tuyết rơi giảm dần
# sorted_snow_days = snow_days_count.sort_values(ascending=False)

# # In danh sách các trạm theo thứ tự từ số ngày tuyết rơi nhiều đến
# print(sorted_snow_days)




# 2. Tìm trạm quan trắc có số lượng thời tiết đa dạng nhất (số lượng element khác nhau nhiều nhất). 
# Liệt kê toàn bộ các loại thời tiết của trạm quan trắc đó.


import dask.dataframe as dd

# Read the CSV file
df = dd.read_csv('2024.csv', dtype={'Q_FLAG': 'object'})

# Group by station and count the number of unique weather elements
element_counts = df.groupby('ID')['ELEMENT'].nunique().compute()

# Find the station with the highest number of unique weather elements
most_diverse_station = element_counts.idxmax()

# Filter the dataframe for the most diverse station
most_diverse_station_data = df[df['ID'] == most_diverse_station].compute()

# List all the weather types for that station
weather_types = most_diverse_station_data['ELEMENT'].unique()

# Print the station ID and its weather types
print(f"Station with the most diverse weather elements: {most_diverse_station}")

print("Weather types:", weather_types)