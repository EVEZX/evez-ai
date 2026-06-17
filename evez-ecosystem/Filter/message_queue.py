class MessageQueue:
    def __init__(self):
        self.inbound_queue = []
        self.outbound_queue = []

    def add_inbound_message(self, message):
        self.inbound_queue.append(message)
        print(f"Inbound message added: {message}")

    def get_inbound_message(self):
        if self.inbound_queue:
            return self.inbound_queue.pop(0)
        return None

    def add_outbound_message(self, message):
        self.outbound_queue.append(message)
        print(f"Outbound message added: {message}")

    def get_outbound_message(self):
        if self.outbound_queue:
            return self.outbound_queue.pop(0)
        return None

    def process_messages(self):
        while self.inbound_queue:
            message = self.get_inbound_message()
            # Process the message here
            print(f"Processing inbound message: {message}")

        while self.outbound_queue:
            message = self.get_outbound_message()
            # Send the message here
            print(f"Sending outbound message: {message}")
