import time
import multiprocessing
from threading import Thread

def cpu_bound_workload():
    total = 0
    for i in range(30_000_000):
        total += i
    return total

def benchmark_single_thread():
    start = time.time()
    cpu_bound_workload()
    cpu_bound_workload()
    return time.time() - start

def benchmark_two_threads():
    t1 = Thread(target=cpu_bound_workload)
    t2 = Thread(target=cpu_bound_workload)
    start = time.time()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    return time.time() - start

def benchmark_two_processes():
    p1 = multiprocessing.Process(target=cpu_bound_workload)
    p2 = multiprocessing.Process(target=cpu_bound_workload)
    start = time.time()
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    return time.time() - start

if __name__ == "__main__":
    print("--- GIL Benchmark Testi Başlıyor ---")
    t_single = benchmark_single_thread()
    print(f"1 Thread (Baseline): {t_single:.2f} sn")
    t_threads = benchmark_two_threads()
    print(f"2 Thread (GIL Kilitliyor): {t_threads:.2f} sn")
    t_processes = benchmark_two_processes()
    print(f"2 Process (Çözüm): {t_processes:.2f} sn")