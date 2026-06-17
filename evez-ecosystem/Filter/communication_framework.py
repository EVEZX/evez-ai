# Communication Framework

class Message:
    def __init__(self, content, sender, recipient):
        self.content = content
        self.sender = sender
        self.recipient = recipient
        self.timestamp = None

class MessageHandler:
    def __init__(self):
        self.channels = {}

    def add_channel(self, channel):
        self.channels[channel.name] = channel

    def route_message(self, message):
        channel = self.channels.get(message.recipient)
        if channel:
            channel.send_message(message)
        else:
            print(f"No channel found for {message.recipient}")

class Channel:
    def __init__(self, name):
        self.name = name

    def send_message(self, message):
        print(f"Sending message from {message.sender} to {self.name}: {message.content}")

# Example usage
if __name__ == '__main__':
    handler = MessageHandler()
    email_channel = Channel('Email')
    sms_channel = Channel('SMS')

    handler.add_channel(email_channel)
    handler.add_channel(sms_channel)

    msg = Message(content='Hello World!', sender='User1', recipient='Email')
    handler.route_message(msg)