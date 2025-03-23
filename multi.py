import os
import time
import threading
import multiprocessing
from queue import Queue
from multiprocessing import Manager

def search_in_file(file_path, keywords):
    """Шукає ключові слова у файлі та підраховує їх кількість."""
    found_words = {word: [] for word in keywords}
    word_counts = {word: 0 for word in keywords}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            for word in keywords:
                count = content.count(word)
                if count > 0:
                    found_words[word].append(file_path)
                    word_counts[word] = count
    except Exception as e:
        print(f"Помилка при обробці {file_path}: {e}")
    return found_words, word_counts


def thread_worker(files, keywords, results_queue, counts_queue):
    """Потоковий обробник файлів."""
    for file in files:
        result, counts = search_in_file(file, keywords)
        results_queue.put(result)
        counts_queue.put(counts)


def process_worker(files, keywords, results_dict, counts_dict):
    """Процесний обробник файлів."""
    for file in files:
        result, counts = search_in_file(file, keywords)
        for key, value in result.items():
            results_dict[key].extend(value)
        for key, value in counts.items():
            counts_dict[key] += value


def run_threading(files, keywords):
    """Запускає багатопотокову версію."""
    start_time = time.time()
    num_threads = len(files)
    results_queue = Queue()
    counts_queue = Queue()
    threads = []
    
    chunk_size = len(files) // num_threads if num_threads > 0 else 1
    for i in range(num_threads):
        chunk = files[i * chunk_size: (i + 1) * chunk_size] if i < num_threads - 1 else files[i * chunk_size:]
        thread = threading.Thread(target=thread_worker, args=(chunk, keywords, results_queue, counts_queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    final_results = {word: [] for word in keywords}
    final_counts = {word: 0 for word in keywords}
    while not results_queue.empty():
        partial_result = results_queue.get()
        for key, value in partial_result.items():
            final_results[key].extend(value)
    while not counts_queue.empty():
        partial_counts = counts_queue.get()
        for key, value in partial_counts.items():
            final_counts[key] += value
    
    print(f"Threading time: {time.time() - start_time:.2f} sec")
    return final_results, final_counts


def run_multiprocessing(files, keywords):
    """Запускає багатопроцесорну версію."""
    start_time = time.time()
    num_processes = len(files)
    manager = Manager()
    results_dict = manager.dict({word: [] for word in keywords})
    counts_dict = manager.dict({word: 0 for word in keywords})
    processes = []
    
    chunk_size = len(files) // num_processes if num_processes > 0 else 1
    for i in range(num_processes):
        chunk = files[i * chunk_size: (i + 1) * chunk_size] if i < num_processes - 1 else files[i * chunk_size:]
        process = multiprocessing.Process(target=process_worker, args=(chunk, keywords, results_dict, counts_dict))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()
    
    print(f"Multiprocessing time: {time.time() - start_time:.2f} sec")
    return dict(results_dict), dict(counts_dict)


if __name__ == "__main__":
    folder_path = "text_files"  # Папка з файлами
    keywords = ["Python", "error", "thread", "process"]  # Ключові слова
    
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    print("Запуск багатопотокової версії")
    threading_results, threading_counts = run_threading(all_files, keywords)
    print("Результати:", threading_results)
    print("Підрахунок слів:", threading_counts)
    
    print("\nЗапуск багатопроцесорної версії")
    multiprocessing_results, multiprocessing_counts = run_multiprocessing(all_files, keywords)
    print("Результати:", multiprocessing_results)
    print("Підрахунок слів:", multiprocessing_counts)
