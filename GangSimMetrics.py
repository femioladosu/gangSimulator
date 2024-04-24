import simpy
import random
from collections import deque

class GangScheduler:
    def __init__(self, env, num_processors, time_quantum):
        self.env = env
        self.num_processors = num_processors
        self.processors = [simpy.Resource(env, capacity=1) for _ in range(num_processors)]
        self.free_processors = list(range(num_processors))
        self.queue = deque()
        self.time_quantum = time_quantum
        self.processor_idle_time = [0] * num_processors  # Track idle time for each processor
        self.processor_busy_time = [0] * num_processors  # Track busy time for each processor (new)
        self.processor_last_free_time = [0] * num_processors

    def generate_gangs(self, num_gangs):
        for gang_id in range(1, num_gangs + 1):
            num_tasks = random.randint(1, 5)
            tasks = [(task_id, [(random.randint(1, 2), random.randint(0, 1)) for _ in range(random.randint(1, 2))])
                     for task_id in range(num_tasks)]
            self.queue.append((gang_id, tasks))
        print("Initial Gangs and Tasks:")
        self.print_gang_details()

    def manage_scheduling(self):
        while True:
            yield self.env.timeout(1)
            if self.queue and self.free_processors:
                gang_id, tasks = self.queue[0]
                if len(tasks) <= len(self.free_processors):
                    self.queue.popleft()
                    self.env.process(self.schedule_gang(gang_id, tasks))

    def schedule_gang(self, gang_id, tasks):
        allocated_processors = self.free_processors[:len(tasks)]
        self.free_processors = self.free_processors[len(tasks):]
        print(f"Scheduling Gang {gang_id} at time {self.env.now} with {len(tasks)} tasks:")
        for i, (task_id, bursts) in enumerate(tasks):
            processor_id = allocated_processors[i]
            print(f"  Task {task_id} of Gang {gang_id} is assigned to Processor {processor_id}.")
            # Calculate and update busy time for CPU cycles
            busy_time = sum(duration for duration, cycle_type in bursts if cycle_type == 0)
            self.processor_busy_time[processor_id] += busy_time
            self.update_processor_usage(processor_id, self.env.now)
        yield self.env.timeout(self.time_quantum)
        print(f"Gang {gang_id} released processors at time {self.env.now}")
        for processor_id in allocated_processors:
            self.processor_idle_time[processor_id] += self.env.now - self.processor_last_free_time[processor_id]
            self.processor_last_free_time[processor_id] = self.env.now
        self.free_processors.extend(allocated_processors)
        self.queue.append((gang_id, tasks))

    def update_processor_usage(self, processor_id, start_time):
        if self.processor_last_free_time[processor_id] < start_time:
            self.processor_idle_time[processor_id] += start_time - self.processor_last_free_time[processor_id]
        self.processor_last_free_time[processor_id] = start_time + self.time_quantum

    def print_gang_details(self):
        for gang_id, tasks in self.queue:
            print(f"Gang {gang_id}:")
            for task_id, bursts in tasks:
                print(f"  Task {task_id}: Bursts -> {bursts}")

    def print_processor_times(self):
        for i, (idle_time, busy_time) in enumerate(zip(self.processor_idle_time, self.processor_busy_time)):
            print(f"Processor {i}: Idle time: {idle_time}, Busy time: {busy_time}")

# Setup
env = simpy.Environment()
num_processors = 20  # Total number of processors
scheduler = GangScheduler(env, num_processors, time_quantum=5)

# Generate gangs with random tasks
scheduler.generate_gangs(8)

# Start the scheduling management process
env.process(scheduler.manage_scheduling())

# Run the simulation
env.run(until=50)

# Print times
scheduler.print_processor_times()
