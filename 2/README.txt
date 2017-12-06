Запуск скрипта в формате:
python convert.py -i INPUT_FILE_PATH -o RES_FILE_PATH -a ALGORITHM
ALGORITHM = [thresh,rdith,odith,ediff1,ediff2,floyd-stein]
thresh - алгоритм порогового отсечения (с порогом 128)
rdith - случайный дизеринг
odith - упорядоченный дизеринг (матрица 16х16)
ediff1 - диффузия ошибки вперёд по строке
ediff2 - диффузия ошибки вперёд по строке для чётных строк и назад для нечётных
floyd-stein - диффузия ошибки по Флойду-Штейнбергу