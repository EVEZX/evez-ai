import json
import queue
import threading
import time

class WorkflowOrchestrator:
    def __init__(self):
        self.state = {}
        self.task_queue = queue.Queue()
        self.lock = threading.Lock()
        self.is_running = True
        
    def load_state(self, state_file):
        try:
            with open(state_file, 'r') as file:
                self.state = json.load(file)
        except FileNotFoundError:
            self.state = {}

    def save_state(self, state_file):
        with open(state_file, 'w') as file:
            json.dump(self.state, file, indent=4)

    def add_task(self, task):
        self.task_queue.put(task)

    def process_tasks(self):
        while self.is_running:
            try:
                task = self.task_queue.get(timeout=1)
                self.execute_task(task)
                self.task_queue.task_done()
            except queue.Empty:
                continue

    def execute_task(self, task):
        print(f'Executing task: {task}')
        time.sleep(1)  # Simulating task execution
        self.lock.acquire()
        self.state[task] = "completed"
        self.lock.release()
        
    def stop(self):
        self.is_running = False

if __name__ == '__main__':
    orchestrator = WorkflowOrchestrator()
    orchestrator.load_state('state.json')
    thread = threading.Thread(target=orchestrator.process_tasks)
    thread.start()
    
    # Adding some tasks for the example
    orchestrator.add_task('Task 1')
    orchestrator.add_task('Task 2')

    time.sleep(5)  # Let the tasks run
    orchestrator.stop()
    orchestrator.save_state('state.json')
    thread.join()