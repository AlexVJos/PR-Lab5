import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "tasks_group",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "tasks_group",
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json[ 'type' ]

        if message_type == 'task_event':
            await self.channel_layer.group_send(
                "tasks_group",
                {
                    'type': 'task_event',
                    'action': text_data_json[ 'action' ],
                    'task': text_data_json[ 'task' ]
                }
            )

    async def task_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'task_event',
            'action': event[ 'action' ],
            'task': event[ 'task' ]
        }))
